import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest

from archetype_classifier.card_embeddings.embeddings import TOLERANCE, build_embeddings, load_embeddings, merge_embeddings, save_embeddings
from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import BASE, MASKED, TEXT_VERSION


class FakeEncoder:
    """Deterministic and torch-free: each text becomes a fixed vector derived from its hash, and a token is a word."""
    name = 'fake'
    revision = 'r1'
    max_tokens: int | None = 4

    def __init__(self) -> None:
        self.seen: list[str] = []

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        self.seen.extend(texts)
        return np.array([np.frombuffer(hashlib.sha256(t.encode()).digest(), dtype=np.uint8)[:8].astype(np.float32) + 1 for t in texts])

    def token_counts(self, texts: Sequence[str]) -> list[int]:
        return [len(t.split()) for t in texts]

def card(name: str, oracle_text: str) -> Card:
    return Card(name, 'normal', (Face(name, '{R}', 1, 'Instant', oracle_text),))

SHOCK = card('Shock', 'Shock deals 2 damage to any target.')
OPT = card('Opt', 'Scry 1.\nDraw a card.')
CANCEL = card('Cancel', 'Counter target spell.')


def test_rows_follow_the_cards_names_in_order_and_are_unit_length() -> None:
    embeddings = build_embeddings([SHOCK, OPT, CANCEL], BASE, FakeEncoder())
    assert embeddings.names == ('Cancel', 'Opt', 'Shock')
    assert embeddings.matrix.shape == (3, 8)
    assert np.allclose(np.linalg.norm(embeddings.matrix, axis=1), 1)

def test_the_encoder_reads_the_recipes_text() -> None:
    encoder = FakeEncoder()
    build_embeddings([SHOCK], MASKED, encoder)
    assert encoder.seen == ['Instant\n~ deals 2 damage to any target.']

def test_the_manifest_says_how_the_embeddings_were_made_and_how_many_cards_ran_past_the_token_limit() -> None:
    embeddings = build_embeddings([SHOCK, OPT, CANCEL], BASE, FakeEncoder())
    assert embeddings.manifest == {'encoder': 'fake', 'revision': 'r1', 'recipe': {'style': 'plain', 'mask': False}, 'text_version': TEXT_VERSION,
                                   'cards': 3, 'max_tokens': 4, 'over_token_limit': 2}  # 'Instant Shock deals …' and 'Instant Scry 1. Draw …'.


# Scenario: adding a set changes no other card's vector (Scenarios.md, "Card representation").

def test_adding_cards_leaves_every_existing_row_within_the_tolerance() -> None:
    before = build_embeddings([SHOCK, OPT], BASE, FakeEncoder())
    after = build_embeddings([SHOCK, OPT, CANCEL], BASE, FakeEncoder())
    rows = {n: after.matrix[i] for i, n in enumerate(after.names)}
    assert all(np.allclose(before.matrix[i], rows[n], atol=TOLERANCE, rtol=0) for i, n in enumerate(before.names))


def test_saved_embeddings_load_back_the_same_from_a_file_named_by_encoder_and_recipe(tmp_path: Path) -> None:
    embeddings = build_embeddings([SHOCK, OPT, CANCEL], MASKED, FakeEncoder())
    path = save_embeddings(embeddings, tmp_path)
    assert path == tmp_path / 'fake__masked.npy' and (tmp_path / 'fake__masked.json').exists()
    loaded = load_embeddings(path)
    assert loaded.names == embeddings.names and loaded.manifest == embeddings.manifest
    assert np.array_equal(loaded.matrix, embeddings.matrix)

def test_a_manifest_that_doesnt_match_its_matrix_fails_and_names_the_file(tmp_path: Path) -> None:
    path = save_embeddings(build_embeddings([SHOCK, OPT], BASE, FakeEncoder()), tmp_path)
    manifest_path = tmp_path / 'fake__base.json'
    saved = json.loads(manifest_path.read_text())
    saved['names'].append('Cancel')
    manifest_path.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match='fake__base.npy has 2 rows but its manifest lists 3 cards'):
        load_embeddings(path)

def test_an_encoder_with_no_token_limit_cuts_off_no_card() -> None:
    encoder = FakeEncoder()
    encoder.max_tokens = None
    manifest = build_embeddings([SHOCK, OPT, CANCEL], BASE, encoder).manifest
    assert (manifest['max_tokens'], manifest['over_token_limit']) == (None, 0)


# Adding a set: embed only the new cards and merge them in.

def test_merging_puts_both_sets_of_rows_in_name_order_and_sums_the_manifests() -> None:
    old, new = build_embeddings([SHOCK, OPT], BASE, FakeEncoder()), build_embeddings([CANCEL], BASE, FakeEncoder())
    merged = merge_embeddings(old, new)
    whole = build_embeddings([SHOCK, OPT, CANCEL], BASE, FakeEncoder())
    assert merged.names == whole.names and merged.manifest == whole.manifest
    assert np.allclose(merged.matrix, whole.matrix, atol=TOLERANCE, rtol=0)

def test_merging_embeddings_from_different_encoders_or_recipes_fails() -> None:
    with pytest.raises(ValueError, match='Only embeddings from the same encoder, revision, recipe and text version can be merged'):
        merge_embeddings(build_embeddings([SHOCK], BASE, FakeEncoder()), build_embeddings([OPT], MASKED, FakeEncoder()))

def test_merging_a_card_already_there_fails() -> None:
    with pytest.raises(ValueError, match='Already embedded: Shock'):
        merge_embeddings(build_embeddings([SHOCK], BASE, FakeEncoder()), build_embeddings([SHOCK, OPT], BASE, FakeEncoder()))
