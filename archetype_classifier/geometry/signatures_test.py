"""Defining cards and centroid pushes (Scenarios.md, "Archetype geometry")."""
import numpy as np

from archetype_classifier.geometry.signatures import build_centroid_push, build_defining_cards, build_push, build_ranked_cards
from archetype_classifier.geometry.space import build_presence
from archetype_classifier.geometry.space_test import deck, lists_space, rows_space
from archetype_classifier.geometry.tree_test import ACTUAL_TWIN, AZORIUS_CONTROL, FAMILY_TREE, IZZET_CONTROL, IZZET_TWIN, RED_DECK_WINS, TREE

# Scenario: defining cards rank by evidence, not just by how exclusive they are. An archetype of 500 rows against 84,000 contrast rows.

ONE_OF, TEN_LISTS, SIGNATURE, STAPLE = 'a one-of in a single list', 'a card in 10 lists, nowhere else', "the archetype's signature card", 'an over-represented staple'

def test_defining_cards_rank_by_z_with_log_odds_beside() -> None:
    ranked = build_ranked_cards((ONE_OF, TEN_LISTS, SIGNATURE, STAPLE), np.array([1, 10, 400, 300]), 500, np.array([0, 0, 100, 30_000]), 84_000, top=5)
    assert [c.card for c in ranked] == [SIGNATURE, STAPLE, TEN_LISTS, ONE_OF]
    by_card = {c.card: c for c in ranked}
    for card, log_odds, z in ((ONE_OF, 5.8171, 4.7465), (TEN_LISTS, 7.5400, 7.2123), (SIGNATURE, 8.1011, 54.2397), (STAPLE, 0.9916, 10.8518)):
        assert np.isclose(by_card[card].log_odds, log_odds, atol=5e-5)
        assert np.isclose(by_card[card].z, z, atol=5e-5)
    assert (by_card[SIGNATURE].rows_in, by_card[SIGNATURE].rows_out) == (400, 100)

def test_only_the_top_cards_are_kept() -> None:
    ranked = build_ranked_cards((ONE_OF, TEN_LISTS, SIGNATURE, STAPLE), np.array([1, 10, 400, 300]), 500, np.array([0, 0, 100, 30_000]), 84_000, top=2)
    assert [c.card for c in ranked] == [SIGNATURE, STAPLE]

def test_a_card_no_more_common_in_the_archetype_than_outside_isnt_listed() -> None:
    ranked = build_ranked_cards(('even', 'rarer', 'commoner'), np.array([50, 10, 60]), 100, np.array([500, 400, 500]), 1_000, top=5)
    assert [c.card for c in ranked] == ['commoner']  # 'even' has log-odds exactly 0 and 'rarer' below it.

def test_ties_break_by_log_odds_then_by_name() -> None:
    ranked = build_ranked_cards(('Shock', 'Mountain', 'Island'), np.array([10, 10, 10]), 10, np.array([0, 0, 0]), 10, top=5)
    assert [c.card for c in ranked] == ['Island', 'Mountain', 'Shock']


# Scenario: against its siblings, a card the whole family plays stops being defining. Izzet Control and Azorius Control under Control; Red Deck Wins
# under Aggro. Each archetype's lists differ only in copies.

FAMILY = lists_space([*((IZZET_CONTROL, deck(Essence_Scatter=4, Shock=4, Island=21 + i, Mountain=31 - i)) for i in range(10)),
                      *((AZORIUS_CONTROL, deck(Essence_Scatter=4, Island=56 + i)) for i in range(10)),
                      *((RED_DECK_WINS, deck(Shock=4, Mountain=56 + i)) for i in range(30))])

def test_against_all_rows_a_control_decks_counterspells_lead() -> None:
    ranked = build_defining_cards(build_presence(FAMILY), FAMILY, TREE, IZZET_CONTROL, 'all')
    assert [c.card for c in ranked] == ['Essence Scatter', 'Island', 'Mountain', 'Shock']
    assert [(round(c.log_odds, 4), round(c.z, 4)) for c in ranked] == [(3.4340, 3.1166), (3.4340, 3.1166), (1.3618, 1.2359), (1.3618, 1.2359)]
    assert [(c.rows_in, c.rows_out) for c in ranked] == [(10, 10), (10, 10), (10, 30), (10, 30)]

def test_against_its_siblings_only_the_red_cards_are_listed() -> None:
    ranked = build_defining_cards(build_presence(FAMILY), FAMILY, TREE, IZZET_CONTROL, 'siblings')
    assert [c.card for c in ranked] == ['Mountain', 'Shock']
    assert [(round(c.log_odds, 4), round(c.z, 4)) for c in ranked] == [(4.7958, 3.2468), (4.7958, 3.2468)]
    assert [(c.rows_in, c.rows_out) for c in ranked] == [(10, 0), (10, 0)]


def test_an_only_child_has_no_sibling_contrast_and_no_defining_cards_against_it() -> None:
    space = lists_space([(IZZET_TWIN, deck(Shock=4, Island=56)), (ACTUAL_TWIN, deck(Shock=4, Mountain=56))])
    assert build_defining_cards(build_presence(space), space, FAMILY_TREE, IZZET_TWIN, 'siblings') == []
    assert [c.card for c in build_defining_cards(build_presence(space), space, FAMILY_TREE, IZZET_TWIN, 'all')] == ['Island']

# Scenario: centroid pushes add up to what separates an archetype from its siblings. The hand-made embedding; no weights, linear copies.

def test_centroid_pushes_add_up_to_the_distance_between_the_averages() -> None:
    space = lists_space([(IZZET_CONTROL, deck(Essence_Scatter=4, Negate=4, Shock=4, Island=24, Mountain=24)),
                         (AZORIUS_CONTROL, deck(Essence_Scatter=4, Negate=4, Island=52))])
    push = build_centroid_push(space, TREE, IZZET_CONTROL)
    assert push is not None
    assert np.isclose(push.distance, 0.3960, atol=5e-5)
    assert [c.card for c in push.cards] == ['Mountain', 'Island', 'Shock', 'Negate', 'Essence Scatter']
    expected = {'Mountain': (0.4950, 0, 0.3819, 0.1890), 'Island': (0.4950, 0.9895, -0.2488, 0.1230), 'Shock': (0.0825, 0, 0.9681, 0.0799),
                'Negate': (0.0825, 0.0761, 0.6041, 0.0039), 'Essence Scatter': (0.0825, 0.0761, 0.0290, 0.0002)}
    for c in push.cards:
        assert np.allclose((c.share_in, c.share_out, c.alignment, c.push), expected[c.card], atol=5e-5), c.card
    assert np.isclose(sum(c.push for c in push.cards), push.distance)

def test_an_archetype_with_no_siblings_has_no_push() -> None:
    space = lists_space([(IZZET_TWIN, deck(Shock=4, Island=56)), (ACTUAL_TWIN, deck(Shock=4, Mountain=56))])
    assert build_centroid_push(space, FAMILY_TREE, IZZET_TWIN) is None

def test_with_no_embedding_each_card_is_its_own_coordinate() -> None:
    space = rows_space([(IZZET_CONTROL, (1, 0, 0)), (AZORIUS_CONTROL, (0, 1, 0))])  # The bag of cards: the lines are the vectors.
    push = build_centroid_push(space, TREE, IZZET_CONTROL)
    assert push is not None
    assert np.isclose(push.distance, np.sqrt(2))
    assert [(c.card, round(c.alignment, 4), round(c.push, 4)) for c in push.cards] == [('dimension 1', 0.7071, 0.7071), ('dimension 2', -0.7071, 0.7071)]


# A push against any contrast given as card shares (#62).

def test_a_push_against_a_contrast_adds_up_to_the_distance_between_them() -> None:
    space = lists_space([(IZZET_CONTROL, deck(Island=60))])  # Only the hand-made embedding matters: Island (1, 0, 0), Mountain (0.8, 0, 0.6).
    all_mountain, all_island = np.array([0, 1.0, 0, 0, 0]), np.array([1.0, 0, 0, 0, 0])
    push = build_push(space, all_mountain, all_island)
    assert np.isclose(push.distance, np.sqrt(0.4))  # (0.8, 0, 0.6) - (1, 0, 0) = (-0.2, 0, 0.6).
    assert sorted((c.card, round(c.share_in, 4), round(c.share_out, 4), round(c.alignment, 4), round(c.push, 4)) for c in push.cards) == [
        ('Island', 0, 1, -0.3162, 0.3162), ('Mountain', 1, 0, 0.3162, 0.3162)]  # Equal pushes, up to rounding; cards neither side plays are left out.
    assert np.isclose(sum(c.push for c in push.cards), push.distance)

def test_without_an_embedding_a_push_ranks_cards_by_how_much_their_shares_differ() -> None:
    space = rows_space([(IZZET_CONTROL, (1, 0, 0))])
    push = build_push(space, np.array([0.7, 0.3, 0]), np.array([0.2, 0.4, 0.4]))
    assert np.isclose(push.distance, np.sqrt(0.42))
    assert [(c.card, round(c.push, 4)) for c in push.cards] == [('dimension 1', 0.3858), ('dimension 3', 0.2469), ('dimension 2', 0.0154)]
    assert np.isclose(sum(c.push for c in push.cards), push.distance)

def test_identical_averages_have_nothing_to_separate_them() -> None:
    space = lists_space([(IZZET_CONTROL, deck(Island=60))])
    shares = np.array([0.5, 0.5, 0, 0, 0])
    push = build_push(space, shares, shares)
    assert push.distance == 0
    assert [(c.card, c.alignment, c.push) for c in push.cards] == [('Island', 0, 0), ('Mountain', 0, 0)]
