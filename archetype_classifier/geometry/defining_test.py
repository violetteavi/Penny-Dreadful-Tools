"""Defining cards and centroid pushes (Scenarios.md, "Archetype geometry")."""
import numpy as np

from archetype_classifier.geometry.defining import build_ranked_cards

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
