"""The model and run store, in the experiments database. Models are saved as their record and what fitting learned, runs as one guess per deck; never decks, never scores."""
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import JSON, FitContext, Model, Prediction, build_training_decks, model_class
from shared.database import Database

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS model (
        id INT AUTO_INCREMENT PRIMARY KEY,
        identity_hash CHAR(40) NOT NULL,
        name VARCHAR(190) NOT NULL,
        version INT NOT NULL,
        params TEXT NOT NULL,
        snapshot_id INT NOT NULL,
        scheme_id INT NOT NULL,
        seed INT NOT NULL,
        training_splits VARCHAR(100) NOT NULL,
        validation_splits VARCHAR(100) NOT NULL,
        training_count INT NOT NULL,
        training_hash CHAR(40) NOT NULL,
        validation_count INT NOT NULL,
        validation_hash CHAR(40) NOT NULL,
        state LONGTEXT NOT NULL,
        fit_seconds DOUBLE NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY (identity_hash, training_hash, validation_hash),
        FOREIGN KEY (snapshot_id) REFERENCES snapshot (id),
        FOREIGN KEY (scheme_id) REFERENCES split_scheme (id)
    )""",
]


class StoreConflict(Exception):
    """The same model on the same decks gave a different result. Nothing was stored."""

@dataclass(frozen=True)
class ModelRecord:
    """Everything that identifies a fitted model, and the decks it actually trained and tuned on."""
    name: str
    version: int
    params: dict[str, JSON]
    snapshot_id: int
    scheme_id: int
    seed: int
    training_splits: frozenset[Split]
    validation_splits: frozenset[Split]
    training_count: int
    training_hash: str  # Fingerprint of the deck ids it trained on, after skipping any with missing contents.
    validation_count: int
    validation_hash: str
    fit_seconds: float

def ensure_schema(edb: Database) -> None:
    loader.ensure_schema(edb)
    for statement in SCHEMA:
        edb.execute(statement)

def save_model(edb: Database, model: Model, record: ModelRecord) -> int:
    """Save a fitted model's record and state, and return its id. Saving the same model again returns the stored model's id."""
    ensure_schema(edb)
    identity = identity_hash(record)
    state = canonical(model.state())
    same = edb.select('SELECT id, state FROM model WHERE identity_hash = %s AND training_hash = %s AND validation_hash = %s', [identity, record.training_hash, record.validation_hash])
    if same:
        stored_id, stored_state = int(same[0]['id']), str(same[0]['state'])  # type: ignore[call-overload]
        if stored_state != state:
            raise StoreConflict(f'The same model on the same decks gave a different result: model {stored_id} learned {stored_state}, this fit learned {state}. '
                                'Make fitting deterministic (the seed must control all randomness), or bump the version.')
        return stored_id
    return edb.insert("""INSERT INTO model (identity_hash, name, version, params, snapshot_id, scheme_id, seed, training_splits, validation_splits, training_count, training_hash,
                                            validation_count, validation_hash, state, fit_seconds) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                      [identity, record.name, record.version, canonical(record.params), record.snapshot_id, record.scheme_id, record.seed, splits_text(record.training_splits),
                       splits_text(record.validation_splits), record.training_count, record.training_hash, record.validation_count, record.validation_hash,
                       state, record.fit_seconds])

def identity_hash(record: ModelRecord) -> str:
    """A model's identity: name, version, parameters, snapshot, scheme, training splits, validation splits and seed."""
    identity: JSON = [record.name, record.version, record.params, record.snapshot_id, record.scheme_id, splits_text(record.training_splits),
                      splits_text(record.validation_splits), record.seed]
    return hashlib.sha1(canonical(identity).encode()).hexdigest()

def load_model(edb: Database, model_id: int) -> tuple[ModelRecord, Model]:
    """A stored model, rebuilt from its state. Its training decks are rebuilt from the record (snapshot, scheme and training splits)."""
    row = edb.select('SELECT * FROM model WHERE id = %s', [model_id])[0]
    record = model_record(row)
    snapshot = loader.load_snapshot(edb, record.snapshot_id, record.scheme_id)
    training_set = build_deck_set(snapshot, record.training_splits, include_test=Split.TEST in record.training_splits)
    training = build_training_decks(training_set, loader.load_contents(training_set.decks))
    context = FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in snapshot.decks.values()}), record.seed)
    return record, model_class(record.name).from_state(record.params, json.loads(str(row['state'])), training, context)

def model_record(row: dict[str, Any]) -> ModelRecord:
    return ModelRecord(row['name'], row['version'], json.loads(row['params']), row['snapshot_id'], row['scheme_id'], row['seed'], splits_from_text(row['training_splits']),
                       splits_from_text(row['validation_splits']), row['training_count'], row['training_hash'], row['validation_count'], row['validation_hash'],
                       row['fit_seconds'])

def canonical(value: JSON) -> str:
    """JSON with sorted keys, so equal values are equal text."""
    return json.dumps(value, sort_keys=True)

def splits_text(splits: frozenset[Split]) -> str:
    return ','.join(sorted(s.value for s in splits))

def splits_from_text(text: str) -> frozenset[Split]:
    return frozenset(Split(s) for s in text.split(',') if s)

def prediction_hash(predictions: Sequence[Prediction]) -> str:
    """A fingerprint of a run's guesses: every deck and its guess, in any order. Evidence is left out, since scores depend only on guesses."""
    pairs = sorted((p.deck_id, -1 if p.guess_id is None else p.guess_id) for p in predictions)
    return hashlib.sha1(';'.join(f'{deck_id}:{guess_id}' for deck_id, guess_id in pairs).encode()).hexdigest()
