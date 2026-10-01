from datetime import UTC, datetime

from archetype_classifier.data_loading.labels import DeckLabel, LabelChange, LabelRule, LabelStatus, Provenance, ScopeRule, label_facts, label_source, label_status

RED_DECK_WINS = 2
PRISONER = 3
AZORIUS_CONTROL = 4
WILDFIRE = 5
THRYX_WILDFIRE = 6
MARCH_2 = datetime(2024, 3, 2, tzinfo=UTC)
MARCH_5 = datetime(2024, 3, 5, tzinfo=UTC)
BOTH_RULES = (LabelRule.LATEST_ENTRY_IS_HUMAN, LabelRule.SITE_LABEL_IF_EVER_HUMAN)
EPOCH = datetime(2020, 1, 1, tzinfo=UTC)  # Order is all these tests need.


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



def test_a_person_changing_the_guess_is_a_corrected_guess() -> None:
    source = label_source([LabelChange(7, RED_DECK_WINS, by_person=False, changed_at=EPOCH), LabelChange(7, PRISONER, by_person=True, changed_at=EPOCH)])
    assert source.provenance == Provenance.CORRECTED_GUESS
    assert source.guess_archetype_id == RED_DECK_WINS
    assert source.latest_archetype_id == PRISONER

def test_a_person_keeping_the_guess_is_a_validated_guess() -> None:
    source = label_source([LabelChange(11, PRISONER, by_person=False, changed_at=EPOCH), LabelChange(11, PRISONER, by_person=True, changed_at=EPOCH)])
    assert source.provenance == Provenance.VALIDATED_GUESS
    assert source.guess_archetype_id == PRISONER

def test_a_first_label_by_a_person_is_direct() -> None:
    source = label_source([LabelChange(12, PRISONER, by_person=True, changed_at=EPOCH)])
    assert source.provenance == Provenance.PERSON_DIRECT
    assert source.guess_archetype_id is None

def test_a_relabel_after_another_person_is_direct() -> None:
    history = [LabelChange(13, RED_DECK_WINS, by_person=False, changed_at=EPOCH), LabelChange(13, RED_DECK_WINS, by_person=True, changed_at=EPOCH), LabelChange(13, PRISONER, by_person=True, changed_at=EPOCH)]
    source = label_source(history)
    assert source.provenance == Provenance.PERSON_DIRECT
    assert source.guess_archetype_id is None
    assert source.latest_archetype_id == PRISONER

def test_no_history() -> None:
    source = label_source([])
    assert source.provenance == Provenance.NO_HISTORY
    assert source.guess_archetype_id is None
    assert source.latest_archetype_id is None

def test_an_unreviewed_guess_is_automatic() -> None:
    source = label_source([LabelChange(8, RED_DECK_WINS, by_person=False, changed_at=EPOCH)])
    assert source.provenance == Provenance.AUTOMATIC
    assert source.guess_archetype_id is None
    assert source.latest_archetype_id == RED_DECK_WINS
