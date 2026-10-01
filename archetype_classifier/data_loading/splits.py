import zlib
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any

from archetype_classifier.data_loading.labels import LabelRule, LabelStatus, ScopeRule


class Split(Enum):
    TRAIN = 'train'
    HELD_OUT = 'held_out'  # Held-out decklists from the training seasons.
    VALIDATION = 'validation'
    TEST = 'test'
    EXCLUDED = 'excluded'  # Neither trained on nor scored; the reason is recorded.

MINIMUM_MAINDECK = 60  # Every legal maindeck has at least this many cards; fewer means broken data.

class ExclusionReason(Enum):
    NO_MAINDECK_CARDS = 'no maindeck cards'
    MAINDECK_UNDER_60_CARDS = 'maindeck under 60 cards'
    RESERVED_SEASON = 'reserved season'
    NOT_IN_SNAPSHOT = 'not in snapshot'  # For example, a deck played after the snapshot was taken.
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
    scope_rule: ScopeRule = ScopeRule.LEAGUE_AND_GATHERLING  # Which decks can be scored at all.
    label_rule: LabelRule = LabelRule.LATEST_ENTRY_IS_HUMAN  # Which label a deck is scored against, and when it is verified.
    train_statuses: frozenset[LabelStatus] = frozenset({LabelStatus.VERIFIED})  # Label statuses a model may train on.
    eval_statuses: frozenset[LabelStatus] = frozenset({LabelStatus.VERIFIED})  # Label statuses that are scored.
    allow_held_out_twins: bool = False  # Hold out single decks rather than maindeck groups, so held-out decks can repeat a training maindeck.

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
            elif k == 'scope_rule':
                values[k] = ScopeRule(v)
            elif k == 'label_rule':
                values[k] = LabelRule(v)
            else:
                values[k] = v
        return cls(name, **values)

def to_json(value: Any) -> Any:
    if isinstance(value, frozenset):
        return sorted(to_json(v) for v in value)
    return value.value if isinstance(value, Enum) else value

def assign_split(*, deck_id: int, season_id: int, maindeck_hash: str | None, maindeck_cards: int, status: LabelStatus, scheme: SplitScheme) -> SplitDecision:
    """The split one deck belongs to under a scheme. Uses only the deck's own facts, so no other deck can change it."""
    if maindeck_hash is None or maindeck_cards == 0:
        return SplitDecision(Split.EXCLUDED, ExclusionReason.NO_MAINDECK_CARDS)
    if maindeck_cards < MINIMUM_MAINDECK:
        return SplitDecision(Split.EXCLUDED, ExclusionReason.MAINDECK_UNDER_60_CARDS)
    role = deck_role(season_id, str(deck_id) if scheme.allow_held_out_twins else maindeck_hash, scheme)
    if role is None:
        return SplitDecision(Split.EXCLUDED, ExclusionReason.RESERVED_SEASON)
    if role == Split.TRAIN:
        allowed, reason = scheme.train_statuses, ExclusionReason.STATUS_NOT_TRAINED_ON
    else:
        allowed, reason = scheme.eval_statuses, ExclusionReason.STATUS_NOT_EVALUATED
    return SplitDecision(role, None) if status in allowed else SplitDecision(Split.EXCLUDED, reason)

def deck_role(season_id: int, group_key: str, scheme: SplitScheme) -> Split | None:
    """The split a deck's season and held-out group give it before its label status is considered, or None for a reserved season.

    The group key is the maindeck hash, so identical maindecks share a role, or the deck id when twins are allowed."""
    if season_id in scheme.test_seasons:
        return Split.TEST
    if season_id in scheme.validation_seasons:
        return Split.VALIDATION
    if season_id in scheme.train_seasons:
        held_out = zlib.crc32((scheme.salt + group_key).encode()) % 100 < scheme.held_out_percent
        return Split.HELD_OUT if held_out else Split.TRAIN
    return None
