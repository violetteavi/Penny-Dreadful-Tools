"""Deck diffs (#62): what changed between a training row T and a deck D, and how far it moved D along an archetype's axis."""
import math

import numpy as np
import pytest

from archetype_classifier.geometry.diffs import DeckDiff, build_axis, build_deck_diff, build_share_axis
from archetype_classifier.geometry.space_test import deck, lists_space, rows_space

ROOT_HALF = math.sqrt(0.5)


def test_a_diff_goes_copy_by_copy() -> None:
    target = deck(Shock=4, Burst_Lightning=4, Mountain=52)
    mine = deck(Shock=2, Lightning_Bolt=4, Mountain=54)
    assert build_deck_diff(target, mine) == DeckDiff(kept=deck(Shock=2, Mountain=52), removed=deck(Burst_Lightning=4, Shock=2),
                                                     added=deck(Lightning_Bolt=4, Mountain=2))


# The axis: from a contrast's centroid to the archetype's. Cards in CARD_EMBEDDING's order: Island (1, 0, 0), Mountain (0.8, 0, 0.6),
# Essence Scatter (0, 1, 0), Negate (0, 0.8, 0.6), Shock (0, 0, 1).

ALL_ESSENCE_SCATTER, ALL_SHOCK = np.array([0, 0, 1.0, 0, 0]), np.array([0, 0, 0, 0, 1.0])

def test_the_axis_points_from_the_contrast_to_the_archetype() -> None:
    axis = build_axis(lists_space([(1, deck(Island=60))]), ALL_ESSENCE_SCATTER, ALL_SHOCK)
    assert axis is not None
    assert axis.gap == pytest.approx(math.sqrt(2))  # From (0, 0, 1) to (0, 1, 0).
    assert axis.direction == pytest.approx([0, ROOT_HALF, -ROOT_HALF])
    assert axis.alignment == pytest.approx([0, -0.6 * ROOT_HALF, ROOT_HALF, 0.2 * ROOT_HALF, -ROOT_HALF])

def test_no_axis_when_the_centroids_coincide() -> None:
    assert build_axis(lists_space([(1, deck(Island=60))]), ALL_SHOCK, ALL_SHOCK) is None


def test_the_share_axis_aligns_each_card_by_its_share_difference() -> None:
    axis = build_share_axis(ALL_ESSENCE_SCATTER, ALL_SHOCK)
    assert axis is not None
    assert axis.gap == pytest.approx(math.sqrt(2))
    assert axis.alignment == pytest.approx([0, 0, ROOT_HALF, 0, -ROOT_HALF])  # beta: the card's own share difference, not its text.

def test_no_share_axis_when_the_shares_coincide() -> None:
    assert build_share_axis(ALL_SHOCK, ALL_SHOCK) is None

def test_in_the_bag_the_share_axis_is_the_spaces_axis() -> None:
    space = rows_space([(1, (1, 0, 0, 0, 0))])  # No embedding: each card is its own coordinate, as in the bag of cards.
    axis, shares = build_axis(space, ALL_ESSENCE_SCATTER, ALL_SHOCK), build_share_axis(ALL_ESSENCE_SCATTER, ALL_SHOCK)
    assert axis is not None and shares is not None
    assert (axis.gap, axis.alignment.tolist()) == (pytest.approx(shares.gap), pytest.approx(shares.alignment.tolist()))
