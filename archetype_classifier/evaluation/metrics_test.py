import dataclasses
import logging

import pytest
from pytest import approx

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import METRICS_VERSION, REVIEWER_CANDIDATES, ArchetypeTree, ScoredDeck, compare, label_rank, score, score_deck
from archetype_classifier.evaluation.scenario_set import AGGRO, AZORIUS_CONTROL, CONTROL, MONO_RED_DEVOTION, NO_GUESS, PRISONER, RED_DECK_WINS, TREE, scenario_decks

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
    assert scores.macro is not None
    assert (scores.macro.hp, scores.macro.hr, scores.macro.hf) == approx((hp, hr, hf), abs=THREE_PLACES)
    assert (scores.min_decks, scores.macro_archetypes, scores.labelled_archetypes) == (min_decks, qualifying, 5)

def test_an_archetype_with_no_guesses_is_left_out_of_macro_precision_only() -> None:
    decks = [ScoredDeck(1, PRISONER, PRISONER, 'a'), ScoredDeck(2, AZORIUS_CONTROL, NO_GUESS, 'b')]
    macro = score(TREE, decks, min_decks=1).macro
    assert macro is not None
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

def test_scores_report_how_many_decks_and_maindecks_they_cover() -> None:
    assert (score(TREE, scenario_decks(), min_decks=1).decks, score(TREE, scenario_decks(), min_decks=1).maindecks) == (4350, 4350)
    assert score(TREE, scenario_decks(decks_per_maindeck=10), min_decks=1).maindecks == 435

ABOUT = 0.005  # Scenarios.md gives interval ends approximately: they move by about 0.001 with the seed.

def test_identical_maindecks_dont_narrow_the_interval() -> None:
    decks = scenario_decks()
    twins = [dataclasses.replace(d, deck_id=d.deck_id + 10_000) for d in decks]
    single, doubled = score(TREE, decks, min_decks=1, seed=7), score(TREE, decks + twins, min_decks=1, seed=7)
    assert single.micro.hf == approx(0.887, abs=THREE_PLACES)
    assert (single.micro_intervals.hf.low, single.micro_intervals.hf.high) == approx((0.881, 0.893), abs=ABOUT)
    assert (doubled.micro, doubled.micro_intervals) == (single.micro, single.micro_intervals)

def test_intervals_are_repeatable_and_recorded() -> None:
    first, second = score(TREE, scenario_decks(), min_decks=1, seed=7, resamples=200), score(TREE, scenario_decks(), min_decks=1, seed=7, resamples=200)
    assert first.micro_intervals == second.micro_intervals
    assert (first.seed, first.resamples) == (7, 200)
    exact = score(TREE, [d for d in scenario_decks() if d.guess_id == d.label_id], min_decks=1)
    assert (exact.micro.hf, exact.micro_intervals.hf.low, exact.micro_intervals.hf.high) == (1.0, 1.0, 1.0)

def test_fewer_maindecks_give_a_wider_interval() -> None:
    many, few = score(TREE, scenario_decks(), min_decks=1, seed=7), score(TREE, scenario_decks(decks_per_maindeck=10), min_decks=1, seed=7)
    assert few.micro == many.micro
    assert (few.micro_intervals.hf.low, few.micro_intervals.hf.high) == approx((0.867, 0.906), abs=ABOUT)
    assert few.micro_intervals.hf.high - few.micro_intervals.hf.low > 2 * (many.micro_intervals.hf.high - many.micro_intervals.hf.low)

def test_a_model_compared_with_itself_differs_by_nothing() -> None:
    c = compare(TREE, scenario_decks(), scenario_decks(), resamples=200)
    for name in ('hp', 'hr', 'hf', 'exact_match_rate'):
        assert getattr(c.difference, name) == 0.0
        assert (getattr(c.intervals, name).low, getattr(c.intervals, name).high) == (0.0, 0.0)

def model_b() -> list[ScoredDeck]:
    """The scenario set, except that 60 of the 120 Prisoner decks guessed as Mono Red Devotion are guessed as Prisoner."""
    decks, fixed = [], 0
    for d in scenario_decks():
        if (d.label_id, d.guess_id) == (PRISONER, MONO_RED_DEVOTION) and fixed < 60:
            d, fixed = dataclasses.replace(d, guess_id=PRISONER), fixed + 1
        decks.append(d)
    return decks

def test_a_consistent_small_improvement_is_detected() -> None:
    a, b = score(TREE, scenario_decks(), min_decks=1, seed=7), score(TREE, model_b(), min_decks=1, seed=7)
    assert (a.micro.hf, b.micro.hf) == approx((0.887, 0.893), abs=THREE_PLACES)
    assert (a.exact_match_rate, b.exact_match_rate) == approx((0.690, 0.703), abs=THREE_PLACES)
    assert b.micro_intervals.hf.low < a.micro_intervals.hf.high  # The separate intervals overlap...
    c = compare(TREE, scenario_decks(), model_b(), seed=7)
    assert c.intervals.hf.low > 0  # ...but the paired difference is clear of 0.
    assert (c.intervals.hf.low, c.intervals.hf.high) == approx((0.004, 0.007), abs=0.001)

def test_decks_only_one_model_scored_are_left_out_of_the_comparison(caplog: pytest.LogCaptureFixture) -> None:
    a = scenario_decks()
    b = [*a[:-1], dataclasses.replace(a[-1], guess_id=NOT_IN_TREE)]
    with caplog.at_level(logging.WARNING):
        c = compare(TREE, a, b, resamples=200)
    assert (c.decks, c.left_out) == (4349, 1)
    assert 'left out' in caplog.text
    assert c == dataclasses.replace(compare(TREE, a[:-1], b[:-1], resamples=200), left_out=1)

def test_no_archetype_meets_the_macro_minimum(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        scores = score(TREE, scenario_decks(), min_decks=2000, resamples=200)
    assert (scores.macro, scores.macro_archetypes) == (None, 0)
    assert '2000' in caplog.text
    expected = score(TREE, scenario_decks(), min_decks=1, resamples=200)
    assert dataclasses.replace(scores, macro=expected.macro, min_decks=1, macro_archetypes=expected.macro_archetypes) == expected

# A program error rather than a scenario: there is nothing to score.
@pytest.mark.parametrize('decks', [[], [ScoredDeck(1, NOT_IN_TREE, PRISONER, 'a'), ScoredDeck(2, PRISONER, NOT_IN_TREE, 'b')]], ids=['empty', 'all-skipped'])
def test_scoring_no_decks_is_an_error(decks: list[ScoredDeck]) -> None:
    with pytest.raises(ValueError, match='No decks to score'):
        score(TREE, decks, min_decks=1)

def test_comparing_models_with_no_decks_in_common_is_an_error() -> None:
    with pytest.raises(ValueError, match='No decks to compare'):
        compare(TREE, [ScoredDeck(1, PRISONER, PRISONER, 'a')], [ScoredDeck(2, PRISONER, PRISONER, 'b')])



# Scenarios: "Ranked candidates". Candidate ids needn't be in the tree; labels and guesses must be, as for hF.

MONO_RED_SWARM, WHITE_WEENIE, MONO_WHITE_HUMANS = 8, 9, 10
RANKED_TREE = ArchetypeTree({**TREE.archetypes, MONO_RED_SWARM: ArchetypeSnapshot(MONO_RED_SWARM, 'Mono Red Swarm', AGGRO, 1),
                             WHITE_WEENIE: ArchetypeSnapshot(WHITE_WEENIE, 'White Weenie', AGGRO, 1),
                             MONO_WHITE_HUMANS: ArchetypeSnapshot(MONO_WHITE_HUMANS, 'Mono White Humans', WHITE_WEENIE, 2)})
RANKED = [
    ScoredDeck(501, PRISONER, PRISONER, 'm501', (PRISONER, RED_DECK_WINS, MONO_RED_DEVOTION)),
    ScoredDeck(502, RED_DECK_WINS, PRISONER, 'm502', (PRISONER, MONO_RED_DEVOTION, RED_DECK_WINS, AGGRO, MONO_RED_SWARM)),
    ScoredDeck(503, AZORIUS_CONTROL, NO_GUESS, 'm503', (PRISONER, RED_DECK_WINS, MONO_RED_DEVOTION, MONO_RED_SWARM, WHITE_WEENIE, MONO_WHITE_HUMANS, AZORIUS_CONTROL, CONTROL)),
    ScoredDeck(504, AGGRO, RED_DECK_WINS, 'm504', (RED_DECK_WINS, MONO_RED_SWARM)),
]
EMPTY_LIST = ScoredDeck(505, MONO_RED_SWARM, NO_GUESS, 'm505', ())

def test_top_1_top_5_and_mrr_count_the_labels_rank() -> None:
    ranking = score(RANKED_TREE, RANKED, min_decks=1).ranking
    assert ranking is not None
    assert (ranking.top_1, ranking.top_5, ranking.mrr) == approx((0.250, 0.500, 0.369), abs=THREE_PLACES)
    assert ranking.no_candidates == 0

def test_a_deck_with_an_empty_list_scores_0_and_is_counted() -> None:
    ranking = score(RANKED_TREE, [*RANKED, EMPTY_LIST], min_decks=1).ranking
    assert ranking is not None
    assert (ranking.top_1, ranking.top_5, ranking.mrr) == approx((0.200, 0.400, 0.295), abs=THREE_PLACES)
    assert ranking.no_candidates == 1

def test_candidate_intervals_treat_identical_maindecks_as_one() -> None:
    decks = [*RANKED, EMPTY_LIST]
    twins = [dataclasses.replace(d, deck_id=d.deck_id + 1000) for d in decks]
    single, doubled = score(RANKED_TREE, decks, min_decks=1, seed=7).ranking, score(RANKED_TREE, decks + twins, min_decks=1, seed=7).ranking
    assert single is not None and doubled is not None
    assert dataclasses.replace(doubled, no_candidates=1) == single  # Only the count of decks doubles.
    for name in ('top_1', 'top_5', 'mrr'):
        interval = getattr(single.intervals, name)
        assert interval.low <= getattr(single, name) <= interval.high
    c = compare(RANKED_TREE, decks, decks, resamples=200)
    for name in ('top_1', 'top_5', 'mrr'):
        assert getattr(c.difference, name) == 0.0
        assert (getattr(c.intervals, name).low, getattr(c.intervals, name).high) == (0.0, 0.0)

def test_a_better_ranking_shows_in_the_comparison() -> None:
    better = [dataclasses.replace(RANKED[1], candidates=(RED_DECK_WINS, PRISONER)), *RANKED[:1], *RANKED[2:]]  # Deck 502's label moves from rank 3 to rank 1.
    c = compare(RANKED_TREE, RANKED, better, resamples=200)
    assert (c.difference.top_1, c.difference.top_5, c.difference.mrr) == approx((0.25, 0.0, (1 - 1 / 3) / 4))

def test_a_model_without_candidates_has_no_ranking() -> None:
    assert score(TREE, scenario_decks(), min_decks=1, resamples=200).ranking is None
    c = compare(RANKED_TREE, [dataclasses.replace(d, candidates=None) for d in RANKED], RANKED, resamples=200)
    assert (c.difference.top_1, c.difference.top_5, c.difference.mrr) == (None, None, None)
    assert (c.intervals.top_1, c.intervals.top_5, c.intervals.mrr) == (None, None, None)
    assert c.difference.hf == 0.0  # The guesses are still compared.

def test_in_a_set_with_candidates_a_deck_without_them_counts_as_an_empty_list() -> None:
    ranking = score(RANKED_TREE, [*RANKED, dataclasses.replace(EMPTY_LIST, candidates=None)], min_decks=1).ranking
    assert ranking == score(RANKED_TREE, [*RANKED, EMPTY_LIST], min_decks=1).ranking

def test_a_candidate_outside_the_tree_is_a_miss_not_a_skip() -> None:
    scores = score(RANKED_TREE, [ScoredDeck(1, PRISONER, PRISONER, 'a', (NOT_IN_TREE, PRISONER))], min_decks=1, resamples=200)
    assert scores.skipped_decks == 0
    assert scores.ranking is not None
    assert (scores.ranking.top_1, scores.ranking.top_5, scores.ranking.mrr) == (0.0, 1.0, 0.5)

def test_label_rank_counts_from_1_and_misses_with_none() -> None:
    assert label_rank(PRISONER, (RED_DECK_WINS, PRISONER)) == 2
    assert label_rank(AGGRO, (RED_DECK_WINS, PRISONER)) is None  # A child of the label doesn't count.
    assert label_rank(PRISONER, ()) is None
    assert REVIEWER_CANDIDATES == 5


# Scenario: metrics are versioned (Scenarios.md, "Experiment reports"). 2: Top 1, Top 5 and MRR on candidates (#14).

def test_metrics_are_versioned() -> None:
    assert METRICS_VERSION == 2
