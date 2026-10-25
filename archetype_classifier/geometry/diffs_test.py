"""Deck diffs (#62): what changed between a training row T and a deck D, and how far it moved D along an archetype's axis."""
import math

import numpy as np
import pytest

from archetype_classifier.geometry.diffs import CardContribution, DeckDiff, build_axis, build_contributions, build_deck_diff, build_share_axis, build_shift
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


# The shift: how far D moved along the target archetype's axis, card by card. T is all Shock, at (0, 0, 1); D is 0.6 Essence Scatter and 0.8 Shock,
# at (0, 0.6, 0.8).

TARGET_LINES, DECK_LINES = np.array([0, 0, 0, 0, 1.0]), np.array([0, 0, 0.6, 0, 0.8])

def test_the_shift_is_how_far_d_moved_along_the_axis() -> None:
    axis = build_axis(lists_space([(1, deck(Island=60))]), ALL_ESSENCE_SCATTER, ALL_SHOCK)
    assert axis is not None
    shift = build_shift(axis, DECK_LINES, TARGET_LINES, movement=math.sqrt(0.4))  # |(0, 0.6, -0.2)|
    assert shift.raw == pytest.approx(0.4 * math.sqrt(2))  # (0, 0.6, -0.2) . (0, 1, -1) / sqrt(2): toward Essence Scatter.
    assert shift.fraction == pytest.approx(0.4)
    assert shift.on_axis == pytest.approx(math.sqrt(0.8))

def test_an_unchanged_deck_has_no_shift_and_no_on_axis_share() -> None:
    axis = build_axis(lists_space([(1, deck(Island=60))]), ALL_ESSENCE_SCATTER, ALL_SHOCK)
    assert axis is not None
    shift = build_shift(axis, TARGET_LINES, TARGET_LINES, movement=0)
    assert (shift.raw, shift.fraction, shift.on_axis) == (0, 0, None)


# Contributions: each changed card's part of the shift, and the kept cards' part from rescaling. T is 56 Island and 4 Shock; D swaps 2 Shock for 2
# Essence Scatter. The axis runs from all Mountain to all Essence Scatter: (-0.8, 1, -0.6) / sqrt(2).

ALL_MOUNTAIN = np.array([0, 1.0, 0, 0, 0])
SWAP_TARGET, SWAP_DECK = deck(Island=56, Shock=4), deck(Island=56, Essence_Scatter=2, Shock=2)

def test_each_changed_card_contributes_and_the_kept_cards_rescale() -> None:
    space = lists_space([(1, SWAP_TARGET), (2, SWAP_DECK)])
    axis = build_axis(space, ALL_ESSENCE_SCATTER, ALL_MOUNTAIN)
    assert axis is not None
    target_lines, deck_lines = space.lines.toarray()
    contributions = build_contributions(axis, space.cards, deck_lines, target_lines, build_deck_diff(SWAP_TARGET, SWAP_DECK))
    assert contributions.cards == [CardContribution('Essence Scatter', 0, 2, pytest.approx(0.025222, abs=1e-6)),
                                   CardContribution('Shock', 4, 2, pytest.approx(0.015095, abs=1e-6))]  # 4 -> 2: its own row, though 2 are kept.
    assert contributions.rescaling == pytest.approx(-0.000717, abs=1e-6)  # Island, kept: its line shrinks, and it points away from Essence Scatter.
