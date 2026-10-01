from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class LabelChange:
    deck_id: int
    archetype_id: int
    by_person: bool
    changed_at: datetime

INCLUDED_SOURCES = frozenset({'League', 'Gatherling'})
EXCLUDED_ARCHETYPES = frozenset({'Unclassified', 'Commander'})  # Placeholders, not strategies.

class ScopeRule(Enum):
    LEAGUE_AND_GATHERLING = 'league_and_gatherling'  # League and Gatherling decks, not labelled Unclassified or Commander.

class LabelRule(Enum):
    LATEST_ENTRY_IS_HUMAN = 'latest_entry_is_human'  # Verified when the latest history entry is a person's and matches the site label.
    SITE_LABEL_IF_EVER_HUMAN = 'site_label_if_ever_human'  # Scored against the site label; verified when a person labelled the deck at some point.

class LabelStatus(Enum):
    VERIFIED = 'verified'
    UNVERIFIED = 'unverified'
    UNLABELLED = 'unlabelled'
    OUT_OF_SCOPE = 'out_of_scope'

@dataclass(frozen=True)
class LabelFacts:
    """What the label history says about a deck: the latest label a person gave, and the latest automatic guess."""
    human_archetype_id: int | None
    human_labelled_at: datetime | None
    machine_archetype_id: int | None
    machine_labelled_at: datetime | None

@dataclass(frozen=True)
class DeckLabel:
    status: LabelStatus
    label_id: int | None  # The label the deck is scored against, or None if it has none.

def label_facts(history: Sequence[LabelChange]) -> LabelFacts:
    """The latest human label and the latest automatic guess in a deck's history, oldest first."""
    human = next((c for c in reversed(history) if c.by_person), None)
    machine = next((c for c in reversed(history) if not c.by_person), None)
    return LabelFacts(human.archetype_id if human else None, human.changed_at if human else None,
                      machine.archetype_id if machine else None, machine.changed_at if machine else None)

def label_status(facts: LabelFacts, site_archetype_id: int | None, site_archetype_name: str | None, source: str, scope_rule: ScopeRule, label_rule: LabelRule) -> DeckLabel:
    """How far a deck's label can be trusted, and the label it is scored against."""
    if not in_scope(source, site_archetype_name, scope_rule):
        return DeckLabel(LabelStatus.OUT_OF_SCOPE, None)
    if site_archetype_id is None:
        return DeckLabel(LabelStatus.UNLABELLED, None)
    if label_rule == LabelRule.LATEST_ENTRY_IS_HUMAN:
        verified = latest_entry_is_human(facts) and facts.human_archetype_id == site_archetype_id
    else:
        verified = facts.human_archetype_id is not None
    return DeckLabel(LabelStatus.VERIFIED if verified else LabelStatus.UNVERIFIED, site_archetype_id)

def in_scope(source: str, site_archetype_name: str | None, scope_rule: ScopeRule) -> bool:
    """Whether the scope rule evaluates decks like this one. There is one rule so far."""
    return source in INCLUDED_SOURCES and site_archetype_name not in EXCLUDED_ARCHETYPES

def latest_entry_is_human(facts: LabelFacts) -> bool:
    """Whether a person's label is the deck's latest history entry. A tie with an automatic guess counts as the person's."""
    if facts.human_labelled_at is None:
        return False
    return facts.machine_labelled_at is None or facts.human_labelled_at >= facts.machine_labelled_at
