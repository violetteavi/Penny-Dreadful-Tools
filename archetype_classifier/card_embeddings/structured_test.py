import pytest

from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.structured import STRUCTURED_COLUMNS, build_structured_vector


def single(name: str, mana_cost: str, cmc: float, type_line: str, power: str | None = None, toughness: str | None = None, loyalty: str | None = None) -> Card:
    return Card(name, 'normal', (Face(name, mana_cost, cmc, type_line, '', power, toughness, loyalty),))

def front(card: Card) -> dict[str, float]:
    """The front block's non-zero columns, keyed without the 'front.' prefix."""
    return {c.removeprefix('front.'): v for c, v in zip(STRUCTURED_COLUMNS, build_structured_vector(card)) if c.startswith('front.') and v}

def stat(card: Card, block: str, name: str) -> tuple[float, float, float]:
    values = dict(zip(STRUCTURED_COLUMNS, build_structured_vector(card)))
    return values[f'{block}.{name}.present'], values[f'{block}.{name}.value'], values[f'{block}.{name}.variable']

DISTRESS = single('Distress', '{B}{B}', 2, 'Sorcery')
ORNITHOPTER = single('Ornithopter', '{0}', 0, 'Artifact Creature — Thopter', '0', '2')
WAYFARING_TEMPLE = single('Wayfaring Temple', '{1}{G}{W}', 3, 'Creature — Elemental', '*', '*')
JAYA_BALLARD = single('Jaya Ballard', '{2}{R}{R}{R}', 5, 'Legendary Planeswalker — Jaya', loyalty='5')


# Scenario: missing stats are absent, not zero (Scenarios.md, "Card representation").

@pytest.mark.parametrize(('card', 'power', 'toughness', 'loyalty'), [
    (DISTRESS, (0, 0, 0), (0, 0, 0), (0, 0, 0)),
    (ORNITHOPTER, (1, 0, 0), (1, 2, 0), (0, 0, 0)),
    (WAYFARING_TEMPLE, (1, 0, 1), (1, 0, 1), (0, 0, 0)),
    (JAYA_BALLARD, (0, 0, 0), (0, 0, 0), (1, 5, 0)),
])
def test_each_stat_is_present_value_and_variable(card: Card, power: tuple[int, int, int], toughness: tuple[int, int, int], loyalty: tuple[int, int, int]) -> None:
    assert (stat(card, 'front', 'power'), stat(card, 'front', 'toughness'), stat(card, 'front', 'loyalty')) == (power, toughness, loyalty)

def test_a_sorcerys_absent_power_never_equals_a_real_zero_power() -> None:
    assert stat(DISTRESS, 'front', 'power') != stat(ORNITHOPTER, 'front', 'power')

@pytest.mark.parametrize(('card', 'expected'), [
    (DISTRESS, {'mana_value': 2, 'pips.B': 2, 'type.Sorcery': 1}),
    (ORNITHOPTER, {'type.Artifact': 1, 'type.Creature': 1, 'toughness.present': 1, 'toughness.value': 2, 'power.present': 1}),
    (WAYFARING_TEMPLE, {'mana_value': 3, 'generic': 1, 'pips.G': 1, 'pips.W': 1, 'type.Creature': 1,
                        'power.present': 1, 'power.variable': 1, 'toughness.present': 1, 'toughness.variable': 1}),
    (JAYA_BALLARD, {'mana_value': 5, 'generic': 2, 'pips.R': 3, 'supertype.Legendary': 1, 'type.Planeswalker': 1, 'loyalty.present': 1, 'loyalty.value': 5}),
])
def test_the_front_block_holds_cost_types_and_stats(card: Card, expected: dict[str, float]) -> None:
    assert front(card) == expected


def block(card: Card, name: str) -> dict[str, float]:
    return {c.removeprefix(f'{name}.'): v for c, v in zip(STRUCTURED_COLUMNS, build_structured_vector(card)) if c.startswith(f'{name}.') and v}

WESTVALE_ABBEY = Card('Westvale Abbey', 'transform', (Face('Westvale Abbey', '', 0, 'Land', ''),
                                                      Face('Ormendahl, Profane Prince', '', 0, 'Legendary Creature — Demon', '', '9', '7')))
DISCOVERY = Card('Discovery // Dispersal', 'split', (Face('Discovery', '{1}{U/B}', 2, 'Sorcery', ''), Face('Dispersal', '{3}{U}{B}', 5, 'Instant', '')))

def test_a_double_faced_cards_back_face_fills_the_back_block() -> None:
    assert block(WESTVALE_ABBEY, 'front') == {'type.Land': 1}
    assert block(WESTVALE_ABBEY, 'back') == {'supertype.Legendary': 1, 'type.Creature': 1, 'power.present': 1, 'power.value': 9,
                                              'toughness.present': 1, 'toughness.value': 7}
    assert block(WESTVALE_ABBEY, 'layout') == {'transform': 1}

def test_a_single_faced_cards_back_block_is_all_zeros() -> None:
    assert block(DISTRESS, 'back') == {}
    assert block(DISTRESS, 'layout') == {'normal': 1}

def test_a_split_cards_halves_fill_the_two_blocks_and_hybrid_mana_pays_for_both_colours() -> None:
    assert block(DISCOVERY, 'front') == {'mana_value': 2, 'generic': 1, 'hybrid': 1, 'pips.U': 1, 'pips.B': 1, 'type.Sorcery': 1}
    assert block(DISCOVERY, 'back') == {'mana_value': 5, 'generic': 3, 'pips.U': 1, 'pips.B': 1, 'type.Instant': 1}

@pytest.mark.parametrize(('card', 'expected'), [
    (single('Gut Shot', '{R/P}', 1, 'Instant'), {'mana_value': 1, 'phyrexian': 1, 'pips.R': 1, 'type.Instant': 1}),
    (single('Spectral Procession', '{2/W}{2/W}{2/W}', 6, 'Sorcery'), {'mana_value': 6, 'hybrid': 3, 'pips.W': 3, 'type.Sorcery': 1}),
    (single('Invasion of Ikoria', '{X}{G}{G}', 2, 'Battle — Siege'), {'mana_value': 2, 'x': 1, 'pips.G': 2, 'type.Battle': 1}),
    (single("Giant's Ire", '{3}{R}', 4, 'Kindred Sorcery — Giant'), {'mana_value': 4, 'generic': 3, 'pips.R': 1, 'type.Kindred': 1, 'type.Sorcery': 1}),
    (single("Giant's Ire", '{3}{R}', 4, 'Tribal Sorcery — Giant'), {'mana_value': 4, 'generic': 3, 'pips.R': 1, 'type.Kindred': 1, 'type.Sorcery': 1}),
])
def test_unusual_costs_and_types(card: Card, expected: dict[str, float]) -> None:
    assert front(card) == expected

@pytest.mark.parametrize(('card', 'power', 'toughness'), [
    (single('Impervious Greatwurm', '{7}{G}{G}{G}', 10, 'Creature — Wurm', '16', '16'), (1, 15, 0), (1, 15, 0)),  # Clipped at 15.
    (single('Spinal Parasite', '{5}', 5, 'Artifact Creature — Insect', '-1', '-1'), (1, -1, 0), (1, -1, 0)),
    (single('Tarmogoyf', '{1}{G}', 2, 'Creature — Lhurgoyf', '*', '1+*'), (1, 0, 1), (1, 1, 1)),
])
def test_large_negative_and_partly_variable_stats(card: Card, power: tuple[int, int, int], toughness: tuple[int, int, int]) -> None:
    assert (stat(card, 'front', 'power'), stat(card, 'front', 'toughness')) == (power, toughness)

def test_a_card_with_more_than_two_faces_uses_the_first_two_and_warns(caplog: pytest.LogCaptureFixture) -> None:
    names = ('Who', 'What', 'When', 'Where', 'Why')
    card = Card(' // '.join(names), 'split', tuple(Face(n, '{1}{W}', 2, 'Instant', '') for n in names))
    assert len(build_structured_vector(card)) == len(STRUCTURED_COLUMNS)
    assert 'Who // What // When // Where // Why has 5 faces' in caplog.text
