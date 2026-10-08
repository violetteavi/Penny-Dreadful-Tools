"""Reports rendered from stored runs in a real experiments database."""
import dataclasses
import re
import sys
from pathlib import Path
from typing import ClassVar

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation import report
from archetype_classifier.evaluation.model import JSON, Prediction, register
from archetype_classifier.evaluation.report import render_report
from archetype_classifier.evaluation.store import ModelRecord, load_test_looks, prediction_hash, save_model, save_run
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
                     '| Trained on | train (2 decks) |', '| Tuned on | validation (2 decks) |', '| Metrics version | 1 |', '| Rows version | 2 |', '| PRs | #6, #31 |']:
        assert expected in lines
    assert any(line.startswith('| Made | ') for line in lines)


# Scenario: the results table has one line per row, with intervals.

INTERVAL = r'\d\.\d\d \[\d\.\d\d, \d\.\d\d\]'

def test_the_results_table_has_one_line_per_row_with_intervals(experiments_db: Database, runs: tuple[int, int]) -> None:
    lines = render(experiments_db)
    table = lines[lines.index('## Results') + 2:]
    assert table[0] == '| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |'
    rows = [line.split(' | ')[0].removeprefix('| ') for line in table[2:8]]
    assert rows == ['held-out, no unseen cards', 'held-out, unseen cards', 'validation', 'validation, no unseen cards', 'validation, new maindeck', 'validation, repeated maindeck']  # No validation deck has unseen cards, so that row is empty and left out.
    validation = table[4]
    assert re.fullmatch(r'\| validation \| 2 \| 2 \| 0\.50 \[\d\.\d\d, \d\.\d\d\] \| 0\.50 \[\d\.\d\d, \d\.\d\d\] \| 0\.50 \[\d\.\d\d, \d\.\d\d\] \| 0\.50 \| 1\.00 \| 0\.50 \(2 archetypes\) \| tuned on \|', validation)
    assert table[2].endswith('|  |')  # No notes for a held-out row.


# Scenario: archetypes appear by name, and confusions link to example decks.

def test_confusions_appear_by_name_with_links_to_example_decks(experiments_db: Database, runs: tuple[int, int]) -> None:
    lines = render(experiments_db)
    validation = lines[lines.index('### Top confusions: validation') + 2:]
    assert validation[0] == '| Label | Guess | Path | Decks | Example decks |'
    assert validation[2] == '| Azorius Control | Red Deck Wins | off | 1 | [202](https://pennydreadfulmagic.com/decks/202/) |'
    held_out = lines[lines.index('### Top confusions: held-out') + 2:]
    assert held_out[2] == '| Azorius Control | Red Deck Wins | off | 1 | [302](https://pennydreadfulmagic.com/decks/302/) |'

def test_an_archetype_missing_from_the_tree_is_named_as_missing(experiments_db: Database, runs: tuple[int, int]) -> None:
    model_id = save_model(experiments_db, *mock_model(seed=2))
    run_id = save_run(experiments_db, model_id, SCOPE, [Prediction(i, 999 if i == 202 else g, {}) for i, g in RUN_1.items()])
    validation = next(line for line in render(experiments_db, run_id) if line.startswith('| validation |'))
    assert validation.endswith('| tuned on, 1 skipped: missing archetype 999 |')


# Scenario: a baseline run is compared deck by deck.

DIFFERENCE = r'-?\d\.\d\d \[-?\d\.\d\d, -?\d\.\d\d\]'

def test_a_baseline_run_is_compared_deck_by_deck(experiments_db: Database, runs: tuple[int, int]) -> None:
    run_1, run_2 = runs
    lines = render(experiments_db, run_1, baseline_run_id=run_2)
    comparison = lines[lines.index(f'## Compared with run {run_2}') + 2:]
    assert comparison[0] == f'Run {run_1} minus run {run_2}, on the decks both runs guessed, with paired intervals.'
    assert comparison[2] == '| Row | Decks compared | Left out | hF | hP | hR | Exact match |'
    validation = next(line for line in comparison if line.startswith('| validation |'))
    assert re.fullmatch(r'\| validation \| 2 \| 0 \| -0\.36 \[-?\d\.\d\d, -?\d\.\d\d\] \| -0\.50 \[-?\d\.\d\d, -?\d\.\d\d\] \| -0\.25 \[-?\d\.\d\d, -?\d\.\d\d\] \| 0\.00 \[-?\d\.\d\d, -?\d\.\d\d\] \|', validation)
    assert not any(line.startswith('## Compared with') for line in render(experiments_db, run_1))


# Scenario: a validation curve is shown when the model has one.

@register
class Tuned(MostCommonArchetype):
    """A stand-in model that tuned a threshold, keeping its curve in its state as the Model protocol documents."""
    name: ClassVar[str] = 'tuned (test)'

    def state(self) -> dict[str, JSON]:
        return {**super().state(), 'threshold': 20, 'validation_curve': [[10, 0.9, 0.5, 0.643], [20, 0.8, 0.7, 0.747], [30, 0.6, 0.8, 0.686]]}

def test_a_validation_curve_is_shown_when_the_model_has_one(experiments_db: Database, runs: tuple[int, int]) -> None:
    _, record = mock_model(seed=0)
    tuned = Tuned.from_state({}, {'archetype_id': RED_DECK_WINS, 'training_decks_with_archetype': 1, 'training_decks': 2}, [], None)  # type: ignore[arg-type]
    model_id = save_model(experiments_db, tuned, dataclasses.replace(record, name='tuned (test)'))
    lines = render(experiments_db, save_run(experiments_db, model_id, SCOPE, [Prediction(i, g, {}) for i, g in RUN_1.items()]))
    curve = lines[lines.index('## Validation curve') + 2:]
    assert curve[:5] == ['| Threshold | hP | hR | hF |', '|---|---|---|---|', '| 10 | 0.90 | 0.50 | 0.64 |', '| **20 (chosen)** | 0.80 | 0.70 | 0.75 |', '| 30 | 0.60 | 0.80 | 0.69 |']
    mock = render(experiments_db, 1)
    assert mock[mock.index('## Validation curve') + 2] == 'No validation curve: this model has no threshold to tune.'


# Scenario: test results need the gate, and each report logs one look.

def test_test_results_need_the_gate_and_each_report_logs_one_look(experiments_db: Database, runs: tuple[int, int]) -> None:
    run_id = save_run(experiments_db, 1, frozenset({Split.TEST}), [Prediction(401, RED_DECK_WINS, {})])
    with pytest.raises(ValueError, match='include_test'):
        render(experiments_db, run_id)
    assert load_test_looks(experiments_db, run_id) == []
    lines = render(experiments_db, run_id, include_test=True)
    assert any(line.startswith('| test, overall | 1 |') for line in lines)
    assert [look.rows for look in load_test_looks(experiments_db, run_id)] == [['test, overall', 'test, 0 unseen copies', 'test, new maindeck']]


# Scenario: the same run always gives the same report.

def test_the_same_run_always_gives_the_same_report(experiments_db: Database, runs: tuple[int, int]) -> None:
    run_1, run_2 = runs
    assert render_report(experiments_db, run_1, min_decks=1, baseline_run_id=run_2, prs=(6,)) == render_report(experiments_db, run_1, min_decks=1, baseline_run_id=run_2, prs=(6,))


# Scenario: a report is written to docs/experiments/ from the command line.

def test_a_report_is_written_from_the_command_line(experiments_db: Database, runs: tuple[int, int], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    run_1, run_2 = runs
    out = tmp_path / 'docs' / 'experiments' / '20261002_most_common.md'
    monkeypatch.setattr(loader, 'experiments_db', lambda: experiments_db)
    monkeypatch.setattr(sys, 'argv', ['report', str(run_1), '--baseline', str(run_2), '--pr', '6', '--pr', '31', '--min-decks', '1', '--out', str(out)])
    report.main()
    assert out.read_text() == render_report(experiments_db, run_1, min_decks=1, baseline_run_id=run_2, prs=(6, 31))
    assert capsys.readouterr().out.strip() == f'Wrote {out}'


def test_rows_with_no_decks_both_runs_guessed_are_left_out_of_the_comparison(experiments_db: Database, runs: tuple[int, int]) -> None:
    held_out_only = save_run(experiments_db, save_model(experiments_db, *mock_model(seed=3)), frozenset({Split.HELD_OUT}),
                             [Prediction(i, g, {}) for i, g in RUN_2.items() if i in (301, 302)])
    lines = render(experiments_db, 1, baseline_run_id=held_out_only)
    comparison = lines[lines.index(f'## Compared with run {held_out_only}'):]
    assert any(line.startswith('| held-out, no unseen cards | 1 |') for line in comparison)
    assert not any(line.startswith('| validation') for line in comparison)

def test_a_deck_with_no_guess_shows_as_a_no_guess_confusion(experiments_db: Database, runs: tuple[int, int]) -> None:
    unsure = save_run(experiments_db, save_model(experiments_db, *mock_model(seed=4)), SCOPE, [Prediction(i, None if i == 202 else g, {}) for i, g in RUN_1.items()])
    lines = render(experiments_db, unsure)
    validation = lines[lines.index('### Top confusions: validation') + 2:]
    assert validation[2] == '| Azorius Control | no guess | on | 1 | [202](https://pennydreadfulmagic.com/decks/202/) |'
