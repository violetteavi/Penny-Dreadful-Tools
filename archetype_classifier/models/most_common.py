"""A mock model: it always guesses the most common archetype among its training decks. The simplest real model to store, and a floor every later model should beat."""
from collections import Counter
from collections.abc import Sequence
from typing import ClassVar

from archetype_classifier.evaluation.model import JSON, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, register


@register
class MostCommonArchetype:
    name: ClassVar[str] = 'most common archetype'
    version: ClassVar[int] = 1

    def __init__(self, params: dict[str, JSON]) -> None:
        self.params = params
        self.archetype_id: int | None = None
        self.with_archetype = 0
        self.training_decks = 0

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        counts = Counter(d.archetype_id for d in training if d.archetype_id is not None)
        self.training_decks = len(training)
        if counts:  # The most decks wins; a tie goes to the lower archetype id, so refitting gives the same guess.
            self.archetype_id, self.with_archetype = min(counts.items(), key=lambda item: (-item[1], item[0]))

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]:
        evidence: dict[str, JSON] = {'training_decks_with_archetype': self.with_archetype, 'training_decks': self.training_decks}
        return [Prediction(d.deck_id, self.archetype_id, evidence) for d in decks]

    def state(self) -> dict[str, JSON]:
        return {'archetype_id': self.archetype_id, 'training_decks_with_archetype': self.with_archetype, 'training_decks': self.training_decks}

    @classmethod
    def from_state(cls, params: dict[str, JSON], state: dict[str, JSON], training: Sequence[TrainingDeck], context: FitContext) -> 'MostCommonArchetype':
        raise NotImplementedError
