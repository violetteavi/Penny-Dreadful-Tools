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

    def to_params(self) -> dict[str, Any]:
        """Every parameter except the name, as JSON-ready values."""
        return {f.name: sorted(v) if isinstance(v := getattr(self, f.name), frozenset) else v for f in fields(self) if f.name != 'name'}

    @classmethod
    def from_params(cls, name: str, params: dict[str, Any]) -> 'SplitScheme':
        """The inverse of to_params. Parameters missing from older schemes take their defaults."""
        season_fields = {f.name for f in fields(cls) if f.name.endswith('_seasons')}
        values: dict[str, Any] = {k: frozenset(v) if k in season_fields else v for k, v in params.items()}
        return cls(name, **values)

def assign_split(*, deck_id: int, season_id: int, maindeck_hash: str | None, maindeck_cards: int, status: LabelStatus, scheme: SplitScheme) -> SplitDecision:
    """The split one deck belongs to under a scheme. Uses only the deck's own facts, so no other deck can change it."""
    if season_id in scheme.test_seasons:
        return SplitDecision(Split.TEST, None)
    if season_id in scheme.validation_seasons:
        return SplitDecision(Split.VALIDATION, None)
    if season_id in scheme.train_seasons:
        held_out = zlib.crc32((scheme.salt + str(maindeck_hash)).encode()) % 100 < scheme.held_out_percent
        return SplitDecision(Split.HELD_OUT if held_out else Split.TRAIN, None)
    return SplitDecision(Split.EXCLUDED, ExclusionReason.RESERVED_SEASON)
