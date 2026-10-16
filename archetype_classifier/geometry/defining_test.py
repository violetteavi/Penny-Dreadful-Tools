"""Defining cards and centroid pushes (Scenarios.md, "Archetype geometry")."""
import numpy as np

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.defining import build_defining_cards, build_presence, build_ranked_cards, build_siblings, build_subtree
from archetype_classifier.geometry.space_test import deck, lists_space

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

CONTROL, AGGRO, IZZET_CONTROL, AZORIUS_CONTROL, RED_DECK_WINS = 1001, 1002, 65, 49, 16
TREE = ArchetypeTree({CONTROL: ArchetypeSnapshot(CONTROL, 'Control', None, 0), AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0),
                      IZZET_CONTROL: ArchetypeSnapshot(IZZET_CONTROL, 'Izzet Control', CONTROL, 1),
                      AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1)})
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


# Siblings: the other archetypes under the same parent, with their own children.

IZZET_TWIN, ACTUAL_TWIN, COMBO = 549, 557, 1003
FAMILY_TREE = ArchetypeTree({**TREE.archetypes, COMBO: ArchetypeSnapshot(COMBO, 'Combo', None, 0),
                             ACTUAL_TWIN: ArchetypeSnapshot(ACTUAL_TWIN, 'Actual Twin', COMBO, 1),
                             IZZET_TWIN: ArchetypeSnapshot(IZZET_TWIN, 'Izzet Twin', ACTUAL_TWIN, 2)})

def test_a_siblings_children_count_among_the_siblings() -> None:
    assert build_siblings(FAMILY_TREE, COMBO) == {CONTROL, IZZET_CONTROL, AZORIUS_CONTROL, AGGRO, RED_DECK_WINS}  # Top-level: the other top-level subtrees.
    assert build_siblings(FAMILY_TREE, IZZET_CONTROL) == {AZORIUS_CONTROL}
    assert build_subtree(FAMILY_TREE, COMBO) == {COMBO, ACTUAL_TWIN, IZZET_TWIN}

def test_an_only_child_has_no_sibling_contrast_and_no_defining_cards_against_it() -> None:
    space = lists_space([(IZZET_TWIN, deck(Shock=4, Island=56)), (ACTUAL_TWIN, deck(Shock=4, Mountain=56))])
    assert build_siblings(FAMILY_TREE, IZZET_TWIN) == frozenset()
    assert build_defining_cards(build_presence(space), space, FAMILY_TREE, IZZET_TWIN, 'siblings') == []
    assert [c.card for c in build_defining_cards(build_presence(space), space, FAMILY_TREE, IZZET_TWIN, 'all')] == ['Island']

def test_presence_counts_a_card_once_per_row_whatever_its_copies() -> None:
    space = lists_space([(IZZET_CONTROL, deck(Shock=4, Island=56)), (IZZET_CONTROL, deck(Shock=1, Island=59))])
    presence = build_presence(space)
    assert presence.cards == ('Island', 'Shock')
    assert presence.matrix.toarray().tolist() == [[1, 1], [1, 1]]
