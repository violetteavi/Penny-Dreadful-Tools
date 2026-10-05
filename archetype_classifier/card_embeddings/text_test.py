from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import BASE, build_card_text

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
