"""The database adapter: reads the site's databases and reads and writes the experiments database.

It holds no decisions of its own; those live in dataset.py, labels.py and splits.py.
"""
import json
from collections import Counter
from datetime import UTC, datetime
from collections.abc import Iterator, Sequence
from typing import Any

from archetype_classifier.data_loading.dataset import ArchetypeRow, ArchetypeSnapshot, Dataset, DatasetDeck, DeckCardRow, DeckRow, DeckSnapshot, Snapshot, snapshot_decks, split_decks
from archetype_classifier.data_loading.labels import LabelChange, Provenance
from archetype_classifier.data_loading.splits import Split, SplitScheme
from decksite.database import db
from shared.database import Database, get_database

EXPERIMENTS_DB = 'archetype_experiments'
DECK_CARD_CHUNK = 5000  # Deck ids per query when streaming deck_card (about 125,000 rows).
INSERT_BATCH = 1000

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS snapshot (
        id INT AUTO_INCREMENT PRIMARY KEY,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        latest_label_change DATETIME NULL,
        deck_count INT NOT NULL,
        max_deck_id INT NOT NULL,
        notes TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS archetype_snapshot (
        snapshot_id INT NOT NULL,
        archetype_id INT NOT NULL,
        name VARCHAR(190) NOT NULL,
        parent_id INT NULL,
        depth INT NOT NULL,
        PRIMARY KEY (snapshot_id, archetype_id),
        FOREIGN KEY (snapshot_id) REFERENCES snapshot (id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS deck_snapshot (
        snapshot_id INT NOT NULL,
        deck_id INT NOT NULL,
        season_id INT NOT NULL,
        archetype_id INT NOT NULL,
        provenance VARCHAR(20) NOT NULL,
        guess_archetype_id INT NULL,
        ground_truth BOOLEAN NOT NULL,
        maindeck_hash CHAR(40) NOT NULL,
        PRIMARY KEY (snapshot_id, deck_id),
        FOREIGN KEY (snapshot_id) REFERENCES snapshot (id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS split_scheme (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(190) NOT NULL UNIQUE,
        params JSON NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS deck_split (
        snapshot_id INT NOT NULL,
        scheme_id INT NOT NULL,
        deck_id INT NOT NULL,
        split VARCHAR(20) NOT NULL,
        unseen_maindeck_copies INT NOT NULL,
        PRIMARY KEY (snapshot_id, scheme_id, deck_id),
        FOREIGN KEY (snapshot_id, deck_id) REFERENCES deck_snapshot (snapshot_id, deck_id) ON DELETE CASCADE,
        FOREIGN KEY (scheme_id) REFERENCES split_scheme (id) ON DELETE CASCADE
    )""",
]


def experiments_db(name: str = EXPERIMENTS_DB) -> Database:
    return get_database(name)

def ensure_schema(edb: Database) -> None:
    for statement in SCHEMA:
        edb.execute(statement)

# Reading the site's databases

def load_decks() -> list[DeckRow]:
    sql = 'SELECT d.id, dc.season_id, s.name AS source, d.archetype_id FROM deck AS d INNER JOIN deck_cache AS dc ON dc.deck_id = d.id INNER JOIN source AS s ON s.id = d.source_id'
    return [DeckRow(r['id'], r['season_id'], r['source'], r['archetype_id']) for r in db().select(sql)]  # type: ignore[arg-type]

def load_label_history() -> list[LabelChange]:
    sql = 'SELECT deck_id, archetype_id, person_id IS NOT NULL AS by_person, changed_date FROM deck_archetype_change ORDER BY deck_id, changed_date, id'
    return [LabelChange(r['deck_id'], r['archetype_id'], bool(r['by_person']), datetime.fromtimestamp(r['changed_date'], UTC)) for r in db().select(sql)]  # type: ignore[arg-type]

def load_archetypes() -> list[ArchetypeRow]:
    sql = 'SELECT a.id, a.name, c.ancestor AS parent_id FROM archetype AS a LEFT JOIN archetype_closure AS c ON c.descendant = a.id AND c.depth = 1 ORDER BY a.id'
    return [ArchetypeRow(r['id'], r['name'], r['parent_id']) for r in db().select(sql)]  # type: ignore[arg-type]

def iter_deck_cards() -> Iterator[DeckCardRow]:
    """Every deck_card row, streamed a chunk of decks at a time so 6 million rows are never held at once."""
    max_id = db().value('SELECT MAX(deck_id) FROM deck_card', [], 0)
    for start in range(0, max_id + 1, DECK_CARD_CHUNK):
        rows = db().select('SELECT deck_id, card, n, sideboard FROM deck_card WHERE deck_id >= %s AND deck_id < %s', [start, start + DECK_CARD_CHUNK])
        for r in rows:
            yield DeckCardRow(r['deck_id'], r['card'], r['n'], bool(r['sideboard']))  # type: ignore[arg-type]

# Writing and reading the experiments database

def create_snapshot(edb: Database, notes: str = '') -> int:
    """Freeze the site's current labels and archetype tree. Returns the new snapshot's id."""
    ensure_schema(edb)
    snapshot = snapshot_decks(load_decks(), load_label_history(), iter_deck_cards(), load_archetypes())
    latest_change = db().value('SELECT FROM_UNIXTIME(MAX(changed_date)) FROM deck_archetype_change')
    max_deck_id = max(snapshot.decks, default=0)
    snapshot_id = edb.insert('INSERT INTO snapshot (latest_label_change, deck_count, max_deck_id, notes) VALUES (%s, %s, %s, %s)', [latest_change, len(snapshot.decks), max_deck_id, notes])
    insert_rows(edb, 'archetype_snapshot', ['snapshot_id', 'archetype_id', 'name', 'parent_id', 'depth'],
                [[snapshot_id, a.id, a.name, a.parent_id, a.depth] for a in snapshot.archetypes.values()])
    insert_rows(edb, 'deck_snapshot', ['snapshot_id', 'deck_id', 'season_id', 'archetype_id', 'provenance', 'guess_archetype_id', 'ground_truth', 'maindeck_hash'],
                [[snapshot_id, d.deck_id, d.season_id, d.archetype_id, d.provenance.value, d.guess_archetype_id, d.ground_truth, d.maindeck_hash] for d in snapshot.decks.values()])
    return snapshot_id

def create_scheme(edb: Database, scheme: SplitScheme) -> int:
    ensure_schema(edb)
    return edb.insert('INSERT INTO split_scheme (name, params) VALUES (%s, %s)', [scheme.name, json.dumps(scheme.to_params())])

def load_scheme(edb: Database, scheme_id: int) -> SplitScheme:
    row = edb.select('SELECT name, params FROM split_scheme WHERE id = %s', [scheme_id])[0]
    return SplitScheme.from_params(str(row['name']), json.loads(str(row['params'])))

def load_snapshot(edb: Database, snapshot_id: int) -> Snapshot:
    decks = {r['deck_id']: DeckSnapshot(r['deck_id'], r['season_id'], r['archetype_id'], Provenance(r['provenance']), r['guess_archetype_id'], bool(r['ground_truth']), r['maindeck_hash'])  # type: ignore[arg-type]
             for r in edb.select('SELECT * FROM deck_snapshot WHERE snapshot_id = %s', [snapshot_id])}
    return Snapshot(decks, load_archetype_snapshot(edb, snapshot_id))  # type: ignore[arg-type]

def load_archetype_snapshot(edb: Database, snapshot_id: int) -> dict[int, ArchetypeSnapshot]:
    return {r['archetype_id']: ArchetypeSnapshot(r['archetype_id'], r['name'], r['parent_id'], r['depth'])  # type: ignore[arg-type, misc]
            for r in edb.select('SELECT * FROM archetype_snapshot WHERE snapshot_id = %s', [snapshot_id])}

def materialise_split(edb: Database, snapshot_id: int, scheme_id: int) -> int:
    """Apply a scheme to a snapshot and store every deck's split. Returns the number of decks split."""
    splits = split_decks(load_snapshot(edb, snapshot_id), iter_deck_cards(), load_scheme(edb, scheme_id))
    insert_rows(edb, 'deck_split', ['snapshot_id', 'scheme_id', 'deck_id', 'split', 'unseen_maindeck_copies'],
                [[snapshot_id, scheme_id, s.deck_id, s.split.value, s.unseen_maindeck_copies] for s in splits.values()])
    return len(splits)

def load_dataset(edb: Database, snapshot_id: int, scheme_id: int) -> Dataset:
    sql = """
        SELECT ds.*, sp.split, sp.unseen_maindeck_copies
        FROM deck_snapshot AS ds
        INNER JOIN deck_split AS sp ON sp.snapshot_id = ds.snapshot_id AND sp.deck_id = ds.deck_id
        WHERE ds.snapshot_id = %s AND sp.scheme_id = %s
    """
    decks = {r['deck_id']: DatasetDeck(r['deck_id'], r['season_id'], r['archetype_id'], Provenance(r['provenance']), r['guess_archetype_id'],  # type: ignore[arg-type]
                                       bool(r['ground_truth']), r['maindeck_hash'], Split(r['split']), r['unseen_maindeck_copies'])  # type: ignore[arg-type]
             for r in edb.select(sql, [snapshot_id, scheme_id])}
    return Dataset(decks, load_archetype_snapshot(edb, snapshot_id))  # type: ignore[arg-type]

def summary(dataset: Dataset) -> dict[str, Counter[str]]:
    """Deck counts by split, by label source and by ground truth, for a quick look at a dataset."""
    decks = dataset.decks.values()
    return {
        'split': Counter(d.split.value for d in decks),
        'provenance': Counter(d.provenance.value for d in decks),
        'ground_truth_by_split': Counter(d.split.value for d in decks if d.ground_truth),
    }

def insert_rows(edb: Database, table: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    placeholders = '(' + ', '.join(['%s'] * len(columns)) + ')'
    for start in range(0, len(rows), INSERT_BATCH):
        batch = rows[start:start + INSERT_BATCH]
        sql = f'INSERT INTO {table} ({", ".join(columns)}) VALUES ' + ', '.join([placeholders] * len(batch))
        edb.execute(sql, [value for row in batch for value in row])

def main() -> None:
    """Create a snapshot, a scheme, or a split from the command line, and print a summary."""
    import argparse
    parser = argparse.ArgumentParser(description=main.__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('snapshot', help='freeze the current labels').add_argument('--notes', default='')
    commands.add_parser('scheme', help='store the default split scheme under a name').add_argument('name')
    for command in ('split', 'summary'):
        p = commands.add_parser(command, help='materialise a split' if command == 'split' else 'summarise a dataset')
        p.add_argument('snapshot_id', type=int)
        p.add_argument('scheme_id', type=int)
    args = parser.parse_args()
    edb = experiments_db()
    if args.command == 'snapshot':
        print(f'Created snapshot {create_snapshot(edb, args.notes)}')
    elif args.command == 'scheme':
        print(f'Created scheme {create_scheme(edb, SplitScheme(args.name))}')
    elif args.command == 'split':
        print(f'Split {materialise_split(edb, args.snapshot_id, args.scheme_id)} decks')
    else:
        for name, counts in summary(load_dataset(edb, args.snapshot_id, args.scheme_id)).items():
            print(name, dict(sorted(counts.items())))

if __name__ == '__main__':
    main()
