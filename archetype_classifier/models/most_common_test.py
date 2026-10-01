from archetype_classifier.data_loading.dataset import ArchetypeSnapshot, CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import JSON, FitContext, PredictDeck, Prediction, TrainingDeck, model_class
from archetype_classifier.models.most_common import MostCommonArchetype

RED_DECK_WINS, AZORIUS_CONTROL = 16, 49  # Their ids in the archetype tree.
TREE = ArchetypeTree({RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', None, 0), AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', None, 0)})
CONTEXT = FitContext(TREE, {}, seed=0)
RED = (CardCount('Mountain', 56), CardCount('Shock', 4))
BLUE = (CardCount('Essence Scatter', 4), CardCount('Island', 56))


def training_deck(deck_id: int, archetype_id: int | None) -> TrainingDeck:
    cards = RED if archetype_id == RED_DECK_WINS else BLUE
    status = LabelStatus.VERIFIED if archetype_id else LabelStatus.UNLABELLED
    return TrainingDeck(PredictDeck(deck_id, 'League', cards, ()), 30, archetype_id, True, status)

VALIDATION = [PredictDeck(201, 'League', RED, ()), PredictDeck(202, 'League', BLUE, ())]


# Scenario: the mock model guesses the most common training archetype (Scenarios.md, "Storing models and runs").

def test_the_mock_model_guesses_the_most_common_training_archetype_for_every_deck() -> None:
    training = [training_deck(101, RED_DECK_WINS), training_deck(102, RED_DECK_WINS), training_deck(103, RED_DECK_WINS),
                training_deck(104, AZORIUS_CONTROL), training_deck(105, AZORIUS_CONTROL)]
    model = MostCommonArchetype({})
    model.fit(training, [], CONTEXT)
    evidence: dict[str, JSON] = {'training_decks_with_archetype': 3, 'training_decks': 5}
    assert model.predict(VALIDATION) == [Prediction(201, RED_DECK_WINS, evidence), Prediction(202, RED_DECK_WINS, evidence)]
    assert model.state() == {'archetype_id': RED_DECK_WINS, 'training_decks_with_archetype': 3, 'training_decks': 5}

def test_a_tie_goes_to_the_lower_archetype_id_so_refitting_gives_the_same_guess() -> None:
    for order in ([AZORIUS_CONTROL, AZORIUS_CONTROL, RED_DECK_WINS, RED_DECK_WINS], [RED_DECK_WINS, RED_DECK_WINS, AZORIUS_CONTROL, AZORIUS_CONTROL]):
        model = MostCommonArchetype({})
        model.fit([training_deck(101 + i, a) for i, a in enumerate(order)], [], CONTEXT)
        assert [p.guess_id for p in model.predict(VALIDATION)] == [RED_DECK_WINS, RED_DECK_WINS]  # Red Deck Wins is 16, Azorius Control 49.

def test_with_no_labelled_training_decks_every_deck_gets_no_guess() -> None:
    model = MostCommonArchetype({})
    model.fit([training_deck(101, None), training_deck(102, None)], [], CONTEXT)
    assert [p.guess_id for p in model.predict(VALIDATION)] == [None, None]

def test_the_mock_model_is_registered_and_rebuilds_from_its_state() -> None:
    training = [training_deck(101, RED_DECK_WINS), training_deck(102, RED_DECK_WINS), training_deck(104, AZORIUS_CONTROL)]
    fitted = MostCommonArchetype({})
    fitted.fit(training, [], CONTEXT)
    rebuilt = model_class('most common archetype').from_state({}, fitted.state(), [], CONTEXT)  # Its state holds everything it learned.
    assert rebuilt.predict(VALIDATION) == fitted.predict(VALIDATION)
    assert rebuilt.state() == fitted.state() == {'archetype_id': RED_DECK_WINS, 'training_decks_with_archetype': 2, 'training_decks': 3}
