"""Deck diffs (#62): what changed between a training row T and a deck D, and how far it moved D along an archetype's axis."""
from archetype_classifier.geometry.diffs import DeckDiff, build_deck_diff
from archetype_classifier.geometry.space_test import deck


def test_a_diff_goes_copy_by_copy() -> None:
    target = deck(Shock=4, Burst_Lightning=4, Mountain=52)
    mine = deck(Shock=2, Lightning_Bolt=4, Mountain=54)
    assert build_deck_diff(target, mine) == DeckDiff(kept=deck(Shock=2, Mountain=52), removed=deck(Burst_Lightning=4, Shock=2),
                                                     added=deck(Lightning_Bolt=4, Mountain=2))
