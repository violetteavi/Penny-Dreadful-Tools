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
