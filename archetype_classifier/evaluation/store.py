"""The model and run store, in the experiments database. Models are saved as their record and what fitting learned, runs as one guess per deck; never decks, never scores."""
import hashlib
from collections.abc import Sequence

from archetype_classifier.evaluation.model import Prediction


def prediction_hash(predictions: Sequence[Prediction]) -> str:
    """A fingerprint of a run's guesses: every deck and its guess, in any order. Evidence is left out, since scores depend only on guesses."""
    pairs = sorted((p.deck_id, -1 if p.guess_id is None else p.guess_id) for p in predictions)
    return hashlib.sha1(';'.join(f'{deck_id}:{guess_id}' for deck_id, guess_id in pairs).encode()).hexdigest()
