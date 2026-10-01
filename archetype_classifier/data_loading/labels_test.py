from datetime import UTC, datetime

from archetype_classifier.data_loading.labels import DeckLabel, LabelChange, LabelRule, LabelStatus, ScopeRule, label_facts, label_status

RED_DECK_WINS = 2
PRISONER = 3
AZORIUS_CONTROL = 4
WILDFIRE = 5
THRYX_WILDFIRE = 6
COMMANDER = 7
UNCLASSIFIED = 8
MARCH_2 = datetime(2024, 3, 2, tzinfo=UTC)
MARCH_5 = datetime(2024, 3, 5, tzinfo=UTC)
BOTH_RULES = (LabelRule.LATEST_ENTRY_IS_HUMAN, LabelRule.SITE_LABEL_IF_EVER_HUMAN)


def status(history: list[LabelChange], site_archetype_id: int | None, site_archetype_name: str | None, label_rule: LabelRule, source: str = 'League') -> DeckLabel:
    return label_status(label_facts(history), site_archetype_id, site_archetype_name, source, ScopeRule.LEAGUE_AND_GATHERLING, label_rule)


# Scenario: label status depends on the history, the site label and the label rule (Scenarios.md, "Splitting decks").

def test_a_persons_label_that_still_stands_is_verified() -> None:
    history = [LabelChange(1, PRISONER, by_person=True, changed_at=MARCH_2)]
    for rule in BOTH_RULES:
        assert status(history, PRISONER, 'Prisoner', rule) == DeckLabel(LabelStatus.VERIFIED, PRISONER)

def test_a_later_automatic_guess_the_site_refused_only_counts_under_the_latest_entry_rule() -> None:
    history = [LabelChange(2, PRISONER, by_person=True, changed_at=MARCH_2), LabelChange(2, RED_DECK_WINS, by_person=False, changed_at=MARCH_5)]
    assert status(history, PRISONER, 'Prisoner', LabelRule.LATEST_ENTRY_IS_HUMAN) == DeckLabel(LabelStatus.UNVERIFIED, PRISONER)
    assert status(history, PRISONER, 'Prisoner', LabelRule.SITE_LABEL_IF_EVER_HUMAN) == DeckLabel(LabelStatus.VERIFIED, PRISONER)

def test_a_curator_move_without_history_is_verified_only_when_the_site_label_counts() -> None:
    history = [LabelChange(3, WILDFIRE, by_person=True, changed_at=MARCH_2)]
    assert status(history, THRYX_WILDFIRE, 'Thryx-Wildfire', LabelRule.LATEST_ENTRY_IS_HUMAN) == DeckLabel(LabelStatus.UNVERIFIED, THRYX_WILDFIRE)
    assert status(history, THRYX_WILDFIRE, 'Thryx-Wildfire', LabelRule.SITE_LABEL_IF_EVER_HUMAN) == DeckLabel(LabelStatus.VERIFIED, THRYX_WILDFIRE)

def test_a_label_no_person_gave_is_unverified() -> None:
    machine_only = [LabelChange(4, RED_DECK_WINS, by_person=False, changed_at=MARCH_2)]
    for rule in BOTH_RULES:
        assert status(machine_only, RED_DECK_WINS, 'Red Deck Wins', rule) == DeckLabel(LabelStatus.UNVERIFIED, RED_DECK_WINS)
        assert status([], AZORIUS_CONTROL, 'Azorius Control', rule) == DeckLabel(LabelStatus.UNVERIFIED, AZORIUS_CONTROL)

def test_a_deck_without_a_label_is_unlabelled() -> None:
    for rule in BOTH_RULES:
        assert status([], None, None, rule) == DeckLabel(LabelStatus.UNLABELLED, None)

def test_placeholder_archetypes_and_other_sources_are_out_of_scope() -> None:
    commander = [LabelChange(7, COMMANDER, by_person=True, changed_at=MARCH_2)]
    unclassified = [LabelChange(8, UNCLASSIFIED, by_person=True, changed_at=MARCH_2)]
    external = [LabelChange(9, RED_DECK_WINS, by_person=True, changed_at=MARCH_2)]
    for rule in BOTH_RULES:
        assert status(commander, COMMANDER, 'Commander', rule) == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)
        assert status(unclassified, UNCLASSIFIED, 'Unclassified', rule) == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)
        assert status(external, RED_DECK_WINS, 'Red Deck Wins', rule, source='Tapped Out') == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)
        assert status([], None, None, rule, source='Tapped Out') == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)


# Scenario: a person's label and an automatic guess at the same moment.

def test_a_persons_label_and_a_guess_at_the_same_moment_counts_as_the_persons() -> None:
    history = [LabelChange(10, RED_DECK_WINS, by_person=False, changed_at=MARCH_2), LabelChange(10, PRISONER, by_person=True, changed_at=MARCH_2)]
    assert status(history, PRISONER, 'Prisoner', LabelRule.LATEST_ENTRY_IS_HUMAN) == DeckLabel(LabelStatus.VERIFIED, PRISONER)
