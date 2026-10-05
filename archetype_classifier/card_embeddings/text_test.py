from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import BASE, STATS, build_card_text

REBUKE_TEXT = 'This spell costs {3} less to cast if it targets a tapped creature.\nDestroy target creature.'


def instant(name: str, mana_cost: str, cmc: float, oracle_text: str) -> Card:
    return Card(name, 'normal', (Face(name, mana_cost, cmc, 'Instant', oracle_text),))


# Scenario: functional reprints get the same representation (Scenarios.md, "Card representation").

def test_the_four_removal_reprints_get_identical_text() -> None:
    names = ["Ajani's Response", 'Grounded for Life', 'Seized from Slumber', 'Luminous Rebuke']
    texts = {build_card_text(instant(n, '{4}{W}', 5, REBUKE_TEXT), BASE) for n in names}
    assert texts == {'Instant\n' + REBUKE_TEXT}

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
