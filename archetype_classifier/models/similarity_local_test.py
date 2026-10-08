"""The similarity baseline on real decks, against the full local dump. Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 2
("similarity baseline") in the experiments database and the real site database, and the agreement check takes about a minute per sampled deck.

    PD_LOCAL_DATA=1 uv run pytest -s archetype_classifier/models/similarity_local_test.py
    PD_LOCAL_DATA_DECKS=50 ...  # how many decks to check against the site (default 20)
"""
import os
from collections.abc import Iterator

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import Snapshot, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, PredictDeck, TrainingDeck, build_predict_decks, build_training_decks
from archetype_classifier.models.similarity import FLOOR, Index, SimilarityBaseline

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
SITE_THRESHOLD = 20


@pytest.fixture(scope='module')
def snapshot() -> Snapshot:
    edb = loader.experiments_db()
    scheme_id = edb.value("SELECT id FROM split_scheme WHERE name = 'similarity baseline'")
    return loader.load_snapshot(edb, 1, scheme_id)

@pytest.fixture(scope='module')
def baseline(snapshot: Snapshot) -> SimilarityBaseline:
    """The fixed-threshold baseline, fitted on scheme 2's TRAIN decks."""
    train = build_deck_set(snapshot, frozenset({Split.TRAIN}))
    context = FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in train.decks.values()}), seed=0)
    model = SimilarityBaseline({'threshold': SITE_THRESHOLD})
    model.fit(build_training_decks(train, loader.load_contents(train.decks)), [], context)
    return model

def predict_deck(snapshot: Snapshot, deck_id: int) -> PredictDeck:
    deck_set = build_deck_set(Snapshot({deck_id: snapshot.decks[deck_id]}, snapshot.archetypes, snapshot.scheme), frozenset({snapshot.decks[deck_id].split}))
    return build_predict_decks(deck_set, loader.load_contents([deck_id]))[0]

def name(snapshot: Snapshot, archetype_id: int | None) -> str | None:
    return snapshot.archetypes[archetype_id].name if archetype_id is not None else None


# Scenario: weights come from the training decks, by the site's formula.

def test_real_weights(baseline: SimilarityBaseline) -> None:
    assert [baseline.playability[c] for c in ('Island', 'Mountain', 'Burst Lightning', 'Make Disappear')] == [0.38226, 0.32338, 0.1311, 0.00173]
    assert baseline.weight("Archmage's Charm") == 1000  # No training deck plays it.
    at_floor = sum(1 for p in baseline.playability.values() if p < FLOOR) / len(baseline.playability)
    assert (len(baseline.playability), round(at_floor, 2)) == (23618, 0.79)


# Scenarios: identical decks, same card and quantity, unseen cards, and decks with no unseen cards but no exact match.

def test_real_scenario_decks(snapshot: Snapshot, baseline: SimilarityBaseline) -> None:
    oops = baseline.matches(predict_deck(snapshot, 269508))
    assert [(m.deck_id, m.score) for m in oops[:3]] == [(264554, 100), (264496, 100), (262588, 79)]
    expected = {  # deck -> (best match, its score, the guess at 20 by name)
        269508: (264554, 100, 'Oops All Lands'), 269653: (244684, 21, 'Izzet Spells'), 269833: (264566, 17, None), 269466: (264841, 9, None),
        269940: (269227, 10, None), 269539: (269464, 73, 'Mono Green Stompy'), 269503: (269180, 61, 'Selesnya Heroic'), 270398: (246062, 29, 'Mono White Humans'),
    }
    for deck_id, (match, score, guess) in expected.items():
        deck = predict_deck(snapshot, deck_id)
        assert (baseline.matches(deck)[0].deck_id, baseline.matches(deck)[0].score) == (match, score), deck_id
        assert name(snapshot, baseline.predict([deck])[0].guess_id) == guess, deck_id


# Scenario: on real decks, the baseline agrees with the site.

@pytest.fixture(scope='module')
def site_index(snapshot: Snapshot) -> Iterator[Index]:
    """Every deck on the site, weighted by the site's own stored playability: what calculate_similar_decks searches."""
    from decksite.data import playability  # Imported here: the site's packages import each other in this order.
    from decksite.main import APP
    with APP.app_context():
        plays = playability.playability()
    everything = {i: d for i, d in snapshot.decks.items()}
    contents = loader.load_contents(everything)
    decks = [TrainingDeck(PredictDeck(i, d.source, tuple(sorted(contents[i].maindeck, key=lambda c: c.card)), ()), d.season_id, d.site_archetype_id, d.reviewed, d.label_status)
             for i, d in everything.items() if i in contents]
    yield Index(decks, lambda card: 1.0 / max(plays.get(card, FLOOR), FLOOR))

def test_the_baseline_agrees_with_the_sites_own_guesser(snapshot: Snapshot, site_index: Index) -> None:
    from decksite.data import deck
    from decksite.main import APP
    validation = sorted(i for i, d in snapshot.decks.items() if d.split == Split.VALIDATION)
    sample_size = int(os.environ.get('PD_LOCAL_DATA_DECKS', '20'))
    league = [i for i in validation if snapshot.decks[i].source == 'League'][::40][:sample_size * 3 // 4]
    gatherling = [i for i in validation if snapshot.decks[i].source == 'Gatherling'][::20][:sample_size - len(league)]
    deck_differs: list[int] = []
    label_differs: list[int] = []
    unlabelled_top: list[int] = []
    for deck_id in league + gatherling:
        with APP.app_context():
            site_decks = deck.load_decks(f'd.id = {deck_id}')
            deck.calculate_similar_decks(site_decks)
        site = [(s.id, s.similarity_score) for s in site_decks[0].similar_decks]
        rows, scores = next(site_index.scores([predict_deck(snapshot, deck_id)]))
        ours = {int(site_index.deck_ids[r]): int(s) for r, s in zip(rows, scores) if s >= SITE_THRESHOLD and site_index.deck_ids[r] != deck_id}
        assert ours == dict(site), deck_id  # The same matches at or above 20, with the same scores.
        source = snapshot.decks[deck_id].source
        ours_pick = site_index.pick(source, rows[site_index.deck_ids[rows] != deck_id], scores[site_index.deck_ids[rows] != deck_id])
        site_pick = next((s for s in site_decks[0].similar_decks if source == 'Gatherling' or (s.reviewed and s.archetype_id is not None)), None)
        if source == 'Gatherling' and site_decks[0].similar_decks and site_decks[0].similar_decks[0].archetype_id is None:
            unlabelled_top.append(deck_id)
        ours_used = ours_pick if ours_pick and ours_pick.score >= SITE_THRESHOLD else None
        if (ours_used.deck_id if ours_used else None) != (site_pick.id if site_pick else None):
            # Tied scores are ordered by deck id here and by active date and finish on the site; often the tied decks are twins with one label.
            (label_differs if (ours_used.label_id if ours_used else None) != (site_pick.archetype_id if site_pick else None) else deck_differs).append(deck_id)
    print(f'\nChecked {len(league)} League and {len(gatherling)} Gatherling decks. The match differs but the label is the same for {len(deck_differs)}: {deck_differs}. '
          f'The label differs for {len(label_differs)}: {label_differs}. Gatherling decks whose top site match is unlabelled: {len(unlabelled_top)}: {unlabelled_top}.')
