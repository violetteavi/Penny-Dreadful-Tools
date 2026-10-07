from dataclasses import asdict

import pytest

from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import BASE, MASKED, RECIPES, TextRecipe, build_card_text, build_masked_text

REBUKE_TEXT = 'This spell costs {3} less to cast if it targets a tapped creature.\nDestroy target creature.'


def instant(name: str, mana_cost: str, cmc: float, oracle_text: str) -> Card:
    return Card(name, 'normal', (Face(name, mana_cost, cmc, 'Instant', oracle_text),))


# Scenario: functional reprints get the same representation (Scenarios.md, "Card representation").

def test_the_four_removal_reprints_get_identical_text() -> None:
    names = ["Ajani's Response", 'Grounded for Life', 'Seized from Slumber', 'Luminous Rebuke']
    texts = {build_card_text(instant(n, '{4}{W}', 5, REBUKE_TEXT), BASE) for n in names}
    assert texts == {'Instant\n' + REBUKE_TEXT}

def test_the_three_mana_elves_get_identical_text_in_every_arm() -> None:
    elves = [Card(n, 'normal', (Face(n, '{G}', 1, 'Creature — Elf Druid', '{T}: Add {G}.', '1', '1'),)) for n in ('Llanowar Elves', 'Elvish Mystic', 'Fyndhorn Elves')]
    for recipe in RECIPES.values():
        assert len({build_card_text(e, recipe) for e in elves}) == 1

def test_a_basic_land_keeps_its_reminder_text() -> None:
    forest = Card('Forest', 'normal', (Face('Forest', '', 0, 'Basic Land — Forest', '({T}: Add {G}.)'),))
    assert build_card_text(forest, BASE) == 'Basic Land — Forest\n({T}: Add {G}.)'

KUMANO = Card('Kumano Faces Kakkazan', 'transform', (
    Face('Kumano Faces Kakkazan', '{R}', 1, 'Enchantment — Saga',
         '(As this Saga enters and after your draw step, add a lore counter.)\n'
         'I — This Saga deals 1 damage to each opponent and each planeswalker they control.\n'
         'II — When you next cast a creature spell this turn, that creature enters with an additional +1/+1 counter on it.\n'
         'III — Exile this Saga, then return it to the battlefield transformed under your control.'),
    Face('Etching of Kumano', '', 1, 'Enchantment Creature — Human Shaman',
         'Haste\nIf a creature dealt damage this turn by a source you controlled would die, exile it instead.', '2', '2')))

def test_a_double_faced_card_joins_its_faces_in_order() -> None:
    assert build_card_text(KUMANO, BASE) == ('Enchantment — Saga\n' + KUMANO.faces[0].oracle_text + '\n//\n'
                                             'Enchantment Creature — Human Shaman\n' + KUMANO.faces[1].oracle_text)


def vanilla(name: str, mana_cost: str, cmc: float, type_line: str, power: str, toughness: str) -> Card:
    return Card(name, 'normal', (Face(name, mana_cost, cmc, type_line, '', power, toughness),))

PLATED_SEASTRIDER = vanilla('Plated Seastrider', '{U}{U}', 2, 'Creature — Beast', '1', '4')
KALONIAN_TUSKER = vanilla('Kalonian Tusker', '{G}{G}', 2, 'Creature — Beast', '3', '3')
GARRUKS_GOREHORN = vanilla("Garruk's Gorehorn", '{4}{G}', 5, 'Creature — Beast', '7', '3')


# Scenario: vanilla creatures differ only in cost, stats and type line (Scenarios.md, "Card representation").

def test_in_the_base_and_masked_formats_the_three_vanilla_beasts_are_just_their_type_line() -> None:
    for recipe in (BASE, MASKED):
        assert {build_card_text(c, recipe) for c in (PLATED_SEASTRIDER, KALONIAN_TUSKER, GARRUKS_GOREHORN)} == {'Creature — Beast'}

SHOCK = instant('Shock', '{R}', 1, 'Shock deals 2 damage to any target.')
BURST_LIGHTNING = instant('Burst Lightning', '{R}', 1, 'Kicker {4} (You may pay an additional {4} as you cast this spell.)\n'
                                                       'Burst Lightning deals 2 damage to any target. If this spell was kicked, it deals 4 damage instead.')


# Scenario: a card's name in its own text doesn't push it away from its peers (Scenarios.md, "Card representation").

def test_the_masked_arm_writes_tilde_for_the_cards_own_name() -> None:
    assert build_card_text(SHOCK, MASKED) == 'Instant\n~ deals 2 damage to any target.'
    assert build_card_text(BURST_LIGHTNING, MASKED) == ('Instant\nKicker {4} (You may pay an additional {4} as you cast this spell.)\n'
                                                        '~ deals 2 damage to any target. If this spell was kicked, it deals 4 damage instead.')

def test_the_base_arm_leaves_the_name_in() -> None:
    assert build_card_text(SHOCK, BASE) == 'Instant\nShock deals 2 damage to any target.'

def test_a_possessive_is_masked_and_the_rest_of_the_word_kept() -> None:
    temple = Card('Wayfaring Temple', 'normal', (Face('Wayfaring Temple', '{1}{G}{W}', 3, 'Creature — Elemental',
                  "Wayfaring Temple's power and toughness are each equal to the number of creatures you control.", '*', '*'),))
    assert build_card_text(temple, MASKED) == "Creature — Elemental\n~'s power and toughness are each equal to the number of creatures you control."

def test_a_legendarys_short_name_is_masked_and_reported_for_the_spot_check() -> None:
    odric = Face('Odric, Master Tactician', '{2}{W}{W}', 4, 'Legendary Creature — Human Soldier',
                 'First strike\nWhenever Odric and at least three other creatures attack, you choose which creatures block this combat and how those creatures block.', '3', '4')
    assert build_masked_text(odric) == ('First strike\nWhenever ~ and at least three other creatures attack, you choose which creatures block this combat and how those creatures block.',
                                        ('Odric',))

def test_the_name_is_matched_case_sensitively_as_a_whole_word() -> None:
    fly = Face('Fly', '{U}', 1, 'Enchantment — Aura', 'Enchant creature\nEnchanted creature has flying and "Whenever this creature deals combat damage to a player, '
               'venture into the dungeon." (Enter the first room or advance to the next room.)')
    assert build_masked_text(fly) == (fly.oracle_text, ())  # "flying" stays.

def test_a_short_name_is_masked_only_on_a_legendary() -> None:
    nivix = Face('Nivix, Aerie of the Firemind', '', 0, 'Land', "{T}: Add {C}.\n{2}{U}{R}, {T}: Exile the top card of your library. Until your next turn, you may cast it if it's an instant or sorcery spell.")
    assert build_masked_text(nivix) == (nivix.oracle_text, ())

def test_each_face_is_masked_against_its_own_name() -> None:
    huntmaster = Card('Huntmaster of the Fells', 'transform', (
        Face('Huntmaster of the Fells', '{2}{R}{G}', 4, 'Creature — Human Werewolf',
             'Whenever this creature enters or transforms into Huntmaster of the Fells, create a 2/2 green Wolf creature token and you gain 2 life.\n'
             'At the beginning of each upkeep, if no spells were cast last turn, transform this creature.', '2', '2'),
        Face('Ravager of the Fells', '', 4, 'Creature — Werewolf',
             "Trample\nWhenever this creature transforms into Ravager of the Fells, it deals 2 damage to target opponent or planeswalker and 2 damage to up to "
             "one target creature that player or that planeswalker's controller controls.\n"
             'At the beginning of each upkeep, if a player cast two or more spells last turn, transform this creature.', '4', '4')))
    front, back = build_card_text(huntmaster, MASKED).split('\n//\n')
    assert 'transforms into ~, create' in front and 'Fells' not in front
    assert 'transforms into ~, it deals' in back and 'Fells' not in back


# Scenario: reprints whose text names the card are identical when masked (Scenarios.md, "Card representation").

def test_lightning_strike_and_searing_spear_are_identical_when_masked() -> None:
    strike = instant('Lightning Strike', '{1}{R}', 2, 'Lightning Strike deals 3 damage to any target.')
    spear = instant('Searing Spear', '{1}{R}', 2, 'Searing Spear deals 3 damage to any target.')
    assert build_card_text(strike, BASE) != build_card_text(spear, BASE)
    assert build_card_text(strike, MASKED) == build_card_text(spear, MASKED) == 'Instant\n~ deals 3 damage to any target.'


# The formats: base and masked. Others tried in #7 are on the archive tag; asking for one fails and says where it went.

def test_the_formats_are_base_and_masked() -> None:
    assert {label: r.label for label, r in RECIPES.items()} == {'base': 'base', 'masked': 'masked'}

def test_a_formats_manifest_shape_is_unchanged_so_saved_files_still_merge() -> None:
    assert asdict(BASE) == {'style': 'plain', 'mask': False} and asdict(MASKED) == {'style': 'plain', 'mask': True}

@pytest.mark.parametrize('style', ['json', 'stats', 'labels'])
def test_a_removed_format_fails_and_points_to_the_archive_tag(style: str) -> None:
    with pytest.raises(ValueError, match=f"The '{style}' format was removed after #7; it is on the tag card-encoder-exploration"):
        TextRecipe(style, mask=True)  # type: ignore[arg-type]
