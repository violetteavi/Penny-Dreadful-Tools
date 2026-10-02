"""Experiment reports: one stored run turned into Markdown, committed in docs/experiments/. Scores are recomputed from the run's stored guesses every time (decision F)."""
import math
from collections.abc import Mapping, Sequence

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.data_loading.slices import build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import METRICS_VERSION, ArchetypeTree, Confusion, Interval, ScoredDeck, in_tree, score
from archetype_classifier.evaluation.rows import PREFIXES, ROWS_VERSION, RowScores, build_rows, score_rows
from archetype_classifier.evaluation.store import canonical, load_guesses, load_model_record, load_run, splits_text
from shared.database import Database

DECK_URL = 'https://pennydreadfulmagic.com/decks/{}/'  # Local deck ids match the public site.
TOP_CONFUSIONS = 10
EXAMPLE_DECKS = 3


def render_report(edb: Database, run_id: int, min_decks: int, baseline_run_id: int | None = None, prs: Sequence[int] = (), include_test: bool = False) -> str:
    """The Markdown report for a stored run. It contains no time of its own, so the same run always gives the same report."""
    run = load_run(edb, run_id)
    record, _ = load_model_record(edb, run.model_id)
    scheme = loader.load_scheme(edb, record.scheme_id)
    lines = [
        f'# Run {run.id}: {record.name} v{record.version}',
        '',
        '| | |',
        '|---|---|',
        f'| Run | {run.id} |',
        f'| Made | {run.created_at:%Y-%m-%d %H:%M:%S} |',
        f'| Scope | {splits_text(run.scope).replace(",", ", ")} |',
        f'| Decks predicted | {run.deck_count} |',
        f'| Prediction hash | {run.prediction_hash} |',
        f'| Model | {run.model_id}: {record.name} v{record.version}, parameters {canonical(record.params)}, seed {record.seed} |',
        f'| Snapshot | {record.snapshot_id} |',
        f'| Scheme | {record.scheme_id} ({scheme.name}) |',
        f'| Trained on | {splits_text(record.training_splits).replace(",", ", ")} ({record.training_count} decks) |',
        f'| Tuned on | {splits_text(record.validation_splits).replace(",", ", ")} ({record.validation_count} decks) |',
        f'| Metrics version | {METRICS_VERSION} |',
        f'| Rows version | {ROWS_VERSION} |',
        f'| PRs | {", ".join(f"#{pr}" for pr in prs) or "none given"} |',
    ]
    snapshot = loader.load_snapshot(edb, record.snapshot_id, record.scheme_id)
    tree = ArchetypeTree(snapshot.archetypes)
    scored = build_deck_set(snapshot, run.scope, include_test=include_test)
    training = build_deck_set(snapshot, record.training_splits, include_test=Split.TEST in record.training_splits)
    rows = build_rows(scored, training, snapshot.scheme)
    results = score_rows(edb, run.id, tree, scored, rows, record.training_splits, record.validation_splits, min_decks, include_test)
    lines += ['', '## Results', '', '| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |', '|---|---|---|---|---|---|---|---|---|---|']
    lines += [result_line(name, r) for name, r in results.items()]
    guesses = load_guesses(edb, run.id)
    for split in (Split.TRAIN, Split.HELD_OUT, Split.VALIDATION, Split.TEST):
        widest = sorted({i for row in rows if split in row.splits and not row.name.endswith('unverified labels') for i in row.deck_ids} & set(guesses))
        decks = in_tree(tree, [ScoredDeck(i, scored.decks[i].label_id, guesses[i].guess_id, scored.decks[i].maindeck_hash) for i in widest])[0]  # type: ignore[arg-type]
        if decks:
            lines += confusion_lines(PREFIXES[split], decks, score(tree, decks, min_decks).confusions, snapshot.archetypes)
    return '\n'.join(lines) + '\n'

def confusion_lines(split_name: str, decks: list[ScoredDeck], confusions: list[Confusion], archetypes: Mapping[int, ArchetypeSnapshot]) -> list[str]:
    """The most common (label, guess) pairs a split's decks got wrong, by name, with links to up to three example decks."""
    lines = ['', f'### Top confusions: {split_name}', '', '| Label | Guess | Path | Decks | Example decks |', '|---|---|---|---|---|']
    for c in confusions[:TOP_CONFUSIONS]:
        examples = [d.deck_id for d in decks if (d.label_id, d.guess_id) == (c.label_id, c.guess_id)][:EXAMPLE_DECKS]
        links = ', '.join(f'[{i}]({DECK_URL.format(i)})' for i in examples)
        lines.append(f'| {name(c.label_id, archetypes)} | {name(c.guess_id, archetypes)} | {"on" if c.on_path else "off"} | {c.decks} | {links} |')
    return lines

def name(archetype_id: int | None, archetypes: Mapping[int, ArchetypeSnapshot]) -> str:
    if archetype_id is None:
        return 'no guess'
    return archetypes[archetype_id].name if archetype_id in archetypes else f'missing archetype {archetype_id}'

def result_line(name: str, r: RowScores) -> str:
    s = r.scores
    macro = f'{number(s.macro.hf)} ({s.macro_archetypes} archetypes)' if s.macro else '—'
    missing = ', '.join(f'missing archetype {i}' for i in sorted(s.missing_archetype_ids))
    notes = [note for note, applies in (('trained on', r.trained_on), ('tuned on', r.tuned_on), (f'{r.skipped} skipped: no stored guess', r.skipped > 0),
                                        (f'{s.skipped_decks} skipped: {missing}', s.skipped_decks > 0)) if applies]
    return (f'| {name} | {s.decks} | {s.maindecks} | {with_interval(s.micro.hf, s.micro_intervals.hf)} | {with_interval(s.micro.hp, s.micro_intervals.hp)} | '
            f'{with_interval(s.micro.hr, s.micro_intervals.hr)} | {number(s.exact_match_rate)} | {number(s.coverage)} | {macro} | {", ".join(notes)} |')

def with_interval(value: float | None, interval: Interval) -> str:
    return f'{number(value)} [{number(interval.low)}, {number(interval.high)}]'

def number(value: float | None) -> str:
    """Two decimals, or a dash for a value that's undefined (for example, precision with no guesses)."""
    return '—' if value is None or math.isnan(value) else f'{value:.2f}'
