import zlib
from dataclasses import dataclass, field, fields
from typing import Any
from enum import Enum


class Split(Enum):
    TRAIN = 'train'
    HELD_OUT = 'held_out'  # Held-out decklists from the training seasons.
    VALIDATION = 'validation'
    TEST = 'test'

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
        return cls(name, **{k: frozenset(v) if k in season_fields else v for k, v in params.items()})

def assign_split(season_id: int, maindeck_hash: str, scheme: SplitScheme) -> Split | None:
    """The split a deck belongs to, or None if its season is outside the scheme."""
    if season_id in scheme.test_seasons:
        return Split.TEST
    if season_id in scheme.validation_seasons:
        return Split.VALIDATION
    if season_id in scheme.train_seasons:
        held_out = zlib.crc32((scheme.salt + maindeck_hash).encode()) % 100 < scheme.held_out_percent
        return Split.HELD_OUT if held_out else Split.TRAIN
    return None
