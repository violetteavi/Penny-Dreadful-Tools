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
