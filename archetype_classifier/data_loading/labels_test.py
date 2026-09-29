from archetype_classifier.data_loading.labels import LabelChange, Provenance, label_source

RED_DECK_WINS = 2
PRISONER = 3


def test_a_person_changing_the_guess_is_a_corrected_guess() -> None:
    source = label_source([LabelChange(7, RED_DECK_WINS, by_person=False), LabelChange(7, PRISONER, by_person=True)])
    assert source.provenance == Provenance.CORRECTED_GUESS
    assert source.guess_archetype_id == RED_DECK_WINS
    assert source.latest_archetype_id == PRISONER
