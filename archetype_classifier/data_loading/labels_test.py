from datetime import UTC, datetime

from archetype_classifier.data_loading.labels import DeckLabel, LabelChange, LabelRule, LabelStatus, ScopeRule, decided_after, label_at, label_facts, label_status

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


# Scenario: a training deck relabelled after the cutoff trains on its label at the cutoff (Scenarios.md, "Labels at a cutoff").

FLARE_DECK_WINS = 11
EQUIPMENT_AGGRO = 12
BURN = 13
NAMES = {RED_DECK_WINS: 'Red Deck Wins', FLARE_DECK_WINS: 'Flare Deck Wins', EQUIPMENT_AGGRO: 'Equipment Aggro', BURN: 'Burn', UNCLASSIFIED: 'Unclassified',
         COMMANDER: 'Commander', WILDFIRE: 'Wildfire'}
CUTOFF = datetime(2025, 10, 3, 7, tzinfo=UTC)  # The start of season 39.
BEFORE = datetime(2025, 6, 1, tzinfo=UTC)
AFTER = datetime(2026, 4, 8, tzinfo=UTC)


def at_cutoff(history: list[LabelChange], source: str = 'League') -> DeckLabel:
    return label_at(history, CUTOFF, source, NAMES, ScopeRule.LEAGUE_AND_GATHERLING)

def test_a_deck_relabelled_by_a_person_after_the_cutoff_keeps_its_earlier_persons_label() -> None:
    a = [LabelChange(1, RED_DECK_WINS, by_person=True, changed_at=BEFORE), LabelChange(1, FLARE_DECK_WINS, by_person=True, changed_at=AFTER)]
    assert at_cutoff(a) == DeckLabel(LabelStatus.VERIFIED, RED_DECK_WINS)

def test_a_persons_review_after_the_cutoff_does_not_verify_an_earlier_automatic_label() -> None:
    b = [LabelChange(2, RED_DECK_WINS, by_person=False, changed_at=BEFORE), LabelChange(2, EQUIPMENT_AGGRO, by_person=True, changed_at=AFTER)]
    assert at_cutoff(b) == DeckLabel(LabelStatus.UNVERIFIED, RED_DECK_WINS)

def test_a_deck_first_labelled_after_the_cutoff_is_unlabelled() -> None:
    c = [LabelChange(3, EQUIPMENT_AGGRO, by_person=True, changed_at=AFTER)]
    assert at_cutoff(c) == DeckLabel(LabelStatus.UNLABELLED, None)

def test_scope_is_judged_on_the_label_at_the_cutoff() -> None:
    d = [LabelChange(4, UNCLASSIFIED, by_person=True, changed_at=BEFORE), LabelChange(4, BURN, by_person=True, changed_at=AFTER)]
    assert at_cutoff(d) == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)
    external = [LabelChange(5, BURN, by_person=True, changed_at=BEFORE), LabelChange(5, RED_DECK_WINS, by_person=True, changed_at=AFTER)]
    assert at_cutoff(external, source='Tapped Out') == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)
    assert at_cutoff([LabelChange(6, BURN, by_person=True, changed_at=AFTER)], source='Tapped Out') == DeckLabel(LabelStatus.OUT_OF_SCOPE, None)

def test_an_automatic_guess_after_the_cutoff_never_beats_a_persons_label() -> None:
    e = [LabelChange(7, BURN, by_person=True, changed_at=BEFORE), LabelChange(7, RED_DECK_WINS, by_person=False, changed_at=AFTER)]
    assert at_cutoff(e) == DeckLabel(LabelStatus.VERIFIED, BURN)
    guess_then_person = [LabelChange(8, RED_DECK_WINS, by_person=False, changed_at=BEFORE), LabelChange(8, BURN, by_person=True, changed_at=BEFORE)]
    assert at_cutoff(guess_then_person) == DeckLabel(LabelStatus.VERIFIED, BURN)
    person_then_guess = [LabelChange(9, BURN, by_person=True, changed_at=BEFORE), LabelChange(9, RED_DECK_WINS, by_person=False, changed_at=BEFORE)]
    assert at_cutoff(person_then_guess) == DeckLabel(LabelStatus.VERIFIED, BURN)

def test_an_entry_exactly_at_the_cutoff_counts_as_before_it() -> None:
    f = [LabelChange(10, BURN, by_person=True, changed_at=CUTOFF), LabelChange(10, RED_DECK_WINS, by_person=True, changed_at=AFTER)]
    assert at_cutoff(f) == DeckLabel(LabelStatus.VERIFIED, BURN)

def test_entries_at_the_same_moment_go_by_history_order() -> None:
    tie = [LabelChange(11, RED_DECK_WINS, by_person=True, changed_at=BEFORE), LabelChange(11, BURN, by_person=True, changed_at=BEFORE)]
    assert at_cutoff(tie) == DeckLabel(LabelStatus.VERIFIED, BURN)

def test_a_decision_after_the_cutoff_is_any_entry_later_than_it() -> None:
    assert decided_after([LabelChange(12, BURN, by_person=True, changed_at=BEFORE), LabelChange(12, BURN, by_person=False, changed_at=AFTER)], CUTOFF)
    assert not decided_after([LabelChange(13, BURN, by_person=True, changed_at=BEFORE), LabelChange(13, RED_DECK_WINS, by_person=True, changed_at=CUTOFF)], CUTOFF)
    assert not decided_after([], CUTOFF)
