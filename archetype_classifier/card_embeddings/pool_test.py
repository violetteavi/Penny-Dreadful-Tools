import pytest

from archetype_classifier.card_embeddings.pool import Card, Face, SiteCard, build_card_pool

SHOCK = Face('Shock', '{R}', 1, 'Instant', 'Shock deals 2 damage to any target.')
DISCOVERY = Face('Discovery', '{1}{U/B}', 2, 'Sorcery', 'Surveil 2, then draw a card. (To surveil 2, look at the top two cards of your library, then put any number of '
                                                       'them into your graveyard and the rest on top of your library in any order.)')
DISPERSAL = Face('Dispersal', '{3}{U}{B}', 5, 'Instant', "Each opponent returns a nonland permanent they control with the greatest mana value among permanents they "
                                                         "control to its owner's hand, then discards a card.")
TAZEEM = Face('Tazeem', '', 0, 'Plane — Zendikar', "Creatures can't block.\nWhenever chaos ensues, draw a card for each land you control.")

SITE_CARDS = [SiteCard(99, 'Shock', 'normal'), SiteCard(20430, 'Discovery // Dispersal', 'split'), SiteCard(1234, 'Tazeem', 'planar')]
FACES = {99: (SHOCK,), 20430: (DISCOVERY, DISPERSAL), 1234: (TAZEEM,)}


def test_each_legal_card_gets_its_site_name_layout_faces_in_order_and_legal_seasons() -> None:
    pool = build_card_pool({'Shock': frozenset({39, 43}), 'Discovery // Dispersal': frozenset({41})}, SITE_CARDS, FACES)
    assert pool == [Card('Discovery // Dispersal', 'split', (DISCOVERY, DISPERSAL), frozenset({41})),
                    Card('Shock', 'normal', (SHOCK,), frozenset({39, 43}))]

def test_a_non_game_card_is_left_out() -> None:
    assert build_card_pool({'Tazeem': frozenset({1}), 'Shock': frozenset({1})}, SITE_CARDS, FACES) == [Card('Shock', 'normal', (SHOCK,), frozenset({1}))]

def test_a_legal_name_the_cards_database_doesnt_have_is_skipped_with_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    assert build_card_pool({'Shock': frozenset({1}), 'Lightning Bolt': frozenset({1})}, SITE_CARDS, FACES) == [Card('Shock', 'normal', (SHOCK,), frozenset({1}))]
    assert 'Skipped 1 legal card the cards database lacks: Lightning Bolt' in caplog.text
