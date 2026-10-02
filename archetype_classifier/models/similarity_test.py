"""The similarity baseline on small rule-level decks: 60-card season 30 lists legal in seasons 30 and 39. Real decks are checked in similarity_local_test.py."""
from typing import cast

import pytest

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot, CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import JSON, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, model_class
from archetype_classifier.models.similarity import Match, SimilarityBaseline

AGGRO, CONTROL, RED_DECK_WINS, BURN, AZORIUS_CONTROL = 1, 2, 16, 17, 49
TREE = ArchetypeTree({AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0), CONTROL: ArchetypeSnapshot(CONTROL, 'Control', None, 0),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1), BURN: ArchetypeSnapshot(BURN, 'Burn', AGGRO, 1),
                      AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1)})
LEGAL = frozenset({'Shock', 'Burst Lightning', 'Mountain', 'Essence Scatter', 'Negate', 'Island', 'Smash to Smithereens', 'Searing Spear'})
CONTEXT = FitContext(TREE, {30: LEGAL, 39: LEGAL}, seed=0)


def cards(**counts: int) -> tuple[CardCount, ...]:
    """Card names written as keywords: underscores are spaces, and "_s_" is "'s " (Ranger_s_Guile is Ranger's Guile)."""
    return tuple(sorted((CardCount(name.replace('_s_', "'s ").replace('_', ' '), n) for name, n in counts.items()), key=lambda c: c.card))

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


# Scenario: League decks skip unreviewed matches, and Gatherling decks don't (a rule-level check).

def test_league_decks_skip_unreviewed_matches_and_gatherling_decks_dont() -> None:
    maindeck = cards(Shock=2, Burst_Lightning=4, Mountain=54)  # Identical to 104, which isn't reviewed.
    model = fitted()
    league, gatherling = model.predict([query(209, maindeck, 'League'), query(209, maindeck, 'Gatherling')])
    assert league == Prediction(209, RED_DECK_WINS, {'match_deck_id': 103, 'score': 33, 'rule': 'league'})
    assert gatherling == Prediction(209, RED_DECK_WINS, {'match_deck_id': 104, 'score': 100, 'rule': 'gatherling'})


# Scenario: the tuned threshold maximises hF on the validation decks.

STOMPY = 18
TUNING_TREE = ArchetypeTree({**{a: TREE.archetypes[a] for a in TREE.archetypes}, STOMPY: ArchetypeSnapshot(STOMPY, 'Stompy', AGGRO, 1)})
VALIDATION = [  # Their best League matches score 100, none, none, none, 67, 33 and 33.
    LabelledDeck(query(201, cards(Shock=4, Burst_Lightning=4, Mountain=52)), RED_DECK_WINS, 'a'),
    LabelledDeck(query(205, cards(Shock=4, Burst_Lightning=4, Searing_Spear=4, Fiery_Temper=1, Mountain=47)), RED_DECK_WINS, 'b'),
    LabelledDeck(query(212, cards(Shock=4, Searing_Spear=4, Fiery_Temper=4, Volcanic_Hammer=4, Mountain=44)), RED_DECK_WINS, 'c'),
    LabelledDeck(query(260, cards(Young_Wolf=4, Nest_Invader=4, Elvish_Visionary=4, Giant_Growth=4, Savage_Swipe=4, Gather_Courage=4, Ranger_s_Guile=4,
                                  Hunger_of_the_Howlpack=4, Aspect_of_Hydra=4, Forest=24)), STOMPY, 'd'),
    LabelledDeck(query(208, cards(Essence_Scatter=4, Negate=4, Mountain=52)), AZORIUS_CONTROL, 'e'),
    LabelledDeck(query(209, cards(Shock=2, Burst_Lightning=4, Mountain=54)), RED_DECK_WINS, 'f'),
    LabelledDeck(query(210, cards(Shock=4, Mountain=56)), RED_DECK_WINS, 'g'),
]

def tuned_state(threshold: int | str) -> dict[str, JSON]:
    model = SimilarityBaseline({'threshold': threshold})
    model.fit(TRAINING, VALIDATION, FitContext(TUNING_TREE, CONTEXT.legal_cards, seed=0))
    return model.state()

def test_the_tuned_threshold_maximises_hf_on_the_validation_decks() -> None:
    state = tuned_state('tuned')
    curve = {point[0]: point[1:] for point in cast(list[list[float]], state['validation_curve'])}
    assert list(curve) == list(range(1, 101))
    assert curve[1] == curve[20] == curve[33] == pytest.approx([1.0, 8 / 14, 0.7273], abs=1e-4)  # Every threshold up to 33 ties at the best hF,
    assert curve[34] == curve[67] == pytest.approx([1.0, 4 / 14, 0.4444], abs=1e-4)
    assert curve[68] == curve[100] == pytest.approx([1.0, 2 / 14, 0.25], abs=1e-4)
    assert state['threshold'] == 20  # so the tuned model keeps the one nearest the site's 20.
    fixed = tuned_state(30)
    assert (fixed['threshold'], fixed['validation_curve']) == (30, state['validation_curve'])  # A fixed threshold is kept, and the curve still recorded.


def test_a_tuned_threshold_needs_validation_decks() -> None:
    with pytest.raises(ValueError, match='validation decks'):
        fitted('tuned')
    assert fitted(20).state()['validation_curve'] == []


# Scenario: scores match the site's own function.

def test_scores_match_the_sites_own_function() -> None:
    from decksite.data.deck import similarity_score  # Imported first: the site's packages import each other in this order.
    from magic.models import Deck
    from magic.models.cardref import CardRef

    def site_deck(maindeck: tuple[CardCount, ...]) -> Deck:
        deck = Deck({})
        deck.maindeck = [CardRef(c.card, c.n) for c in maindeck]
        return deck

    model = fitted()
    training = {d.deck.deck_id: site_deck(d.deck.maindeck) for d in TRAINING}
    compared = 0
    for v in VALIDATION:
        for match in model.matches(v.deck):
            assert match.score == round(similarity_score(site_deck(v.deck.maindeck), training[match.deck_id], model.playability) * 100)
            compared += 1
    assert compared == 16  # Candidates: 3 each for decks 201, 205, 212, 209 and 210, 1 for 208, and none for 260.


# Scenario: a fitted baseline loads back and guesses the same.

def test_a_fitted_baseline_loads_back_and_guesses_the_same() -> None:
    model = SimilarityBaseline({'threshold': 'tuned'})
    model.fit(TRAINING, VALIDATION, FitContext(TUNING_TREE, CONTEXT.legal_cards, seed=0))
    rebuilt = model_class('similarity').from_state(model.params, model.state(), TRAINING, CONTEXT)
    decks = [v.deck for v in VALIDATION]
    assert rebuilt.predict(decks) == model.predict(decks)
    assert rebuilt.state() == model.state()
