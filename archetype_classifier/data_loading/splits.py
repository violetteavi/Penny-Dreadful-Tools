import zlib
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any


from archetype_classifier.data_loading.labels import LabelStatus


class Split(Enum):
    TRAIN = 'train'
    HELD_OUT = 'held_out'  # Held-out decklists from the training seasons.
    VALIDATION = 'validation'
    TEST = 'test'
    EXCLUDED = 'excluded'  # Neither trained on nor scored; the reason is recorded.

class ExclusionReason(Enum):
    RESERVED_SEASON = 'reserved season'
    STATUS_NOT_TRAINED_ON = 'status not used for training'
    STATUS_NOT_EVALUATED = 'status not used for evaluation'

@dataclass(frozen=True)
class SplitDecision:
    split: Split
    reason: ExclusionReason | None  # Why the deck is excluded; None for every other split.

@dataclass(frozen=True)
class SplitScheme:
    """A named recipe for splitting decks. New parameters need a default that reproduces earlier schemes."""
    name: str
    train_seasons: frozenset[int] = field(default_factory=lambda: frozenset(range(1, 39)))
    validation_seasons: frozenset[int] = frozenset({39})
    test_seasons: frozenset[int] = frozenset({40, 41, 42})
    held_out_percent: int = 10  # Share of training-season decklists held out, identical maindecks together.
    salt: str = ''  # Mixed into the hash; a different salt gives a different held-out set.
    train_statuses: frozenset[LabelStatus] = frozenset({LabelStatus.VERIFIED})  # Label statuses a model may train on.
    eval_statuses: frozenset[LabelStatus] = frozenset({LabelStatus.VERIFIED})  # Label statuses that are scored.

    def to_params(self) -> dict[str, Any]:
        """Every parameter except the name, as JSON-ready values."""
        return {f.name: to_json(getattr(self, f.name)) for f in fields(self) if f.name != 'name'}

    @classmethod
    def from_params(cls, name: str, params: dict[str, Any]) -> 'SplitScheme':
        """The inverse of to_params. Parameters missing from older schemes take their defaults."""
        values: dict[str, Any] = {}
        for k, v in params.items():
            if k.endswith('_seasons'):
                values[k] = frozenset(v)
            elif k.endswith('_statuses'):
                values[k] = frozenset(LabelStatus(s) for s in v)
            else:
                values[k] = v
        return cls(name, **values)

def to_json(value: Any) -> Any:
    if isinstance(value, frozenset):
        return sorted(to_json(v) for v in value)
    return value.value if isinstance(value, Enum) else value

def assign_split(*, deck_id: int, season_id: int, maindeck_hash: str | None, maindeck_cards: int, status: LabelStatus, scheme: SplitScheme) -> SplitDecision:
    """The split one deck belongs to under a scheme. Uses only the deck's own facts, so no other deck can change it."""
    role = deck_role(season_id, maindeck_hash, scheme)
    if role is None:
        return SplitDecision(Split.EXCLUDED, ExclusionReason.RESERVED_SEASON)
    if role == Split.TRAIN:
        allowed, reason = scheme.train_statuses, ExclusionReason.STATUS_NOT_TRAINED_ON
    else:
        allowed, reason = scheme.eval_statuses, ExclusionReason.STATUS_NOT_EVALUATED
    return SplitDecision(role, None) if status in allowed else SplitDecision(Split.EXCLUDED, reason)

def deck_role(season_id: int, maindeck_hash: str | None, scheme: SplitScheme) -> Split | None:
    """The split a deck's season and held-out group give it before its label status is considered, or None for a reserved season."""
    if season_id in scheme.test_seasons:
        return Split.TEST
    if season_id in scheme.validation_seasons:
        return Split.VALIDATION
    if season_id in scheme.train_seasons:
        held_out = zlib.crc32((scheme.salt + str(maindeck_hash)).encode()) % 100 < scheme.held_out_percent
        return Split.HELD_OUT if held_out else Split.TRAIN
    return None
