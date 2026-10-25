"""Card specificity (#62): how tied a card is to one label, on its own."""
import pytest

from archetype_classifier.geometry.space import build_presence
from archetype_classifier.geometry.space_test import deck, lists_space
from archetype_classifier.geometry.specificity import build_label_concentration


def test_label_concentration_is_the_share_of_a_cards_rows_with_its_most_common_label() -> None:
    space = lists_space([(1, deck(Shock=4, Mountain=56)), (1, deck(Shock=2, Mountain=58)), (2, deck(Shock=4, Island=56))])
    presence = build_presence(space)
    assert presence.cards == ('Island', 'Mountain', 'Shock')
    assert build_label_concentration(presence, space.rows.labels).tolist() == pytest.approx([1, 1, 2 / 3])  # Shock: 2 of its 3 rows are label 1.
