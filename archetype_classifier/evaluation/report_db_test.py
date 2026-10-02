"""Reports rendered from stored runs in a real experiments database."""
import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation.model import Prediction
from archetype_classifier.evaluation.report import render_report
from archetype_classifier.evaluation.store import ModelRecord, prediction_hash, save_model, save_run
from archetype_classifier.evaluation.store_db_test import BLUE, RED, store_snapshot
from archetype_classifier.models.most_common import MostCommonArchetype
from shared.database import Database

CONTROL, RED_DECK_WINS, AZORIUS_CONTROL = 2, 16, 49
V = LabelStatus.VERIFIED
# The decks of "Experiment reports" (Scenarios.md), plus a test-season deck. Deck 201 repeats deck 101's maindeck, and deck 302 has 3 unseen copies.
DECKS = {101: (30, Split.TRAIN, V, RED_DECK_WINS, RED), 102: (30, Split.TRAIN, V, AZORIUS_CONTROL, BLUE), 301: (30, Split.HELD_OUT, V, RED_DECK_WINS, RED),
         302: (30, Split.HELD_OUT, V, AZORIUS_CONTROL, BLUE), 201: (39, Split.VALIDATION, V, RED_DECK_WINS, RED), 202: (39, Split.VALIDATION, V, AZORIUS_CONTROL, BLUE),
         401: (41, Split.TEST, V, RED_DECK_WINS, RED)}
TRAIN, VALIDATION, SCOPE = frozenset({Split.TRAIN}), frozenset({Split.VALIDATION}), frozenset({Split.HELD_OUT, Split.VALIDATION})
RUN_1 = {301: RED_DECK_WINS, 302: RED_DECK_WINS, 201: RED_DECK_WINS, 202: RED_DECK_WINS}  # The mock model guesses Red Deck Wins everywhere.
RUN_2 = {301: RED_DECK_WINS, 302: CONTROL, 201: RED_DECK_WINS, 202: CONTROL}  # A baseline that falls back to Control for the Azorius Control decks.


def mock_model(seed: int) -> tuple[MostCommonArchetype, ModelRecord]:
    model = MostCommonArchetype.from_state({}, {'archetype_id': RED_DECK_WINS, 'training_decks_with_archetype': 1, 'training_decks': 2}, [], None)  # type: ignore[arg-type]
    return model, ModelRecord('most common archetype', 1, {}, 1, 1, seed, TRAIN, VALIDATION, 2, 'a' * 40, 2, 'b' * 40, 0.01)

@pytest.fixture
def runs(experiments_db: Database) -> tuple[int, int]:
    """Run 1 of model 1 and baseline run 2 of model 2, both on {HELD_OUT, VALIDATION}."""
    loader.ensure_schema(experiments_db)
    store_snapshot(experiments_db, 1, loader.create_scheme(experiments_db, SplitScheme('typical')), DECKS, unseen={302: 3}, maindecks={201: f'{101:040x}'})
    run_ids = []
    for seed, guesses in ((0, RUN_1), (1, RUN_2)):
        model_id = save_model(experiments_db, *mock_model(seed))
        run_ids.append(save_run(experiments_db, model_id, SCOPE, [Prediction(i, g, {}) for i, g in guesses.items()]))
    return run_ids[0], run_ids[1]

def render(edb: Database, run_id: int = 1, **kwargs: object) -> list[str]:
    return render_report(edb, run_id, min_decks=1, prs=(6, 31), **kwargs).splitlines()  # type: ignore[arg-type]


# Scenario: the header says exactly what produced the numbers.

def test_the_header_says_exactly_what_produced_the_numbers(experiments_db: Database, runs: tuple[int, int]) -> None:
    lines = render(experiments_db)
    assert lines[0] == '# Run 1: most common archetype v1'
    for expected in ['| Run | 1 |', '| Scope | held_out, validation |', '| Decks predicted | 4 |', f'| Prediction hash | {prediction_hash([Prediction(i, g, {}) for i, g in RUN_1.items()])} |',
                     '| Model | 1: most common archetype v1, parameters {}, seed 0 |', '| Snapshot | 1 |', '| Scheme | 1 (typical) |',
                     '| Trained on | train (2 decks) |', '| Tuned on | validation (2 decks) |', '| Metrics version | 1 |', '| Rows version | 1 |', '| PRs | #6, #31 |']:
        assert expected in lines
    assert any(line.startswith('| Made | ') for line in lines)
