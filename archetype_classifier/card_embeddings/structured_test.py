import math

import pytest

from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.structured import ABSENT, CardNumbers, Scalar, build_card_numbers, build_front_numbers


def single(name: str, mana_cost: str, cmc: float, type_line: str, power: str | None = None, toughness: str | None = None, loyalty: str | None = None) -> Card:
    return Card(name, 'normal', (Face(name, mana_cost, cmc, type_line, '', power, toughness, loyalty),))

DISTRESS = single('Distress', '{B}{B}', 2, 'Sorcery')
ORNITHOPTER = single('Ornithopter', '{0}', 0, 'Artifact Creature — Thopter', '0', '2')
KALONIAN_TUSKER = single('Kalonian Tusker', '{G}{G}', 2, 'Creature — Beast', '3', '3')
SPINAL_PARASITE = single('Spinal Parasite', '{5}', 5, 'Artifact Creature — Insect', '-1', '-1')
LHURGOYF = single('Lhurgoyf', '{2}{G}{G}', 4, 'Creature — Lhurgoyf', '*', '1+*')
DISCOVERY = Card('Discovery // Dispersal', 'split', (Face('Discovery', '{1}{U/B}', 2, 'Sorcery', ''), Face('Dispersal', '{3}{U}{B}', 5, 'Instant', '')))


# Scenario: missing stats are absent, not zero (Scenarios.md, "Card representation").

def test_a_sorcerys_absent_power_never_equals_a_real_zero_power() -> None:
    assert build_card_numbers(DISTRESS).power == ABSENT
    assert build_card_numbers(ORNITHOPTER).power == Scalar(True, False, 0)


# Scenario: vanilla creatures differ only in cost, stats and type line (Scenarios.md, "Card representation").

def test_the_numbers_tell_the_five_vanilla_creatures_apart() -> None:
    vanillas = [single('Plated Seastrider', '{U}{U}', 2, 'Creature — Beast', '1', '4'), KALONIAN_TUSKER,
                single("Garruk's Gorehorn", '{4}{G}', 5, 'Creature — Beast', '7', '3'), single('Coral Eel', '{1}{U}', 2, 'Creature — Fish', '2', '1'),
                single('Spined Wurm', '{4}{G}', 5, 'Creature — Wurm', '5', '4')]
    assert len({build_card_numbers(c) for c in vanillas}) == 5


# A card's front-face numbers: mana value, power, toughness and loyalty as (present, variable, fixed), and colours, from the front face only, except that
# a split card sums both halves' mana values and takes both halves' colours.

LIGHTNING_STRIKE = single('Lightning Strike', '{1}{R}', 2, 'Instant')
FIREBALL = single('Fireball', '{X}{R}', 1, 'Sorcery')
FOREST = single('Forest', '', 0, 'Basic Land — Forest')
SHAPESHIFTER = single('Shapeshifter', '{6}', 6, 'Artifact Creature — Shapeshifter', '*', '7-*')
SOULS_OF_THE_LOST = single('Souls of the Lost', '{1}{B}', 2, 'Creature — Spirit', '*', '*+1')
NISSA = single('Nissa, Steward of Elements', '{X}{G}{U}', 2, 'Legendary Planeswalker — Nissa', loyalty='X')
JACE = single('Jace, Wielder of Mysteries', '{1}{U}{U}{U}', 4, 'Legendary Planeswalker — Jace', loyalty='4')
FIRE_ICE = Card('Fire // Ice', 'split', (Face('Fire', '{1}{R}', 2, 'Instant', ''), Face('Ice', '{1}{U}', 2, 'Instant', '')))
HUNTMASTER = Card('Huntmaster of the Fells', 'transform', (Face('Huntmaster of the Fells', '{2}{R}{G}', 4, 'Creature — Human Werewolf', '', '2', '2'),
                                                           Face('Ravager of the Fells', '', 4, 'Creature — Werewolf', '', '4', '4')))

@pytest.mark.parametrize(('card', 'expected'), [
    (LIGHTNING_STRIKE, CardNumbers(Scalar(True, False, 2), ABSENT, ABSENT, ABSENT, frozenset('R'))),
    (ORNITHOPTER, CardNumbers(Scalar(True, False, 0), Scalar(True, False, 0), Scalar(True, False, 2), ABSENT, frozenset())),
    (FIREBALL, CardNumbers(Scalar(True, True, 1), ABSENT, ABSENT, ABSENT, frozenset('R'))),
    (LHURGOYF, CardNumbers(Scalar(True, False, 4), Scalar(True, True, 0), Scalar(True, True, 1), ABSENT, frozenset('G'))),
    (FOREST, CardNumbers(ABSENT, ABSENT, ABSENT, ABSENT, frozenset())),
    (SHAPESHIFTER, CardNumbers(Scalar(True, False, 6), Scalar(True, True, 0), Scalar(True, True, 7, -1), ABSENT, frozenset())),
    (SOULS_OF_THE_LOST, CardNumbers(Scalar(True, False, 2), Scalar(True, True, 0), Scalar(True, True, 1), ABSENT, frozenset('B'))),
    (NISSA, CardNumbers(Scalar(True, True, 2), ABSENT, ABSENT, Scalar(True, True, 0), frozenset('GU'))),
    (JACE, CardNumbers(Scalar(True, False, 4), ABSENT, ABSENT, Scalar(True, False, 4), frozenset('U'))),
    (SPINAL_PARASITE, CardNumbers(Scalar(True, False, 5), Scalar(True, False, -1), Scalar(True, False, -1), ABSENT, frozenset())),
])
def test_a_cards_front_numbers(card: Card, expected: CardNumbers) -> None:
    assert build_card_numbers(card) == expected

def test_a_split_card_sums_both_halves_mana_values_and_takes_both_colours() -> None:
    assert build_card_numbers(FIRE_ICE) == CardNumbers(Scalar(True, False, 4), ABSENT, ABSENT, ABSENT, frozenset('RU'))

def test_a_double_faced_card_uses_its_front_face_only() -> None:
    assert build_card_numbers(HUNTMASTER) == CardNumbers(Scalar(True, False, 4), Scalar(True, False, 2), Scalar(True, False, 2), ABSENT, frozenset('RG'))

def test_hybrid_and_phyrexian_symbols_count_towards_each_of_their_colours() -> None:
    assert build_card_numbers(DISCOVERY).colours == frozenset('UB')  # Discovery // Dispersal is split: {1}{U/B} and {3}{U}{B}.
    assert build_card_numbers(DISCOVERY).mana_value == Scalar(True, False, 7)
    assert build_card_numbers(single('Spined Thopter', '{2}{U/P}', 3, 'Artifact Creature — Phyrexian Thopter', '2', '1')).colours == frozenset('U')

def test_front_numbers_stack_every_card_in_order_with_log_values() -> None:
    numbers = build_front_numbers([LIGHTNING_STRIKE, KALONIAN_TUSKER, FOREST])
    assert numbers.names == ('Lightning Strike', 'Kalonian Tusker', 'Forest')
    assert numbers.present.tolist() == [[True, False, False, False], [True, True, True, False], [False, False, False, False]]
    assert numbers.log_values()[1].tolist() == pytest.approx([math.log(3), math.log(4), math.log(4), 0])
    assert numbers.colours.tolist() == [[0, 0, 0, 1, 0], [0, 0, 0, 0, 1], [0, 0, 0, 0, 0]]  # W U B R G.
