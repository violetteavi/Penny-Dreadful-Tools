"""The #64 exploration: archetype geometry in a nearest-deck model's space (Scenarios.md, "Archetype geometry"; 20261016_Archetype_Geometry_Architecture.pdf).

For each run it refits the stored model (store.load_model, which checks the stored fingerprints), reads its space off it (build_model_space), and
applies the geometry functions: centroids, typical lists and cohesion; defining cards against all rows and against siblings, and centroid pushes;
separation, overlap and where parent-labelled rows sit; strategy and combo analogies. It composes existing functions only. Nothing is tuned.

It writes a summary into docs/experiments/, and the full tables (CSV) and figure data (.npz) into --out, for the results PDF.

    uv run --group archetypes python -m archetype_classifier.experiments.archetype_geometry --runs 17 14 --date 20261016 --pr 65 \\
        --out .context/reports/20261016_Archetype_Geometry_Results
"""
import argparse
import csv
import statistics
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import Snapshot, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.store import ModelRecord, identity_hash, load_guesses, load_model, load_model_record, load_run
from archetype_classifier.geometry.analogies import AnalogyScore, build_analogy_scores, build_pair_analogies, build_strategy_analogies
from archetype_classifier.geometry.centroids import MIN_ROWS, build_centroids, build_medoids
from archetype_classifier.geometry.contrasts import RowContrast
from archetype_classifier.geometry.faithfulness import build_tree_order
from archetype_classifier.geometry.shape import build_overlap, build_parent_positions, build_separation
from archetype_classifier.geometry.signatures import build_centroid_push, build_defining_cards
from archetype_classifier.geometry.space import DeckSpace, build_model_space, build_presence

OUT = Path(__file__).parents[1] / 'docs' / 'experiments'
DECK_URL = 'https://pennydreadfulmagic.com/decks/{}/'
EXISTING = 5  # Training decks under the cutoff for an archetype to count as existing on season 39 (#59).
TOP, NEGATIVE = 5, 3  # Defining cards and pushes shown per archetype; the most negative pushes shown.
CURATED = ('Orzhov Control', 'Orzhov Midrange', 'Mono Black Midrange', 'Mono Black Control',  # The analogy examples.
           'Izzet Control', 'Izzet Twin', 'Applejacks', 'Lumbertwin',
           'Izzet Tempo', 'Polymorph', 'Actual Twin', 'Temur Ascendancy',  # #59: the bag's solo wins...
           'Dimir Midrange', 'Equipment Aggro',  # ...and the average's.
           'Red Deck Wins', 'Azorius Control', 'Esper Control', 'Dimir Control', 'Burn', 'White Weenie',  # Common archetypes.
           'Aristocrats', 'Mono Black Aristocrats', 'Orzhov Aristocrats', 'Golgari Aristocrats', 'Abzan Aristocrats', 'Mardu Aristocrats',
           'Rakdos Aristocrats', 'Squirrel Aristocrats')  # A parent and its children.
COMBO_PAIRS = (('Applejacks', 'Lumbertwin'), ('Izzet Control', 'Izzet Twin'), ('Izzet Control', 'Izzet Ascension'), ('Izzet Control', 'Izzet Storm'),
               ('Izzet Tempo', 'Izzet Blitzkrieg'), ('Mono Blue Tempo', 'Mono Blue Dreadnought'), ('Dimir Control', 'Dimir Tendrils'),
               ('Grixis Control', 'Grixis Tendrils'), ('Sultai Midrange', 'Sultai Tendrils'), ('Jeskai Control', 'Jeskai Jeskai Ascendancy'),
               ('Jeskai Control', 'Jeskai Fake-Twin'), ('Boros Aggro', 'Boros Twin'), ('Naya Midrange', 'Naya Fake-Twin'))  # Agreed on #65.
NAMED_ANALOGIES = (('Orzhov Midrange', 'Orzhov Control', 'Mono Black Midrange', 'Mono Black Control'),
                   ('Applejacks', 'Lumbertwin', 'Izzet Control', 'Izzet Twin'), ('Izzet Control', 'Izzet Twin', 'Applejacks', 'Lumbertwin'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runs', type=int, nargs='+', required=True, help='stored runs of the embedding nearest deck, the first one in detail')
    parser.add_argument('--min-rows', type=int, default=MIN_ROWS, help=f'the fewest training rows for a centroid (default {MIN_ROWS})')
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the summary file name')
    parser.add_argument('--pr', type=int, action='append', default=[], help='a PR that produced the analysis (repeatable)')
    parser.add_argument('--out', type=Path, required=True, help='where the full tables and figure data go')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    edb = loader.experiments_db()
    results = []
    for run_id in args.runs:
        run = load_run(edb, run_id)
        _, state = load_model_record(edb, run.model_id)
        record, model = load_model(edb, run.model_id)
        space = build_model_space(model)
        del model
        snapshot = loader.load_snapshot(edb, record.snapshot_id, record.scheme_id)
        result = analyse(space, snapshot, load_guesses(edb, run_id), args.min_rows)
        result['provenance'] = provenance(run_id, run.model_id, record, state)
        write_tables(result, args.out / f'run{run_id}')
        results.append(result)
        print(f'run {run_id}: {len(result["centroids"].label_ids)} archetypes with centroids, {len(result["analogies"])} analogies', flush=True)
    path = OUT / f'{args.date}_archetype_geometry.md'
    path.write_text(summary(results, args.pr))
    print(path)


def provenance(run_id: int, model_id: int, record: ModelRecord, state: dict[str, Any]) -> dict[str, Any]:
    """What the stored records already say about the space: which run, which model, and its fingerprints."""
    return {'run': run_id, 'model': model_id, 'name': record.name, 'version': record.version, 'params': record.params, 'snapshot': record.snapshot_id,
            'scheme': record.scheme_id, 'identity hash': identity_hash(record), 'embedding hash': state.get('embedding_hash'),
            'card weights hash': (state.get('card_weights') or {}).get('card_weights_hash'), 'training decks': record.training_count,
            'training fingerprint': record.training_hash, 'training rows': state.get('training_rows')}


def analyse(space: DeckSpace, snapshot: Snapshot, guesses: dict[int, Any], min_rows: int) -> dict[str, Any]:
    tree = ArchetypeTree(snapshot.archetypes)
    names = {a.id: a.name for a in snapshot.archetypes.values()}
    centroids = build_centroids(space, min_rows)
    index = centroids.index()
    medoids = build_medoids(space, centroids)
    presence = build_presence(space)
    separation = {s.label_id: s for s in build_separation(centroids, tree)}
    overlap = build_overlap(space, centroids)
    defining: dict[tuple[int, RowContrast], list[Any]] = {(label, contrast): build_defining_cards(presence, space, tree, label, contrast)
                                                       for label in centroids.label_ids.tolist() for contrast in ('all', 'siblings')}
    pushes = {label: build_centroid_push(space, tree, label) for label in centroids.label_ids.tolist()}
    strategy = build_strategy_analogies(names, centroids)
    pairs, skipped_pairs = build_pair_analogies(COMBO_PAIRS, names, centroids)
    analogies = build_analogy_scores(centroids, [*strategy, *pairs])
    train_counts = Counter(d.label_id for d in build_deck_set(snapshot, frozenset({Split.TRAIN})).decks.values())
    validation = [d for d in build_deck_set(snapshot, frozenset({Split.VALIDATION})).decks.values() if train_counts.get(d.label_id, 0) >= EXISTING]
    top_1: dict[int, list[bool]] = {}
    for d in validation:
        if d.deck_id in guesses and d.label_id is not None:
            top_1.setdefault(d.label_id, []).append(guesses[d.deck_id].guess_id == d.label_id)
    curated = [label for label in (next((i for i, n in names.items() if n == name), None) for name in CURATED) if label is not None and label in index]
    rows = np.flatnonzero(np.isin(space.rows.labels, curated))
    return {'space': space, 'tree': tree, 'names': names, 'centroids': centroids, 'medoids': medoids, 'separation': separation, 'overlap': overlap,
            'defining': defining, 'pushes': pushes, 'positions': build_parent_positions(space, centroids, tree), 'analogies': analogies,
            'skipped_pairs': skipped_pairs, 'top_1': top_1, 'curated': curated, 'missing_curated': [n for n in CURATED if n not in {names[c] for c in curated}],
            'figure': {'label_ids': centroids.label_ids, 'unit': centroids.unit, 'tree_order': np.array(build_tree_order(tree, centroids.label_ids.tolist())),
                       'cohesion': centroids.cohesion, 'curated_rows': rows, 'curated_vectors': space.matrix[rows],
                       'curated_labels': space.rows.labels[rows], 'curated_deck_counts': space.rows.deck_counts[rows],
                       'curated_own_cosine': np.einsum('ij,ij->i', space.matrix[rows], centroids.unit[[index[int(label)] for label in space.rows.labels[rows]]])}}


def write_tables(result: dict[str, Any], prefix: Path) -> None:
    names, centroids, tree = result['names'], result['centroids'], result['tree']
    rows: list[list[Any]] = []
    for label in centroids.label_ids.tolist():
        s, o, a = result['separation'][label], result['overlap'][label], tree.archetypes[label]
        t1 = result['top_1'].get(label, [])
        rows.append([label, names[label], a.depth, names.get(a.parent_id, '') if a.parent_id else '', o.rows, int(centroids.weights[centroids.index()[label]]),
                     round(float(centroids.cohesion[centroids.index()[label]]), 4), result['space'].rows.newest_deck_ids[result['medoids'][label]],
                     names.get(s.nearest_id, ''), rounded(s.nearest_cosine), rounded(s.sibling_mean), rounded(s.other_mean), o.overlapping,
                     round(o.overlapping / o.rows, 4), '; '.join(f'{names[k]} {n}' for k, n in o.nearer.most_common(3)), len(t1), rounded(sum(t1) / len(t1)) if t1 else ''])
    write_csv(prefix.with_name(prefix.name + '_archetypes.csv'), ['label_id', 'archetype', 'depth', 'parent', 'rows', 'decks', 'cohesion', 'typical_list_deck_id',
              'nearest_centroid', 'nearest_cosine', 'sibling_mean_cosine', 'other_mean_cosine', 'overlapping_rows', 'overlap', 'nearer_centroids',
              'season_39_decks', 'season_39_top_1'], rows)
    write_csv(prefix.with_name(prefix.name + '_defining_cards.csv'), ['archetype', 'contrast', 'rank', 'card', 'rows_in', 'rows_out', 'log_odds', 'z'],
              [[names[label], contrast, rank, c.card, c.rows_in, c.rows_out, round(c.log_odds, 4), round(c.z, 4)]
               for (label, contrast), cards in result['defining'].items() for rank, c in enumerate(cards, 1)])
    write_csv(prefix.with_name(prefix.name + '_pushes.csv'), ['archetype', 'distance', 'rank', 'card', 'share_in', 'share_out', 'alignment', 'push'],
              [[names[label], round(p.distance, 4), rank, c.card, round(c.share_in, 5), round(c.share_out, 5), round(c.alignment, 4), round(c.push, 5)]
               for label, p in result['pushes'].items() if p is not None for rank, c in enumerate(p.cards[:TOP] + p.cards[-NEGATIVE:], 1)])
    write_csv(prefix.with_name(prefix.name + '_parent_positions.csv'), ['parent', 'rows', 'between children', 'one child', 'elsewhere', 'mean own cosine'],
              [[names[parent], len(ps), *(sum(p.position == k for p in ps) for k in ('between children', 'one child', 'elsewhere')),
                rounded(statistics.mean(p.own_cosine for p in ps if p.own_cosine is not None) if any(p.own_cosine is not None for p in ps) else None)]
               for parent, ps in group_positions(result['positions']).items()])
    write_csv(prefix.with_name(prefix.name + '_analogies.csv'), ['kind', 'a', 'a_star', 'b', 'b_star', 'rank_3cosadd', 'rank_3cosmul', 'rank_only_b', 'offset_cosine',
              'offset_percentile'], [[s.analogy.kind, *(names[x] for x in (s.analogy.a, s.analogy.a_star, s.analogy.b, s.analogy.b_star)), s.rank_add, s.rank_mul,
                                      s.rank_only_b, round(s.offset_cosine, 4), rounded(s.offset_percentile)] for s in result['analogies']])
    np.savez_compressed(prefix.with_name(prefix.name + '_figure.npz'), **result['figure'])


def summary(results: Sequence[dict[str, Any]], prs: Sequence[int]) -> str:
    first = results[0]
    names = first['names']
    lines = ['# Archetype geometry', '', f'#64 (Archetype geometry: typical lists, defining cards and analogies in the deck-vector space). PRs: '
             f'{", ".join(f"#{p}" for p in prs) or "none"}. Nothing is tuned. Full tables and figure data are next to the results PDF.', '', '## Provenance', '',
             '| | ' + ' | '.join(f'run {r["provenance"]["run"]}' for r in results) + ' |', '|---|' + '---|' * len(results)]
    for key in first['provenance']:
        lines.append(f'| {key} | ' + ' | '.join(f'`{r["provenance"][key]}`' for r in results) + ' |')
    lines += ['', '## Overview', '', '| | ' + ' | '.join(f'run {r["provenance"]["run"]}' for r in results) + ' |', '|---|' + '---|' * len(results)]
    for label, value in overview_rows(results):
        lines.append(f'| {label} | ' + ' | '.join(value(r) for r in results) + ' |')
    lines += ['', f'## Curated archetypes (run {first["provenance"]["run"]})', '', '| Archetype | Rows | Cohesion | Typical list | Nearest centroid | Overlap | '
              'Season 39 Top 1 |' + ''.join(f' Cohesion, run {r["provenance"]["run"]} |' for r in results[1:]), '|---|---|---|---|---|---|---|' + '---|' * (len(results) - 1)]
    for label in first['curated']:
        i, s, o = first['centroids'].index()[label], first['separation'][label], first['overlap'][label]
        t1 = first['top_1'].get(label, [])
        others = ''.join(f' {cohesion_of(r, label)} |' for r in results[1:])
        lines.append(f'| {names[label]} | {o.rows} | {first["centroids"].cohesion[i]:.4f} | [{first["space"].rows.newest_deck_ids[first["medoids"][label]]}]'
                     f'({DECK_URL.format(first["space"].rows.newest_deck_ids[first["medoids"][label]])}) | {names.get(s.nearest_id, "")} {rounded(s.nearest_cosine)} | '
                     f'{o.overlapping / o.rows:.2f} | {f"{sum(t1) / len(t1):.2f} ({len(t1)})" if t1 else "–"} |{others}')
    if first['missing_curated']:
        lines += ['', f'Curated archetypes without a centroid: {", ".join(first["missing_curated"])}.']
    lines += ['', f'## Defining cards and pushes (run {first["provenance"]["run"]})', '',
              f'Top {TOP} by z (log-odds in brackets) against all other rows and against siblings; the largest centroid pushes against siblings, and the most negative.', '']
    for label in first['curated']:
        push = first['pushes'][label]
        lines += [f'**{names[label]}**', '', f'- All rows: {cards_text(first["defining"][(label, "all")])}',
                  f'- Siblings: {cards_text(first["defining"][(label, "siblings")])}',
                  f'- Pushes: {"no siblings" if push is None else ", ".join(f"{c.card} {c.push:.4f}" for c in push.cards[:TOP])} '
                  f'{"" if push is None else "(of " + f"{push.distance:.4f}" + "; most negative: " + ", ".join(f"{c.card} {c.push:.4f}" for c in push.cards[-NEGATIVE:]) + ")"}', '']
    lines += ['## Named analogies', '', '| Analogy | ' + ' | '.join(f'run {r["provenance"]["run"]}: 3CosAdd / 3CosMul / only-b, offset (percentile)' for r in results) + ' |',
              '|---|' + '---|' * len(results)]
    for a, a_star, b, b_star in NAMED_ANALOGIES:
        lines.append(f'| {a} : {a_star} :: {b} : {b_star} | ' + ' | '.join(named_analogy(r, (a, a_star, b, b_star)) for r in results) + ' |')
    lines += ['', '## Parent-labelled rows', '', '| Parent | ' + ' | '.join(f'run {r["provenance"]["run"]}: between / one child / elsewhere' for r in results) + ' |',
              '|---|' + '---|' * len(results)]
    for parent in sorted(group_positions(first['positions']), key=lambda p: -len(group_positions(first['positions'])[p]))[:15]:
        lines.append(f'| {names[parent]} ({len(group_positions(first["positions"])[parent])} rows) | ' + ' | '.join(position_text(r, parent) for r in results) + ' |')
    return '\n'.join(lines) + '\n'


def overview_rows(results: Sequence[dict[str, Any]]) -> list[tuple[str, Any]]:
    def analogy_stat(kind: str, f: Any) -> Any:
        return lambda r: f([s for s in r['analogies'] if s.analogy.kind == kind])
    def median(values: list[float]) -> str:
        return f'{statistics.median(values):.3f}' if values else '–'
    def share(scores: list[AnalogyScore], test: Any) -> str:
        return f'{sum(map(test, scores)) / len(scores):.2f}' if scores else '–'
    return [('Archetypes with a centroid', lambda r: str(len(r['centroids'].label_ids))),
            ('Below the floor (rows)', lambda r: f'{len(r["centroids"].skipped)} ({sum(r["centroids"].skipped.values())})'),
            ('Median cohesion', lambda r: median(r['centroids'].cohesion.tolist())),
            ('Rows nearer another centroid', lambda r: f'{sum(o.overlapping for o in r["overlap"].values()) / sum(o.rows for o in r["overlap"].values()):.3f}'),
            ('Spearman: overlap vs season 39 Top 1 (archetypes with 10+ decks)', spearman_text),
            ('Parent-labelled rows: between / one child / elsewhere', lambda r: '/'.join(str(sum(p.position == k for p in r['positions'])) for k in ('between children', 'one child', 'elsewhere'))),
            *((f'{kind.capitalize()} analogies: count', analogy_stat(kind, lambda s: str(len(s)))) for kind in ('strategy', 'pair')),
            *((f'{kind.capitalize()} analogies: median offset cosine (median percentile)',
               analogy_stat(kind, lambda s: f'{median([x.offset_cosine for x in s])} ({median([x.offset_percentile for x in s if x.offset_percentile is not None])})'))
              for kind in ('strategy', 'pair')),
            *((f'{kind.capitalize()} analogies: share ranked 1 by 3CosAdd / 3CosMul / only-b',
               analogy_stat(kind, lambda s: '/'.join(share(s, lambda x, f=f: getattr(x, f) == 1) for f in ('rank_add', 'rank_mul', 'rank_only_b')))) for kind in ('strategy', 'pair')),
            *((f'{kind.capitalize()} analogies: share where the offset beats only-b (3CosMul rank < only-b rank)',
               analogy_stat(kind, lambda s: share(s, lambda x: x.rank_mul < x.rank_only_b))) for kind in ('strategy', 'pair'))]


def spearman_text(r: dict[str, Any]) -> str:
    pairs = [(o.overlapping / o.rows, sum(r['top_1'][label]) / len(r['top_1'][label])) for label, o in r['overlap'].items() if len(r['top_1'].get(label, [])) >= 10]
    if len(pairs) < 3:
        return '–'
    rho, p = stats.spearmanr(*zip(*pairs, strict=True))
    return f'{rho:.2f} (p = {p:.3f}, {len(pairs)} archetypes)'


def named_analogy(r: dict[str, Any], names: tuple[str, str, str, str]) -> str:
    ids = {v: k for k, v in r['names'].items()}
    wanted = tuple(ids.get(n) for n in names)
    for s in r['analogies']:
        if (s.analogy.a, s.analogy.a_star, s.analogy.b, s.analogy.b_star) == wanted:
            return f'{s.rank_add} / {s.rank_mul} / {s.rank_only_b}, {s.offset_cosine:.3f} ({rounded(s.offset_percentile)})'
    return 'not built'


def position_text(r: dict[str, Any], parent: int) -> str:
    ps = group_positions(r['positions']).get(parent, [])
    return '/'.join(str(sum(p.position == k for p in ps)) for k in ('between children', 'one child', 'elsewhere')) if ps else '–'


def group_positions(positions: Sequence[Any]) -> dict[int, list[Any]]:
    grouped: dict[int, list[Any]] = {}
    for p in positions:
        grouped.setdefault(p.parent_id, []).append(p)
    return grouped


def cohesion_of(r: dict[str, Any], label: int) -> str:
    index = r['centroids'].index()
    return f'{r["centroids"].cohesion[index[label]]:.4f}' if label in index else '–'


def cards_text(cards: Sequence[Any]) -> str:
    return ', '.join(f'{c.card} {c.z:.1f} ({c.log_odds:.2f})' for c in cards) or 'none'


def rounded(value: float | None) -> float | str:
    return '' if value is None else round(value, 4)


def write_csv(path: Path, header: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    with path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == '__main__':
    main()
