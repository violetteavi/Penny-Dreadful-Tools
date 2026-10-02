"""Scoring rows from a run's stored guesses, against a real experiments database."""
from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.data_loading.slices import DeckSet, build_deck_set
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation.metrics import ArchetypeTree, ScoredDeck, score
from archetype_classifier.evaluation.model import Prediction
from archetype_classifier.evaluation.rows import build_rows, score_rows
from archetype_classifier.evaluation.rows_test import MAINDECK_A, RED_DECK_WINS, SNAPSHOT
from archetype_classifier.evaluation.store import ModelRecord, save_model, save_run
from archetype_classifier.models.most_common import MostCommonArchetype
from shared.database import Database

AZORIUS_CONTROL = 49
TREE = ArchetypeTree({RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', None, 0), AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', None, 0)})
TRAIN, VALIDATION = frozenset({Split.TRAIN}), frozenset({Split.VALIDATION})
GUESSES = {101: RED_DECK_WINS, 102: AZORIUS_CONTROL, 301: RED_DECK_WINS, 302: AZORIUS_CONTROL, 201: RED_DECK_WINS, 202: None,
           401: RED_DECK_WINS, 402: AZORIUS_CONTROL, 403: RED_DECK_WINS, 404: RED_DECK_WINS}  # Every deck is labelled Red Deck Wins.


def run(edb: Database, scope: frozenset[Split], guesses: dict[int, int | None] = GUESSES) -> int:
    """A stored run of a stored model, with the given guesses for the scope's decks."""
    loader.ensure_schema(edb)
    edb.execute("INSERT INTO snapshot (id, deck_count, max_deck_id, notes) VALUES (1, 0, 0, 'test')")
    scheme_id = loader.create_scheme(edb, SplitScheme('typical'))
    record = ModelRecord('most common archetype', 1, {}, 1, scheme_id, 0, TRAIN, VALIDATION, 2, 'a' * 40, 2, 'b' * 40, 0.0)
    model_id = save_model(edb, MostCommonArchetype({}), record)
    in_scope = [i for i, d in SNAPSHOT.decks.items() if d.split in scope and i in guesses]
    return save_run(edb, model_id, scope, [Prediction(i, guesses[i], {}) for i in in_scope])

def scored(splits: frozenset[Split]) -> DeckSet:
    return build_deck_set(SNAPSHOT, splits, include_test=Split.TEST in splits)


# Scenarios: scoring held-out and validation decks gives their rows; rows the model tuned on are flagged.

def test_each_row_is_scored_from_the_stored_guesses_and_flagged_for_training_and_tuning(experiments_db: Database) -> None:
    splits = frozenset({Split.HELD_OUT, Split.VALIDATION})
    run_id = run(experiments_db, splits)
    rows = build_rows(scored(splits), scored(TRAIN), SNAPSHOT.scheme)
    results = score_rows(experiments_db, run_id, TREE, scored(splits), rows, TRAIN, VALIDATION, min_decks=1)

    assert results['validation'].scores == score(TREE, [ScoredDeck(201, RED_DECK_WINS, RED_DECK_WINS, MAINDECK_A), ScoredDeck(202, RED_DECK_WINS, None, f'{202:040x}')], min_decks=1)
    assert {name: (r.trained_on, r.tuned_on) for name, r in results.items()} == {
        'held-out, no unseen cards': (False, False), 'held-out, unseen cards': (False, False),
        'validation': (False, True), 'validation, new maindeck': (False, True), 'validation, repeated maindeck': (False, True)}
    tuned_on_held_out_too = score_rows(experiments_db, run_id, TREE, scored(splits), rows, TRAIN, splits, min_decks=1)
    assert all(r.tuned_on for r in tuned_on_held_out_too.values())
