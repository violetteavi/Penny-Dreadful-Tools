from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import BASE, MASKED, STATS, build_card_text, build_masked_text

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
    for recipe in (BASE, STATS, MASKED):
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

def test_in_the_base_arm_the_three_vanilla_beasts_are_just_their_type_line() -> None:
    assert {build_card_text(c, BASE) for c in (PLATED_SEASTRIDER, KALONIAN_TUSKER, GARRUKS_GOREHORN)} == {'Creature — Beast'}

def test_the_stats_arm_puts_cost_and_stats_first_so_the_beasts_differ() -> None:
    assert build_card_text(PLATED_SEASTRIDER, STATS) == '{U}{U} · Creature — Beast · 1/4'
    assert build_card_text(KALONIAN_TUSKER, STATS) == '{G}{G} · Creature — Beast · 3/3'
    assert build_card_text(GARRUKS_GOREHORN, STATS) == '{4}{G} · Creature — Beast · 7/3'

def test_the_stats_arm_leaves_out_what_a_face_doesnt_have() -> None:
    jaya = Card('Jaya Ballard', 'normal', (Face('Jaya Ballard', '{2}{R}{R}{R}', 5, 'Legendary Planeswalker — Jaya', '+1: …', loyalty='5'),))
    land = Card('Forest', 'normal', (Face('Forest', '', 0, 'Basic Land — Forest', '({T}: Add {G}.)'),))
    assert build_card_text(jaya, STATS) == '{2}{R}{R}{R} · Legendary Planeswalker — Jaya · Loyalty 5\n+1: …'
    assert build_card_text(land, STATS) == 'Basic Land — Forest\n({T}: Add {G}.)'
    assert build_card_text(KUMANO, STATS).split('\n//\n')[1].startswith('Enchantment Creature — Human Shaman · 2/2\n')


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

def test_a_name_inside_a_longer_word_is_left_alone() -> None:
    assert build_masked_text(Face('Shock', '{R}', 1, 'Instant', 'Shockwave and Shocked stay; Shock goes.')) == ('Shockwave and Shocked stay; ~ goes.', ())

def test_a_short_name_is_masked_only_on_a_legendary() -> None:
    assert build_masked_text(Face('Will, the Wise', '{U}', 1, 'Creature — Human', 'Will draw.')) == ('Will draw.', ())

def test_each_face_is_masked_against_its_own_name() -> None:
    ikoria = Card('Invasion of Ikoria', 'transform', (
        Face('Invasion of Ikoria', '{X}{G}{G}', 2, 'Battle — Siege', 'When this Siege enters, search for Zilortha.'),
        Face('Zilortha, Apex of Ikoria', '', 2, 'Legendary Creature — Dinosaur', 'Zilortha attacks. Invasion of Ikoria stays.', '8', '8')))
    assert build_card_text(ikoria, MASKED) == ('Battle — Siege\nWhen this Siege enters, search for Zilortha.\n//\n'
                                               'Legendary Creature — Dinosaur\n~ attacks. Invasion of Ikoria stays.')
