from datetime import UTC, datetime

from archetype_classifier.data_loading.labels import DeckLabel, LabelChange, LabelRule, LabelStatus, Provenance, ScopeRule, label_facts, label_source, label_status

RED_DECK_WINS = 2
PRISONER = 3
MARCH_2 = datetime(2024, 3, 2, tzinfo=UTC)
BOTH_RULES = (LabelRule.LATEST_ENTRY_IS_HUMAN, LabelRule.SITE_LABEL_IF_EVER_HUMAN)
EPOCH = datetime(2020, 1, 1, tzinfo=UTC)  # Order is all these tests need.


def status(history: list[LabelChange], site_archetype_id: int | None, site_archetype_name: str | None, label_rule: LabelRule, source: str = 'League') -> DeckLabel:
    return label_status(label_facts(history), site_archetype_id, site_archetype_name, source, ScopeRule.LEAGUE_AND_GATHERLING, label_rule)


# Scenario: label status depends on the history, the site label and the label rule (Scenarios.md, "Splitting decks").

def test_a_persons_label_that_still_stands_is_verified() -> None:
    history = [LabelChange(1, PRISONER, by_person=True, changed_at=MARCH_2)]
    for rule in BOTH_RULES:
        assert status(history, PRISONER, 'Prisoner', rule) == DeckLabel(LabelStatus.VERIFIED, PRISONER)



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
