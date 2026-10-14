"""Reference decks for every model, rule-level (Scenarios.md, "Reference decks for every model"). Real data is checked in reference_decks_local_test.py."""
from collections import Counter

from archetype_classifier.evaluation.model import PredictDeck
from archetype_classifier.evaluation.reference_decks import GROUPS, HAND_MADE_ID, REFERENCE_DECKS, Kind, build_hand_made_deck

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
