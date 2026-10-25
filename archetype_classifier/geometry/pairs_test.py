"""Which training rows a deck is diffed against (#62)."""
import numpy as np
import pytest

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.geometry.pairs import PairClass, build_match_row, build_near_rivals, build_pair_class
from archetype_classifier.geometry.tree_test import (ACTUAL_TWIN, AGGRO, AZORIUS_CONTROL, COMBO, CONTROL, FAMILY_TREE, IZZET_CONTROL, IZZET_TWIN,
                                                     RED_DECK_WINS)
from archetype_classifier.models.embedding_nearest import build_training_rows
from archetype_classifier.models.embedding_nearest_test import MONO_RED_SWARM, RED_DECK_WINS, TRAINING, training

ROWS = build_training_rows(TRAINING)  # Maindeck A as Red Deck Wins (decks 101 and 103) and as Mono Red Swarm (105); maindeck B as Azorius Control (107).


def test_a_stored_match_is_the_row_of_its_newest_deck_under_the_guessed_label() -> None:
    assert build_match_row(ROWS, 103, RED_DECK_WINS) == 0
    assert build_match_row(ROWS, 105, MONO_RED_SWARM) == 1

def test_a_match_with_no_such_row_is_refused() -> None:
    with pytest.raises(ValueError, match='No training row with newest deck 105 under label 16'):
        build_match_row(ROWS, 105, RED_DECK_WINS)


# How two labels are related. FAMILY_TREE, plus Temur Ascendancy under Combo: Izzet Twin's cousin through Actual Twin.

TEMUR_ASCENDANCY = 2001
COUSINS = ArchetypeTree({**FAMILY_TREE.archetypes, TEMUR_ASCENDANCY: ArchetypeSnapshot(TEMUR_ASCENDANCY, 'Temur Ascendancy', COMBO, 1)})

@pytest.mark.parametrize(('deck_label', 'row_label', 'pair_class'), [
    (IZZET_CONTROL, IZZET_CONTROL, PairClass.SAME),
    (IZZET_CONTROL, AZORIUS_CONTROL, PairClass.SIBLING),
    (ACTUAL_TWIN, TEMUR_ASCENDANCY, PairClass.SIBLING),
    (IZZET_TWIN, TEMUR_ASCENDANCY, PairClass.SAME_BRANCH),
    (CONTROL, IZZET_CONTROL, PairClass.ANCESTOR_DESCENDANT),
    (IZZET_TWIN, COMBO, PairClass.ANCESTOR_DESCENDANT),  # A grandparent too.
    (RED_DECK_WINS, IZZET_CONTROL, PairClass.UNRELATED),
    (CONTROL, AGGRO, PairClass.UNRELATED),  # Two top-level archetypes aren't siblings.
])
def test_two_labels_fall_in_exactly_one_class(deck_label: int, row_label: int, pair_class: PairClass) -> None:
    assert build_pair_class(COUSINS, deck_label, row_label) == pair_class


# Near rivals: the best row of each of the best-scoring other archetypes. Nine rows, each a distinct list, labelled:
LABELS = [1, 1, 2, 3, 4, 5, 6, 7, 2]
SIMILARITIES = np.array([1.0, 0.9, 0.8, 0.7, 0.95, 0.6, 0.5, 0.4, 0.85])
SPREAD = build_training_rows([training(i + 1, label, (CardCount('Mountain', 50 + i),)) for i, label in enumerate(LABELS)])

def test_near_rivals_are_the_best_rows_of_the_best_other_archetypes() -> None:
    assert build_near_rivals(SIMILARITIES, SPREAD, label_id=1) == [4, 8, 3, 5, 6]  # Labels 4, 2 (its better row), 3, 5 and 6; never its own label.
