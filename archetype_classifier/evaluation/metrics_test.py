import dataclasses
import logging

import pytest
from pytest import approx

from archetype_classifier.evaluation.metrics import ScoredDeck, score, score_deck
from archetype_classifier.evaluation.scenario_set import AGGRO, AZORIUS_CONTROL, MONO_RED_DEVOTION, NO_GUESS, PRISONER, RED_DECK_WINS, TREE, scenario_decks

THREE_PLACES = 0.0005  # Scenarios.md gives scores to three decimal places.


def test_an_exact_guess_scores_one() -> None:
    s = score_deck(TREE, PRISONER, PRISONER)
    assert (s.hp, s.hr, s.hf) == (1.0, 1.0, 1.0)
    assert s.exact

def test_a_correct_parent_fallback_beats_a_wrong_branch() -> None:
    guesses = [PRISONER, RED_DECK_WINS, MONO_RED_DEVOTION, AZORIUS_CONTROL]
    scores = [score_deck(TREE, PRISONER, guess) for guess in guesses]
    assert [(s.hp, s.hr) for s in scores] == [approx((1.0, 1.0), abs=THREE_PLACES), approx((1.0, 0.667), abs=THREE_PLACES), approx((0.667, 0.667), abs=THREE_PLACES), (0.0, 0.0)]
    hfs = [s.hf for s in scores]
    assert hfs == sorted(hfs, reverse=True) and len(set(hfs)) == 4

def test_a_too_specific_guess_on_a_parent_label_is_penalised() -> None:
    too_specific = score_deck(TREE, RED_DECK_WINS, PRISONER)
    assert (too_specific.hp, too_specific.hr) == approx((0.667, 1.0), abs=THREE_PLACES)
    assert score_deck(TREE, RED_DECK_WINS, RED_DECK_WINS).hf > too_specific.hf > score_deck(TREE, RED_DECK_WINS, AZORIUS_CONTROL).hf
    # Tentative: a too-specific guess costs more precision than a parent fallback the same distance off.
    parent_fallback = score_deck(TREE, PRISONER, RED_DECK_WINS)
    assert too_specific.hp is not None and parent_fallback.hp is not None
    assert too_specific.hp < parent_fallback.hp

def test_a_wrong_child_on_the_right_branch_beats_a_top_level_fallback() -> None:
    assert score_deck(TREE, PRISONER, MONO_RED_DEVOTION).hf == approx(0.667, abs=THREE_PLACES)
    assert score_deck(TREE, PRISONER, AGGRO).hf == approx(0.5, abs=THREE_PLACES)

def test_no_guess_scores_as_a_guess_of_the_root() -> None:
    s = score_deck(TREE, PRISONER, NO_GUESS)
    assert (s.hp, s.hr, s.hf) == (None, 0.0, 0.0)
    assert not s.exact

P, MRD, RDW, A, AC, NONE = PRISONER, MONO_RED_DEVOTION, RED_DECK_WINS, AGGRO, AZORIUS_CONTROL, NO_GUESS
ON, OFF = True, False
# The table under "Summarising a set of guesses": label, guess, hP, hR, hF, depth difference, on-path.
SCENARIO_TABLE = [
    (P, P, 1.0, 1.0, 1.0, 0, ON), (P, MRD, 0.667, 0.667, 0.667, 0, OFF), (P, RDW, 1.0, 0.667, 0.8, -1, ON),
    (P, A, 1.0, 0.333, 0.5, -2, ON), (P, AC, 0.0, 0.0, 0.0, -1, OFF), (P, NONE, None, 0.0, 0.0, -3, ON),
    (MRD, P, 0.667, 0.667, 0.667, 0, OFF), (MRD, MRD, 1.0, 1.0, 1.0, 0, ON), (MRD, RDW, 1.0, 0.667, 0.8, -1, ON),
    (MRD, A, 1.0, 0.333, 0.5, -2, ON), (MRD, AC, 0.0, 0.0, 0.0, -1, OFF), (MRD, NONE, None, 0.0, 0.0, -3, ON),
    (RDW, P, 0.667, 1.0, 0.8, 1, ON), (RDW, MRD, 0.667, 1.0, 0.8, 1, ON), (RDW, RDW, 1.0, 1.0, 1.0, 0, ON),
    (RDW, A, 1.0, 0.5, 0.667, -1, ON), (RDW, AC, 0.0, 0.0, 0.0, 0, OFF), (RDW, NONE, None, 0.0, 0.0, -2, ON),
    (A, P, 0.333, 1.0, 0.5, 2, ON), (A, MRD, 0.333, 1.0, 0.5, 2, ON), (A, RDW, 0.5, 1.0, 0.667, 1, ON),
    (A, A, 1.0, 1.0, 1.0, 0, ON), (A, AC, 0.0, 0.0, 0.0, 1, OFF), (A, NONE, None, 0.0, 0.0, -1, ON),
    (AC, P, 0.0, 0.0, 0.0, 1, OFF), (AC, MRD, 0.0, 0.0, 0.0, 1, OFF), (AC, RDW, 0.0, 0.0, 0.0, 0, OFF),
    (AC, A, 0.0, 0.0, 0.0, -1, OFF), (AC, AC, 1.0, 1.0, 1.0, 0, ON), (AC, NONE, None, 0.0, 0.0, -2, ON),
]

@pytest.mark.parametrize(('label', 'guess', 'hp', 'hr', 'hf', 'depth_difference', 'on_path'), SCENARIO_TABLE)
def test_every_pair_in_the_scenario_table_scores_as_listed(label: int, guess: int | None, hp: float | None, hr: float, hf: float, depth_difference: int, on_path: bool) -> None:
    s = score_deck(TREE, label, guess)
    assert s.hp == (None if hp is None else approx(hp, abs=THREE_PLACES))
    assert (s.hr, s.hf) == approx((hr, hf), abs=THREE_PLACES)
    assert (s.depth_difference, s.on_path) == (depth_difference, on_path)

def test_micro_averaging_sums_over_decks() -> None:
    micro = score(TREE, scenario_decks(), min_decks=1).micro
    assert (micro.hp, micro.hr, micro.hf) == approx((0.911, 0.865, 0.887), abs=THREE_PLACES)

def test_coverage_and_exact_match_rate() -> None:
    scores = score(TREE, scenario_decks(), min_decks=1)
    assert scores.coverage == approx(4110 / 4350)
    assert scores.exact_match_rate == approx(3000 / 4350)

@pytest.mark.parametrize(('min_decks', 'qualifying', 'hp', 'hr', 'hf'), [
    (1, 5, 0.851, 0.867, 0.852),
    (500, 4, 0.920, 0.872, 0.894),  # Aggro left out.
    (800, 3, 0.950, 0.858, 0.902),  # Aggro and Red Deck Wins left out.
])
def test_macro_averaging_weighs_every_labelled_archetype_equally(min_decks: int, qualifying: int, hp: float, hr: float, hf: float) -> None:
    scores = score(TREE, scenario_decks(), min_decks=min_decks)
    assert (scores.macro.hp, scores.macro.hr, scores.macro.hf) == approx((hp, hr, hf), abs=THREE_PLACES)
    assert (scores.min_decks, scores.macro_archetypes, scores.labelled_archetypes) == (min_decks, qualifying, 5)

def test_an_archetype_with_no_guesses_is_left_out_of_macro_precision_only() -> None:
    decks = [ScoredDeck(1, PRISONER, PRISONER, 'a'), ScoredDeck(2, AZORIUS_CONTROL, NO_GUESS, 'b')]
    macro = score(TREE, decks, min_decks=1).macro
    assert (macro.hp, macro.hr, macro.hf) == (1.0, 0.5, 0.5)

def test_depth_differences_are_counted_separately_on_and_off_the_path() -> None:
    scores = score(TREE, scenario_decks(), min_decks=1)
    assert scores.on_path_depths.counts == {-3: 100, -2: 170, -1: 360, 0: 3000, 1: 330, 2: 70}
    assert scores.on_path_depths.mean == approx(-0.132, abs=THREE_PLACES)
    assert scores.off_path_depths.counts == {-1: 40, 0: 240, 1: 40}
    assert scores.off_path_depths.mean == 0.0

def test_confusions_are_counted_by_label_and_guess() -> None:
    confusions = score(TREE, scenario_decks(), min_decks=1).confusions
    assert (len(confusions), sum(c.decks for c in confusions)) == (25, 1350)
    assert [c.decks for c in confusions] == sorted((c.decks for c in confusions), reverse=True)
    assert {(c.label_id, c.guess_id, c.decks, c.on_path) for c in confusions[:6]} == {
        (RDW, P, 180, ON), (P, RDW, 150, ON), (P, MRD, 120, OFF), (MRD, RDW, 120, ON), (MRD, P, 100, OFF), (RDW, MRD, 90, ON),
    }

NOT_IN_TREE = 99

@pytest.mark.parametrize('extra', [ScoredDeck(9999, PRISONER, NOT_IN_TREE, 'extra'), ScoredDeck(9999, NOT_IN_TREE, PRISONER, 'extra')], ids=['guess', 'label'])
def test_a_deck_outside_the_tree_is_skipped_with_a_warning(extra: ScoredDeck, caplog: pytest.LogCaptureFixture) -> None:
    expected = score(TREE, scenario_decks(), min_decks=1)
    with caplog.at_level(logging.WARNING):
        scores = score(TREE, [*scenario_decks(), extra], min_decks=1)
    assert str(NOT_IN_TREE) in caplog.text
    assert (scores.skipped_decks, scores.missing_archetype_ids) == (1, frozenset({NOT_IN_TREE}))
    assert dataclasses.replace(scores, skipped_decks=0, missing_archetype_ids=frozenset()) == expected
