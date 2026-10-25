"""The #62 Stage 1 run: deck diffs (20261024_Deck_Diffs_Architecture.pdf).

Every pair is a deck D against a training row T, whose label is the target archetype. D is a season 39 deck of an existing archetype (scored against
its snapshot label) or, for the coverage set, a training row. The pairs:
- (a) each season 39 deck against its run 17 match and its run 16 match;
- (b) against its true archetype's typical list, and against a wrong guess's typical list (typical lists in run 17's space);
- (c) coverage: the season 39 decks and 2,000 drawn training rows, each against one drawn row per pair class and its 5 near rivals under run 17.

Each pair is measured in runs 17, 14 and 16, one space at a time: cosine, net shift and shifts as agreed on #62 (10-21). Card specificity and the
case-study card contributions come from run 17. It composes tested functions only; nothing is tuned.

It writes pairs.csv, cards.csv and timings.json into --out, and a summary into docs/experiments/.

    uv run --group archetypes python -m archetype_classifier.experiments.deck_diffs --date 20261025 --out .context/reports/20261025_Deck_Diffs_Results
"""
import argparse
import csv
import json
import resource
import statistics
import time
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.data_loading.slices import Snapshot, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import Model, Prediction
from archetype_classifier.evaluation.store import identity_hash, load_guesses, load_model, load_model_record, load_run
from archetype_classifier.geometry.centroids import Centroids, build_centroids, build_medoids, build_shares, build_spread
from archetype_classifier.geometry.contrasts import (
    Neighbour,
    NeighbourContrast,
    build_blended_contrast,
    build_global_contrast,
    build_neighbour_contrasts,
    build_span_neighbours,
)
from archetype_classifier.geometry.diffs import (
    Axis,
    DeckDiff,
    Shift,
    build_agreement,
    build_axis,
    build_contributions,
    build_deck_diff,
    build_net_shift,
    build_share_axis,
    build_shift,
)
from archetype_classifier.geometry.pairs import PairClass, build_coverage_rows, build_match_row, build_near_rivals
from archetype_classifier.geometry.signatures import build_push
from archetype_classifier.geometry.space import DeckSpace, PlacedDecks, build_model_space, build_placed_decks, build_presence
from archetype_classifier.geometry.specificity import build_label_concentration
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck

OUT = Path(__file__).parents[1] / 'docs' / 'experiments'
AVERAGE, UNWEIGHTED, BAG = 17, 14, 16
EXISTING = 5  # Training decks under the cutoff for an archetype to count as existing on season 39 (#59).
ANCHOR_ROWS, ANCHOR_SEED, DRAW_SEED = 2000, 0, 1
CHUNK = 1000  # Anchors compared with every training row at once.
SIGNATURE = 10  # A target archetype's blended signature cards: the top of its blended push.
CASE_STUDIES = {270580: 'Izzet Twin miss', 269557: 'Temur Ascendancy miss', 270765: 'Squirrel Aristocrats miss', 270471: 'only the bag right',
                269637: 'only the average right'}  # Picked by the median net shift against run 17's match (20261024 spec).


@dataclass
class Pair:
    pair_id: int
    kind: str  # 'match 17', 'match 16', 'typical, true', 'typical, guessed' or 'coverage'.
    anchor: str  # 'season 39' or 'training'.
    pair_class: str
    deck_id: int | None  # D, a season 39 deck...
    anchor_row: int | None  # ...or a training row.
    deck_label: int
    row: int  # T.
    row_label: int
    guessed_by: str = ''  # For a guessed typical list: '17', '16' or '17 16'.
    measures: dict[str, Any] = field(default_factory=dict)

    @property
    def group(self) -> str:
        """What the report groups by: the coverage class with its anchor, or the set with whether T's label is D's."""
        if self.kind == 'coverage':
            return f'coverage, {self.anchor}, {self.pair_class}'
        return f'{self.kind}, {"right" if self.pair_class == PairClass.SAME.value else "wrong"}'


@dataclass(frozen=True)
class Geometry:
    centroids: Centroids
    index: dict[int, int]
    shares: np.ndarray
    neighbours: dict[int, list[Neighbour]]
    local: dict[int, NeighbourContrast]
    global_contrast: np.ndarray


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the summary file name')
    parser.add_argument('--pr', type=int, action='append', default=[], help='a PR that produced the analysis (repeatable)')
    parser.add_argument('--out', type=Path, required=True, help='where pairs.csv, cards.csv and timings.json go')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}
    edb = loader.experiments_db()

    clock = time.perf_counter()
    model, provenance_17 = refit(edb, AVERAGE)
    timings['run 17: refit'] = time.perf_counter() - clock
    record, _ = load_model_record(edb, load_run(edb, AVERAGE).model_id)
    snapshot = loader.load_snapshot(edb, record.snapshot_id, record.scheme_id)
    tree = ArchetypeTree(snapshot.archetypes)
    names = {a.id: a.name for a in snapshot.archetypes.values()}
    train_counts = Counter(d.label_id for d in build_deck_set(snapshot, frozenset({Split.TRAIN})).decks.values())
    decks = sorted((d for d in snapshot.decks.values() if d.split == Split.VALIDATION and d.label_id is not None and train_counts.get(d.label_id, 0) >= EXISTING),
                   key=lambda d: d.deck_id)
    contents = {i: c.maindeck for i, c in loader.load_contents([d.deck_id for d in decks]).items()}
    guesses = {run: load_guesses(edb, run) for run in (AVERAGE, BAG)}

    clock = time.perf_counter()
    space = build_model_space(model)
    geometry = build_geometry(space)
    medoids = build_medoids(space, geometry.centroids)
    timings['run 17: geometry'] = time.perf_counter() - clock
    rows = space.rows
    deck_labels = {d.deck_id: int(d.label_id) for d in decks if d.label_id is not None}

    clock = time.perf_counter()
    pairs, skipped = build_all_pairs(model, space, geometry, medoids, tree, deck_labels, contents, guesses)
    timings['pairs'] = time.perf_counter() - clock

    def maindeck_of_deck(p: Pair) -> tuple[CardCount, ...]:
        return contents[p.deck_id] if p.deck_id is not None else rows.maindecks[p.anchor_row]  # type: ignore[index]

    clock = time.perf_counter()
    presence = build_presence(space)
    concentration = dict(zip(presence.cards, build_label_concentration(presence, rows.labels).tolist(), strict=True))
    assert isinstance(model, EmbeddingNearestDeck) and model.card_weights is not None  # Run 17 weighs by IDF.
    idf = model.card_weights.weight
    diffs = {p.pair_id: build_deck_diff(rows.maindecks[p.row], maindeck_of_deck(p)) for p in pairs}
    for p in pairs:
        p.measures.update(specificity(diffs[p.pair_id], idf, concentration))
        p.measures.update(seasons(p, snapshot, rows.newest_deck_ids))
    timings['run 17: specificity'] = time.perf_counter() - clock

    clock = time.perf_counter()
    placed, position = place(model, pairs, contents, rows.maindecks)
    measure_average(space, geometry, placed, position, pairs)
    timings['run 17: measures'] = time.perf_counter() - clock
    cards = case_cards(space, geometry, placed, position, pairs, diffs, idf, concentration, names)
    neighbours_17 = geometry.neighbours
    row_identity = (rows.labels.copy(), rows.newest_deck_ids.copy())
    del model, space, geometry, placed, presence

    clock = time.perf_counter()
    model, provenance_14 = refit(edb, UNWEIGHTED)
    timings['run 14: refit'] = time.perf_counter() - clock
    clock = time.perf_counter()
    space = build_model_space(model)
    check_rows(space, row_identity, UNWEIGHTED)
    geometry = build_geometry(space)
    placed, position = place(model, pairs, contents, rows.maindecks)
    measure_other(space, geometry, placed, position, pairs, 'r14')
    timings['run 14: geometry and measures'] = time.perf_counter() - clock
    del model, space, geometry, placed

    clock = time.perf_counter()
    model, provenance_16 = refit(edb, BAG)
    timings['run 16: refit'] = time.perf_counter() - clock
    clock = time.perf_counter()
    space = build_model_space(model)
    check_rows(space, row_identity, BAG)
    geometry = build_geometry(space)
    placed, position = place(model, pairs, contents, rows.maindecks)
    measure_other(space, geometry, placed, position, pairs, 'r16', on_axis=True)
    borrowed = build_neighbour_contrasts(geometry.centroids, geometry.shares, neighbours_17)  # The bag with run 17's span neighbours.
    measure_other(space, geometry, placed, position, pairs, 'bag_n17', local=borrowed)
    timings['run 16: geometry and measures'] = time.perf_counter() - clock
    del model, space, geometry, placed

    timings['peak memory, MB'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    write_pairs(args.out / 'pairs.csv', pairs, names, rows.newest_deck_ids)
    write_csv(args.out / 'cards.csv', ['pair_id', 'role', 'axis', 'card', 'copies_target', 'copies_deck', 'contribution', 'idf', 'label_concentration', 'unseen',
                                       'signature'], cards)
    (args.out / 'timings.json').write_text(json.dumps(timings, indent=1))
    provenance = {AVERAGE: provenance_17, UNWEIGHTED: provenance_14, BAG: provenance_16}
    path = OUT / f'{args.date}_deck_diffs.md'
    path.write_text(summary(pairs, skipped, provenance, timings, args.pr))
    print(path)


def refit(edb: Any, run_id: int) -> tuple[Model, dict[str, Any]]:
    run = load_run(edb, run_id)
    record, state = load_model_record(edb, run.model_id)
    _, model = load_model(edb, run.model_id)
    weights: Any = state.get('card_weights') or {}
    return model, {'run': run_id, 'model': run.model_id, 'name': record.name, 'params': record.params, 'snapshot': record.snapshot_id,
                   'scheme': record.scheme_id, 'identity hash': identity_hash(record), 'embedding hash': state.get('embedding_hash'),
                   'card weights hash': weights.get('card_weights_hash'), 'training fingerprint': record.training_hash}


def build_geometry(space: DeckSpace) -> Geometry:
    centroids = build_centroids(space)
    shares = build_shares(space, centroids)
    neighbours = build_span_neighbours(centroids, build_spread(space, centroids))
    return Geometry(centroids, centroids.index(), shares, neighbours, build_neighbour_contrasts(centroids, shares, neighbours), build_global_contrast(shares))


def check_rows(space: DeckSpace, identity: tuple[np.ndarray, np.ndarray], run_id: int) -> None:
    """Every run trained on the same decks, so the rows (and the pairs' row numbers) must be the same."""
    if not (np.array_equal(space.rows.labels, identity[0]) and np.array_equal(space.rows.newest_deck_ids, identity[1])):
        raise ValueError(f"Run {run_id}'s training rows differ from run 17's")


def build_all_pairs(model: Model, space: DeckSpace, geometry: Geometry, medoids: dict[int, int], tree: ArchetypeTree, deck_labels: dict[int, int],
                    contents: dict[int, tuple[CardCount, ...]], guesses: dict[int, dict[int, Prediction]]) -> tuple[list[Pair], Counter[str]]:
    rows = space.rows
    pairs: list[Pair] = []
    skipped: Counter[str] = Counter()

    def add(kind: str, anchor: str, deck_id: int | None, anchor_row: int | None, deck_label: int, row: int, pair_class: str | None = None,
            guessed_by: str = '') -> None:
        same = PairClass.SAME.value if int(rows.labels[row]) == deck_label else 'other'
        pairs.append(Pair(len(pairs), kind, anchor, pair_class or same, deck_id, anchor_row, deck_label, row, int(rows.labels[row]), guessed_by))

    for deck_id, label in deck_labels.items():
        for run in (AVERAGE, BAG):
            guess = guesses[run].get(deck_id)
            if guess is None or guess.guess_id is None:
                skipped[f'match {run}: no guess'] += 1
                continue
            add(f'match {run}', 'season 39', deck_id, None, label, build_match_row(rows, int(guess.evidence['match_deck_id']), guess.guess_id))  # type: ignore[arg-type]
        if label in medoids:
            add('typical, true', 'season 39', deck_id, None, label, medoids[label])
        else:
            skipped['typical, true: under 10 rows'] += 1
        wrong: dict[int, list[str]] = {}
        for run in (AVERAGE, BAG):
            guess = guesses[run].get(deck_id)
            if guess is not None and guess.guess_id is not None and guess.guess_id != label:
                wrong.setdefault(guess.guess_id, []).append(str(run))
        for guess_id, runs in wrong.items():
            if guess_id in medoids:
                add('typical, guessed', 'season 39', deck_id, None, label, medoids[guess_id], guessed_by=' '.join(runs))
            else:
                skipped['typical, guessed: under 10 rows'] += 1

    eligible = frozenset(geometry.centroids.label_ids.tolist())
    candidates = np.flatnonzero(np.isin(rows.labels, list(eligible)))
    drawn_rows = np.random.default_rng(ANCHOR_SEED).choice(candidates, size=ANCHOR_ROWS, replace=False).tolist()
    anchors: list[tuple[str, int | None, int | None, int]] = [('season 39', deck_id, None, label) for deck_id, label in deck_labels.items()]
    anchors += [('training', None, int(r), int(rows.labels[r])) for r in drawn_rows]
    rng = np.random.default_rng(DRAW_SEED)
    for start in range(0, len(anchors), CHUNK):
        chunk = anchors[start:start + CHUNK]
        vectors = build_placed_decks(model, [contents[d] if d is not None else rows.maindecks[r] for _, d, r, _ in chunk]).matrix  # type: ignore[index]
        similarities = np.asarray(vectors @ space.matrix.T)
        for (anchor, anchor_deck, anchor_row, label), sims in zip(chunk, similarities, strict=True):
            for pair_class, drawn in build_coverage_rows(label, anchor_row, rows, tree, eligible, rng).items():
                if drawn is None:
                    skipped[f'coverage, {anchor}, {pair_class.value}: nothing to draw'] += 1
                else:
                    add('coverage', anchor, anchor_deck, anchor_row, label, drawn, pair_class.value)
            for row in build_near_rivals(sims, rows, label):
                add('coverage', anchor, anchor_deck, anchor_row, label, row, PairClass.NEAR_RIVAL.value)
    return pairs, skipped


def place(model: Model, pairs: Sequence[Pair], contents: dict[int, tuple[CardCount, ...]],
          maindecks: Sequence[tuple[CardCount, ...]]) -> tuple[PlacedDecks, dict[tuple[str, int], int]]:
    """Every D and T in the model's space, each distinct one once."""
    keys: dict[tuple[str, int], int] = {}
    for p in pairs:
        for key in (('deck', p.deck_id) if p.deck_id is not None else ('row', p.anchor_row), ('row', p.row)):
            keys.setdefault(key, len(keys))  # type: ignore[arg-type]
    placed = build_placed_decks(model, [contents[i] if kind == 'deck' else maindecks[i] for kind, i in keys])
    return placed, keys


def lines_of(placed: PlacedDecks, position: dict[tuple[str, int], int], p: Pair) -> tuple[np.ndarray, float, np.ndarray, float, np.ndarray, np.ndarray]:
    """D's and T's scaled lines, lengths and unit vectors."""
    d = position[('deck', p.deck_id) if p.deck_id is not None else ('row', p.anchor_row)]  # type: ignore[index]
    t = position[('row', p.row)]
    dense = (lambda m, i: np.asarray(m[i].toarray()).ravel()) if sparse.issparse(placed.matrix) else (lambda m, i: m[i])
    return (placed.lines[d].toarray().ravel(), float(placed.lengths[d]), placed.lines[t].toarray().ravel(), float(placed.lengths[t]),
            dense(placed.matrix, d), dense(placed.matrix, t))


def axes(space: DeckSpace, geometry: Geometry, local: dict[int, NeighbourContrast] | None = None) -> Callable[[int, str], Axis | None]:
    """Each target archetype's axes, built once: 'blended', 'local' and 'global' in the space, and 'share' (blended, over card shares)."""
    cache: dict[tuple[int, str], Axis | None] = {}
    contrasts = local if local is not None else geometry.local

    def axis(label: int, kind: str) -> Axis | None:
        if (label, kind) not in cache:
            mine = geometry.shares[geometry.index[label]]
            blended = build_blended_contrast(contrasts[label], geometry.global_contrast)
            if kind == 'share':
                cache[label, kind] = build_share_axis(mine, blended)
            elif kind == 'local':
                own = contrasts[label].local_contrast
                cache[label, kind] = None if own is None else build_axis(space, mine, own)
            else:
                cache[label, kind] = build_axis(space, mine, blended if kind == 'blended' else geometry.global_contrast)
        return cache[label, kind]
    return axis


def shift_measures(prefix: str, shift: Shift | None, on_axis: bool) -> dict[str, Any]:
    found: dict[str, float | None] = {f'{prefix}_raw': None if shift is None else shift.raw, f'{prefix}_fraction': None if shift is None else shift.fraction}
    if on_axis:
        found[f'{prefix}_on_axis'] = None if shift is None else shift.on_axis
    return found


def measure_average(space: DeckSpace, geometry: Geometry, placed: PlacedDecks, position: dict[tuple[str, int], int], pairs: Sequence[Pair]) -> None:
    axis = axes(space, geometry)
    for p in pairs:
        deck_lines, deck_length, target_lines, target_length, v_d, v_t = lines_of(placed, position, p)
        movement = float(np.linalg.norm(v_d - v_t))
        p.measures['r17_cosine'] = float(v_d @ v_t)
        p.measures['r17_net_shift'] = build_net_shift(space, deck_lines, deck_length, target_lines, target_length)
        label = int(space.rows.labels[p.row])
        known = label in geometry.index
        for kind in ('blended', 'local', 'global'):
            a = axis(label, kind) if known else None
            p.measures.update(shift_measures(f'r17_{kind}', None if a is None else build_shift(a, deck_lines, target_lines, movement), kind == 'blended'))
        share = axis(label, 'share') if known else None
        line_movement = float(np.linalg.norm(deck_lines - target_lines))
        p.measures.update(shift_measures('r17_share', None if share is None else build_shift(share, deck_lines, target_lines, line_movement), True))
        both = (p.measures['r17_blended_fraction'], p.measures['r17_share_fraction'])
        p.measures['r17_combined_fraction'] = None if None in both else (both[0] + both[1]) / 2


def measure_other(space: DeckSpace, geometry: Geometry, placed: PlacedDecks, position: dict[tuple[str, int], int], pairs: Sequence[Pair], prefix: str,
                  on_axis: bool = False, local: dict[int, NeighbourContrast] | None = None) -> None:
    """Run 14 or 16: cosine and net shift (unless borrowing neighbours, which changes neither) and the blended shift."""
    axis = axes(space, geometry, local)
    for p in pairs:
        deck_lines, deck_length, target_lines, target_length, v_d, v_t = lines_of(placed, position, p)
        if local is None:
            p.measures[f'{prefix}_cosine'] = float(v_d @ v_t)
            p.measures[f'{prefix}_net_shift'] = build_net_shift(space, deck_lines, deck_length, target_lines, target_length)
        label = int(space.rows.labels[p.row])
        a = axis(label, 'blended') if label in geometry.index else None
        shift = None if a is None else build_shift(a, deck_lines, target_lines, float(np.linalg.norm(v_d - v_t)))
        p.measures.update(shift_measures(f'{prefix}_blended', shift, on_axis))


def specificity(diff: DeckDiff, idf: Callable[[str], float], concentration: dict[str, float]) -> dict[str, Any]:
    def mean(lines: Sequence[CardCount], value: Callable[[str], float | None]) -> float | None:
        known = [(line.n, v) for line in lines if (v := value(line.card)) is not None]
        copies = sum(n for n, _ in known)
        return sum(n * v for n, v in known) / copies if copies else None
    return {'copies_kept': sum(line.n for line in diff.kept), 'copies_removed': sum(line.n for line in diff.removed),
            'copies_added': sum(line.n for line in diff.added), 'unseen_added': sum(line.n for line in diff.added if line.card not in concentration),
            'idf_added': mean(diff.added, idf), 'idf_removed': mean(diff.removed, idf),
            'concentration_added': mean(diff.added, concentration.get), 'concentration_removed': mean(diff.removed, concentration.get)}


def seasons(p: Pair, snapshot: Snapshot, newest: np.ndarray) -> dict[str, Any]:
    deck_season = snapshot.decks[p.deck_id if p.deck_id is not None else int(newest[p.anchor_row])].season_id  # type: ignore[index]
    row_season = snapshot.decks[int(newest[p.row])].season_id
    return {'deck_season': deck_season, 'row_season': row_season, 'season_gap': deck_season - row_season}


def case_cards(space: DeckSpace, geometry: Geometry, placed: PlacedDecks, position: dict[tuple[str, int], int], pairs: Sequence[Pair], diffs: dict[int, DeckDiff],
               idf: Callable[[str], float], concentration: dict[str, float], names: dict[int, str]) -> list[list[Any]]:
    """Card tables for the case studies' match and typical-list pairs, and for one coverage pair per anchor and class at its median shift."""
    wanted = {p.pair_id: 'case study' for p in pairs if p.deck_id in CASE_STUDIES and p.kind != 'coverage'}
    by_cell: dict[tuple[str, str], list[Pair]] = {}
    for p in pairs:
        if p.kind == 'coverage' and p.measures['r17_blended_fraction'] is not None:
            by_cell.setdefault((p.anchor, p.pair_class), []).append(p)
    for cell in by_cell.values():
        median = statistics.median(p.measures['r17_blended_fraction'] for p in cell)
        wanted.setdefault(min(cell, key=lambda p: (abs(p.measures['r17_blended_fraction'] - median), p.pair_id)).pair_id, 'hand-read')
    axis = axes(space, geometry)
    found: list[list[Any]] = []
    for p in pairs:
        if p.pair_id not in wanted:
            continue
        label = int(space.rows.labels[p.row])
        if label not in geometry.index:
            continue
        deck_lines, _, target_lines, _, _, _ = lines_of(placed, position, p)
        blended = build_blended_contrast(geometry.local[label], geometry.global_contrast)
        signature = {c.card for c in build_push(space, geometry.shares[geometry.index[label]], blended).cards[:SIGNATURE]}
        for kind in ('blended', 'share'):
            a = axis(label, kind)
            if a is None:
                continue
            contributions = build_contributions(a, space.cards, deck_lines, target_lines, diffs[p.pair_id])
            for c in contributions.cards:
                found.append([p.pair_id, wanted[p.pair_id], 'embedding' if kind == 'blended' else 'share', c.card, c.copies_target, c.copies_deck,
                              c.contribution, idf(c.card), concentration.get(c.card), c.card not in concentration, c.card in signature])
            found.append([p.pair_id, wanted[p.pair_id], 'embedding' if kind == 'blended' else 'share', '(rescaling: kept cards)', '', '',
                          contributions.rescaling, '', '', '', ''])
    return found


def write_pairs(path: Path, pairs: Sequence[Pair], names: dict[int, str], newest: np.ndarray) -> None:
    measures = list(pairs[0].measures) if pairs else []
    write_csv(path, ['pair_id', 'kind', 'anchor', 'pair_class', 'group', 'guessed_by', 'deck_id', 'anchor_row', 'deck_label', 'row', 'row_newest_deck',
                     'row_label', 'case_study', *measures],
              [[p.pair_id, p.kind, p.anchor, p.pair_class, p.group, p.guessed_by, p.deck_id, p.anchor_row, names[p.deck_label], p.row, int(newest[p.row]),
                names[p.row_label], CASE_STUDIES.get(p.deck_id or 0, ''), *(p.measures.get(m) for m in measures)] for p in pairs])


COMPARISONS = (('17 vs 14', 'r17_blended_fraction', 'r14_blended_fraction'), ('17 vs 16', 'r17_blended_fraction', 'r16_blended_fraction'),
               ('17 embedding vs 17 share', 'r17_blended_fraction', 'r17_share_fraction'),
               ('17 share vs bag, 17 neighbours', 'r17_share_fraction', 'bag_n17_blended_fraction'),
               ('bag, 17 neighbours vs bag, own', 'bag_n17_blended_fraction', 'r16_blended_fraction'))
MEDIANS = ('copies_removed', 'copies_added', 'unseen_added', 'season_gap', 'r17_cosine', 'r17_net_shift', 'r17_blended_fraction', 'r17_blended_on_axis',
           'r17_share_fraction', 'r17_share_on_axis', 'r14_net_shift', 'r16_net_shift', 'r16_blended_fraction')


def summary(pairs: Sequence[Pair], skipped: Counter[str], provenance: dict[int, dict[str, Any]], timings: dict[str, float], prs: Sequence[int]) -> str:
    groups: dict[str, list[Pair]] = {}
    for p in pairs:
        groups.setdefault(p.group, []).append(p)
    lines = ['# Deck diffs, Stage 1', '', f'#62 (Deck diffs: what the cards kept, removed and added between two decks look like). PRs: '
             f'{", ".join(f"#{p}" for p in prs) or "none"}. Nothing is tuned. pairs.csv and cards.csv are next to the results PDF.', '', '## Provenance', '',
             '| | ' + ' | '.join(f'run {r}' for r in provenance) + ' |', '|---|' + '---|' * len(provenance)]
    for key in provenance[AVERAGE]:
        lines.append(f'| {key} | ' + ' | '.join(f'`{v[key]}`' for v in provenance.values()) + ' |')
    lines += ['', '## Pairs', '', '| Group | Pairs |', '|---|---|', *(f'| {g} | {len(ps)} |' for g, ps in sorted(groups.items())), '',
              'Skipped: ' + (', '.join(f'{k} {n}' for k, n in sorted(skipped.items())) or 'none') + '.', '',
              '## Medians', '', '| Group | ' + ' | '.join(MEDIANS) + ' |', '|---|' + '---|' * len(MEDIANS)]
    for g, ps in sorted(groups.items()):
        lines.append(f'| {g} | ' + ' | '.join(median_text([p.measures.get(m) for p in ps]) for m in MEDIANS) + ' |')
    lines += ['', '## Across spaces', '', 'Sign agreement / Spearman / small-flip share (both |fraction| < 0.05), over pairs with both shifts.', '',
              '| Group | ' + ' | '.join(name for name, _, _ in COMPARISONS) + ' |', '|---|' + '---|' * len(COMPARISONS)]
    for g, ps in sorted(groups.items()):
        lines.append(f'| {g} | ' + ' | '.join(agreement_text(ps, first, second) for _, first, second in COMPARISONS) + ' |')
    lines += ['', '## Timings', '', '| Step | Seconds |', '|---|---|', *(f'| {k} | {v:.0f} |' for k, v in timings.items())]
    return '\n'.join(lines) + '\n'


def median_text(values: Sequence[Any]) -> str:
    present = [v for v in values if v is not None]
    return f'{statistics.median(present):.3g}' if present else '–'


def agreement_text(pairs: Sequence[Pair], first: str, second: str) -> str:
    a, b = [p.measures.get(first) for p in pairs], [p.measures.get(second) for p in pairs]
    if sum(x is not None and y is not None for x, y in zip(a, b, strict=True)) < 3:
        return '–'
    agreement = build_agreement(a, b)
    flips = '–' if agreement.small_flip_share is None else f'{agreement.small_flip_share:.2f}'
    return f'{agreement.sign_agreement:.2f} / {agreement.spearman:.2f} / {flips} ({agreement.pairs})'


def write_csv(path: Path, header: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    with path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == '__main__':
    main()
