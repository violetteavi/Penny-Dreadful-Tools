"""Which training rows a deck is diffed against (#62)."""
import pytest

from archetype_classifier.geometry.pairs import build_match_row
from archetype_classifier.models.embedding_nearest import build_training_rows
from archetype_classifier.models.embedding_nearest_test import MONO_RED_SWARM, RED_DECK_WINS, TRAINING

ROWS = build_training_rows(TRAINING)  # Maindeck A as Red Deck Wins (decks 101 and 103) and as Mono Red Swarm (105); maindeck B as Azorius Control (107).


def test_a_stored_match_is_the_row_of_its_newest_deck_under_the_guessed_label() -> None:
    assert build_match_row(ROWS, 103, RED_DECK_WINS) == 0
    assert build_match_row(ROWS, 105, MONO_RED_SWARM) == 1

def test_a_match_with_no_such_row_is_refused() -> None:
    with pytest.raises(ValueError, match='No training row with newest deck 105 under label 16'):
        build_match_row(ROWS, 105, RED_DECK_WINS)
