"""Experiment reports: one stored run turned into Markdown, committed in docs/experiments/. Scores are recomputed from the run's stored guesses every time (decision F)."""
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.data_loading.slices import DeckSet, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import METRICS_VERSION, ArchetypeTree, Confusion, Interval, ScoredDeck, compare, in_tree, score
from archetype_classifier.evaluation.model import JSON, Prediction
from archetype_classifier.evaluation.rows import PREFIXES, ROWS_VERSION, Row, RowScores, build_rows, score_rows
from archetype_classifier.evaluation.store import canonical, load_guesses, load_model_record, load_run, splits_text
from shared.database import Database

DECK_URL = 'https://pennydreadfulmagic.com/decks/{}/'  # Local deck ids match the public site.
TOP_CONFUSIONS = 10
EXAMPLE_DECKS = 3


def render_report(edb: Database, run_id: int, min_decks: int, baseline_run_id: int | None = None, prs: Sequence[int] = (), include_test: bool = False) -> str:
    """The Markdown report for a stored run. It contains no time of its own, so the same run always gives the same report."""
    run = load_run(edb, run_id)
    record, state = load_model_record(edb, run.model_id)
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
    lines += curve_lines(state)
    guesses = load_guesses(edb, run.id)
    for split in (Split.TRAIN, Split.HELD_OUT, Split.VALIDATION, Split.TEST):
        widest = sorted({i for row in rows if split in row.splits and not row.name.endswith('unverified labels') for i in row.deck_ids} & set(guesses))
        decks = in_tree(tree, [ScoredDeck(i, scored.decks[i].label_id, guesses[i].guess_id, scored.decks[i].maindeck_hash) for i in widest])[0]  # type: ignore[arg-type]
        if decks:
            lines += confusion_lines(PREFIXES[split], decks, score(tree, decks, min_decks).confusions, snapshot.archetypes)
    if baseline_run_id is not None:
        lines += comparison_lines(run.id, baseline_run_id, rows, scored, guesses, load_guesses(edb, baseline_run_id), tree)
    return '\n'.join(lines) + '\n'

def curve_lines(state: Mapping[str, JSON]) -> list[str]:
    """The model's validation curve, if it keeps one in its state (as the Model protocol documents), with the chosen threshold marked."""
    lines = ['', '## Validation curve', '']
    curve = state.get('validation_curve')
    if not isinstance(curve, list) or not curve:
        return lines + ['No validation curve: this model has no threshold to tune.']
    lines += ['| Threshold | hP | hR | hF |', '|---|---|---|---|']
    for threshold, hp, hr, hf in cast(list[list[float]], curve):  # The documented shape: [threshold, hP, hR, hF] points.
        shown = f'**{threshold} (chosen)**' if threshold == state.get('threshold') else str(threshold)
        lines.append(f'| {shown} | {number(hp)} | {number(hr)} | {number(hf)} |')
    return lines

def comparison_lines(run_id: int, baseline_run_id: int, rows: Sequence[Row], scored: DeckSet, guesses: Mapping[int, Prediction],
                     baseline: Mapping[int, Prediction], tree: ArchetypeTree) -> list[str]:
    """This run minus the baseline, row by row, on the decks both guessed: each resample draws the same maindecks for both."""
    lines = ['', f'## Compared with run {baseline_run_id}', '', f'Run {run_id} minus run {baseline_run_id}, on the decks both runs guessed, with paired intervals.', '',
             '| Row | Decks compared | Left out | hF | hP | hR | Exact match |', '|---|---|---|---|---|---|---|']
    for row in rows:
        ours, theirs = scored_decks(row, scored, guesses, tree), scored_decks(row, scored, baseline, tree)
        if not {d.deck_id for d in ours} & {d.deck_id for d in theirs}:
            continue
        c = compare(tree, theirs, ours)
        d, i = c.difference, c.intervals
        lines.append(f'| {row.name} | {c.decks} | {c.left_out} | {with_interval(d.hf, i.hf)} | {with_interval(d.hp, i.hp)} | {with_interval(d.hr, i.hr)} | '
                     f'{with_interval(d.exact_match_rate, i.exact_match_rate)} |')
    return lines

def scored_decks(row: Row, scored: DeckSet, guesses: Mapping[int, Prediction], tree: ArchetypeTree) -> list[ScoredDeck]:
    return in_tree(tree, [ScoredDeck(i, scored.decks[i].label_id, guesses[i].guess_id, scored.decks[i].maindeck_hash)  # type: ignore[arg-type]
                          for i in sorted(row.deck_ids) if i in guesses])[0]

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
    if value is None or math.isnan(value):
        return '—'
    text = f'{value:.2f}'
    return '0.00' if text == '-0.00' else text  # A tiny negative difference shouldn't read as a direction.

def main() -> None:
    """Render a stored run's report and write it, usually into docs/experiments/."""
    import argparse
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('run_id', type=int)
    parser.add_argument('--baseline', type=int, help='a run to compare with, deck by deck')
    parser.add_argument('--pr', type=int, action='append', default=[], help='a PR that produced the run (repeatable)')
    parser.add_argument('--min-decks', type=int, required=True, help='the fewest decks an archetype needs to count in macro averages')
    parser.add_argument('--include-test', action='store_true', help='allow test-season results; logs a test look')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    markdown = render_report(loader.experiments_db(), args.run_id, args.min_decks, args.baseline, args.pr, args.include_test)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown)
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
