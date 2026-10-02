"""The similarity baseline on small rule-level decks: 60-card season 30 lists legal in seasons 30 and 39. Real decks are checked in similarity_local_test.py."""
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot, CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, PredictDeck, Prediction, TrainingDeck
from archetype_classifier.models.similarity import Match, SimilarityBaseline

AGGRO, CONTROL, RED_DECK_WINS, BURN, AZORIUS_CONTROL = 1, 2, 16, 17, 49
TREE = ArchetypeTree({AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0), CONTROL: ArchetypeSnapshot(CONTROL, 'Control', None, 0),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1), BURN: ArchetypeSnapshot(BURN, 'Burn', AGGRO, 1),
                      AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1)})
LEGAL = frozenset({'Shock', 'Burst Lightning', 'Mountain', 'Essence Scatter', 'Negate', 'Island', 'Smash to Smithereens', 'Searing Spear'})
CONTEXT = FitContext(TREE, {30: LEGAL, 39: LEGAL}, seed=0)


def cards(**counts: int) -> tuple[CardCount, ...]:
    return tuple(sorted((CardCount(name.replace('_', ' '), n) for name, n in counts.items()), key=lambda c: c.card))

def training(deck_id: int, archetype_id: int, maindeck: tuple[CardCount, ...], sideboard: tuple[CardCount, ...] = (), reviewed: bool = True,
             status: LabelStatus = LabelStatus.VERIFIED, source: str = 'League') -> TrainingDeck:
    return TrainingDeck(PredictDeck(deck_id, source, maindeck, sideboard), 30, archetype_id, reviewed, status)

TRAINING = [
    training(101, RED_DECK_WINS, cards(Shock=4, Burst_Lightning=4, Mountain=52)),
    training(102, AZORIUS_CONTROL, cards(Essence_Scatter=4, Negate=4, Island=52), sideboard=cards(Smash_to_Smithereens=2)),
    training(103, RED_DECK_WINS, cards(Shock=4, Burst_Lightning=2, Mountain=54)),
    training(104, RED_DECK_WINS, cards(Shock=2, Burst_Lightning=4, Mountain=54), reviewed=False, status=LabelStatus.UNVERIFIED),
]

def fitted(threshold: int | str = 20) -> SimilarityBaseline:
    model = SimilarityBaseline({'threshold': threshold})
    model.fit(TRAINING, [], CONTEXT)
    return model


# Scenario: weights come from the training decks, by the site's formula.

def test_weights_come_from_the_training_decks_by_the_sites_formula() -> None:
    weight = fitted().weight
    assert weight('Shock') == weight('Burst Lightning') == weight('Mountain') == 1 / 0.75  # In 3 of the 4 training maindecks.
    assert weight('Island') == weight('Negate') == 1 / 0.25
    assert weight('Smash to Smithereens') == 1 / 0.05  # Only in a sideboard, so 0.2 of one deck in 4.
    assert weight('Searing Spear') == 1000  # Legal in season 30, played by no training deck: the floor.
    assert weight("Archmage's Charm") == 1000  # Never legal in a training season: also the floor.


def query(deck_id: int, maindeck: tuple[CardCount, ...], source: str = 'League') -> PredictDeck:
    return PredictDeck(deck_id, source, maindeck, ())


# Scenario: a deck identical to training decks matches at 100%, and ties go to the higher id.

def test_an_identical_deck_matches_at_100_and_ties_go_to_the_higher_id() -> None:
    model = fitted()
    deck = query(201, cards(Shock=4, Burst_Lightning=4, Mountain=52))
    assert model.matches(deck) == [Match(101, 100), Match(104, 33), Match(103, 33)]
    assert model.predict([deck]) == [Prediction(201, RED_DECK_WINS, {'match_deck_id': 101, 'score': 100, 'rule': 'league'})]


# Scenario: a match needs the same card and quantity.

def test_a_match_needs_the_same_card_and_quantity() -> None:
    deck = query(210, cards(Shock=4, Mountain=56))
    assert fitted().matches(deck) == [Match(103, 33), Match(101, 33), Match(104, 0)]  # 104 plays 2 Shock: a candidate, but nothing shared.
    assert fitted(20).predict([deck])[0].guess_id == RED_DECK_WINS
    assert fitted(34).predict([deck]) == [Prediction(210, None, {})]


# Scenario: sharing only a basic land isn't a match (a rule-level check).

def test_sharing_only_a_basic_land_isnt_a_match() -> None:
    deck = query(208, cards(Essence_Scatter=4, Negate=4, Mountain=52))  # Shares only "52 Mountain" with 101.
    assert fitted().matches(deck) == [Match(102, 67)]
    assert fitted(1).predict([deck])[0].evidence == {'match_deck_id': 102, 'score': 67, 'rule': 'league'}
