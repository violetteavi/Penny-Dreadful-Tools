from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class Provenance(Enum):
    VALIDATED_GUESS = 'validated_guess'  # A person kept the automatic guess before it.
    CORRECTED_GUESS = 'corrected_guess'  # A person changed the automatic guess before it.
    PERSON_DIRECT = 'person_direct'  # A person labelled it with no automatic guess immediately before.
    AUTOMATIC = 'automatic'  # The latest label is an automatic guess nobody has reviewed.
    NO_HISTORY = 'no_history'  # The deck predates the label history.

HUMAN_PROVENANCES = frozenset({Provenance.VALIDATED_GUESS, Provenance.CORRECTED_GUESS, Provenance.PERSON_DIRECT})

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
    previous = history[-2] if len(history) > 1 else None
    if previous is None or previous.by_person:
        return LabelSource(Provenance.PERSON_DIRECT, None, latest.archetype_id)
    provenance = Provenance.VALIDATED_GUESS if previous.archetype_id == latest.archetype_id else Provenance.CORRECTED_GUESS
    return LabelSource(provenance, previous.archetype_id, latest.archetype_id)
