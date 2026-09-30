from archetype_classifier.data_loading.labels import LabelChange, Provenance, label_source

RED_DECK_WINS = 2
PRISONER = 3


def test_a_person_changing_the_guess_is_a_corrected_guess() -> None:
    source = label_source([LabelChange(7, RED_DECK_WINS, by_person=False), LabelChange(7, PRISONER, by_person=True)])
    assert source.provenance == Provenance.CORRECTED_GUESS
    assert source.guess_archetype_id == RED_DECK_WINS
    assert source.latest_archetype_id == PRISONER

def test_a_person_keeping_the_guess_is_a_validated_guess() -> None:
    source = label_source([LabelChange(11, PRISONER, by_person=False), LabelChange(11, PRISONER, by_person=True)])
    assert source.provenance == Provenance.VALIDATED_GUESS
    assert source.guess_archetype_id == PRISONER

def test_a_first_label_by_a_person_is_direct() -> None:
    source = label_source([LabelChange(12, PRISONER, by_person=True)])
    assert source.provenance == Provenance.PERSON_DIRECT
    assert source.guess_archetype_id is None

def test_a_relabel_after_another_person_is_direct() -> None:
    history = [LabelChange(13, RED_DECK_WINS, by_person=False), LabelChange(13, RED_DECK_WINS, by_person=True), LabelChange(13, PRISONER, by_person=True)]
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
    source = label_source([LabelChange(8, RED_DECK_WINS, by_person=False)])
    assert source.provenance == Provenance.AUTOMATIC
    assert source.guess_archetype_id is None
    assert source.latest_archetype_id == RED_DECK_WINS
