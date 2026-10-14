"""Reference decks for every model, rule-level (Scenarios.md, "Reference decks for every model"). Real data is checked in reference_decks_local_test.py."""
import logging
from collections import Counter

import pytest

from archetype_classifier.evaluation.model import Candidate, PredictDeck, Prediction
from archetype_classifier.evaluation.reference_decks import GROUPS, HAND_MADE_ID, REFERENCE_DECKS, Kind, ReferenceDeck, ReferenceResult, build_hand_made_deck, build_reference_result

# The list matches the scenarios.

def test_five_guards_seven_hard_cases_and_one_extreme() -> None:
    kinds = Counter(d.kind for d in REFERENCE_DECKS)
    assert kinds == {Kind.GUARD: 5, Kind.HARD: 7, Kind.EXTREME: 1}
    assert len({d.deck_id for d in REFERENCE_DECKS}) == len(REFERENCE_DECKS)
    assert [d.deck_id for d in REFERENCE_DECKS if d.kind == Kind.GUARD] == [269508, 269539, 269503, 269833, 269466]
    assert [d.deck_id for d in REFERENCE_DECKS if d.kind == Kind.HARD] == [269484, 269637, 271375, 269591, 269653, 269940, 270398]

def test_guards_and_hard_cases_have_a_label_and_a_pass_mark_and_the_extreme_has_neither() -> None:
    for d in REFERENCE_DECKS:
        if d.kind == Kind.EXTREME:
            assert (d.label, d.top, d.deck_id) == (None, 0, HAND_MADE_ID)
            assert d.maindeck is not None
        else:
            assert d.label and d.top in (1, 5) and d.maindeck is None and d.deck_id > 0, d.deck_id
    assert {d.label for d in REFERENCE_DECKS if d.top == 5} == {'Izzet Madcap'}  # Only the new archetype needs just the top 5.

def test_groups_belong_to_hard_cases_and_include_their_deck() -> None:
    hard = {d.deck_id for d in REFERENCE_DECKS if d.kind == Kind.HARD}
    assert {deck: len(group) for deck, group in GROUPS.items()} == {269484: 5, 269637: 66, 271375: 7, 269591: 24}
    for deck, group in GROUPS.items():
        assert deck in hard and deck in group and list(group) == sorted(set(group))


# Scenario: a deck of only newly legal cards (extreme).

def test_the_hand_made_deck_is_a_legal_60_card_list_with_24_lands() -> None:
    deck = build_hand_made_deck()
    lands = {'Botanical Sanctum', 'Breeding Pool', 'Waterlogged Grove', 'Daily Bugle Building', 'Zanarkand, Ancient Metropolis', 'Jidoor, Aristocratic Capital'}
    assert (deck.deck_id, deck.source, deck.sideboard) == (HAND_MADE_ID, 'League', ())
    assert sum(c.n for c in deck.maindeck) == 60
    assert max(c.n for c in deck.maindeck) == 4
    assert sum(c.n for c in deck.maindeck if c.card in lands) == 24
    assert [c.card for c in deck.maindeck] == sorted(c.card for c in deck.maindeck)  # Sorted by name, as every loaded deck is.

def test_the_hand_made_deck_is_the_extremes_maindeck() -> None:
    [extreme] = [d for d in REFERENCE_DECKS if d.kind == Kind.EXTREME]
    assert build_hand_made_deck() == PredictDeck(HAND_MADE_ID, 'League', extreme.maindeck or (), ())


# Scoring one deck: the label's rank among the candidates, or the guess for a model without them.

RED_DECK_WINS, MONO_RED_SWARM, AZORIUS_CONTROL, IZZET_MADCAP = 16, 164, 49, 642
IDS = {'Red Deck Wins': RED_DECK_WINS, 'Mono Red Swarm': MONO_RED_SWARM, 'Azorius Control': AZORIUS_CONTROL, 'Izzet Madcap': IZZET_MADCAP}
GUARD = ReferenceDeck(101, 'Red Deck Wins', Kind.GUARD, 1, 'a guard')
NEW = ReferenceDeck(102, 'Izzet Madcap', Kind.HARD, 5, 'a new archetype')
EXTREME = ReferenceDeck(HAND_MADE_ID, None, Kind.EXTREME, 0, 'an extreme')

def ranked(deck_id: int, *ids: int) -> Prediction:
    return Prediction(deck_id, ids[0] if ids else None, {}, tuple(Candidate(i, 1.0 - k / 10) for k, i in enumerate(ids)))

@pytest.mark.parametrize(('deck', 'prediction', 'rank', 'passed'), [
    (GUARD, ranked(101, RED_DECK_WINS, MONO_RED_SWARM), 1, True),
    (GUARD, ranked(101, MONO_RED_SWARM, RED_DECK_WINS), 2, False),  # Candidate 2 misses a top-1 mark.
    (NEW, ranked(102, 1, 2, 3, IZZET_MADCAP, 5, 6), 4, True),  # Within the top 5.
    (NEW, ranked(102, 1, 2, 3, 4, 5, IZZET_MADCAP), 6, False),  # Just outside it.
    (GUARD, ranked(101, MONO_RED_SWARM, AZORIUS_CONTROL), None, False),  # Not in the list.
    (GUARD, ranked(101), None, False),  # An empty list misses.
])
def test_the_rank_and_pass_come_from_the_candidates(deck: ReferenceDeck, prediction: Prediction, rank: int | None, passed: bool) -> None:
    result = build_reference_result(deck, prediction, IDS)
    assert (result.rank, result.passed, result.missing_label) == (rank, passed, False)

@pytest.mark.parametrize(('guess', 'rank', 'passed'), [(RED_DECK_WINS, 1, True), (MONO_RED_SWARM, None, False), (None, None, False)])
def test_a_model_without_candidates_is_judged_on_its_guess(guess: int | None, rank: int | None, passed: bool) -> None:
    result = build_reference_result(GUARD, Prediction(101, guess, {}), IDS)
    assert (result.rank, result.passed, result.top_five) == (rank, passed, ())

def test_the_result_records_the_guess_and_the_first_five_candidates() -> None:
    result = build_reference_result(GUARD, ranked(101, MONO_RED_SWARM, RED_DECK_WINS, 3, 4, 5, 6, 7), IDS)
    assert result == ReferenceResult(101, 2, False, MONO_RED_SWARM, (MONO_RED_SWARM, RED_DECK_WINS, 3, 4, 5), False)

def test_an_extreme_has_no_rank_and_no_pass_mark() -> None:
    result = build_reference_result(EXTREME, ranked(HAND_MADE_ID, AZORIUS_CONTROL, MONO_RED_SWARM), IDS)
    assert result == ReferenceResult(HAND_MADE_ID, None, None, AZORIUS_CONTROL, (AZORIUS_CONTROL, MONO_RED_SWARM), False)

def test_a_group_deck_is_scored_against_its_hard_cases_label() -> None:
    result = build_reference_result(GUARD, ranked(105, RED_DECK_WINS), IDS)  # Another deck of the group, with the reference deck's label and mark.
    assert (result.deck_id, result.rank, result.passed) == (105, 1, True)

def test_a_label_missing_from_the_snapshot_warns_and_is_recorded(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        result = build_reference_result(ReferenceDeck(103, 'Boros Engineers', Kind.HARD, 1, 'not in this snapshot'), ranked(103, RED_DECK_WINS), IDS)
    assert (result.rank, result.passed, result.missing_label) == (None, None, True)
    assert "No archetype named 'Boros Engineers' for reference deck 103" in caplog.text
