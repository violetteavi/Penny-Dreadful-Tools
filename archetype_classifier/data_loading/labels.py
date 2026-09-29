from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class Provenance(Enum):
    CORRECTED_GUESS = 'corrected_guess'  # A person changed the automatic guess before it.
    AUTOMATIC = 'automatic'  # The latest label is an automatic guess nobody has reviewed.
    NO_HISTORY = 'no_history'  # The deck predates the label history.

HUMAN_PROVENANCES = frozenset({Provenance.CORRECTED_GUESS})

@dataclass(frozen=True)
class LabelChange:
    deck_id: int
    archetype_id: int
    by_person: bool

@dataclass(frozen=True)
class LabelSource:
    provenance: Provenance
    guess_archetype_id: int | None  # The automatic guess a person reviewed, if there was one.
    latest_archetype_id: int | None  # The latest archetype in the label history.

def label_source(history: Sequence[LabelChange]) -> LabelSource:
    """Where a deck's latest label came from. `history` is that deck's label changes, oldest first."""
    if not history:
        return LabelSource(Provenance.NO_HISTORY, None, None)
    latest = history[-1]
    if not latest.by_person:
        return LabelSource(Provenance.AUTOMATIC, None, latest.archetype_id)
    previous = history[-2]
    return LabelSource(Provenance.CORRECTED_GUESS, previous.archetype_id, latest.archetype_id)
