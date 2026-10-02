"""Experiment reports: one stored run turned into Markdown, committed in docs/experiments/. Scores are recomputed from the run's stored guesses every time (decision F)."""
from collections.abc import Sequence

from archetype_classifier.data_loading import loader
from archetype_classifier.evaluation.metrics import METRICS_VERSION
from archetype_classifier.evaluation.rows import ROWS_VERSION
from archetype_classifier.evaluation.store import canonical, load_model_record, load_run, splits_text
from shared.database import Database


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
    return '\n'.join(lines) + '\n'
