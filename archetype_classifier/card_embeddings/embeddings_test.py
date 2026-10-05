import hashlib
from collections.abc import Sequence

import numpy as np

from archetype_classifier.card_embeddings.embeddings import TOLERANCE, build_embeddings
from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import BASE, STATS, TEXT_VERSION


class FakeEncoder:
    """Deterministic and torch-free: each text becomes a fixed vector derived from its hash, and a token is a word."""
    name = 'fake'
    revision = 'r1'
    max_tokens = 4

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
    build_embeddings([SHOCK], STATS, encoder)
    assert encoder.seen == ['{R} · Instant\nShock deals 2 damage to any target.']

def test_the_manifest_says_how_the_embeddings_were_made_and_how_many_cards_ran_past_the_token_limit() -> None:
    embeddings = build_embeddings([SHOCK, OPT, CANCEL], BASE, FakeEncoder())
    assert embeddings.manifest == {'encoder': 'fake', 'revision': 'r1', 'recipe': {'stats': False, 'mask': False}, 'text_version': TEXT_VERSION,
                                   'cards': 3, 'max_tokens': 4, 'over_token_limit': 2}  # 'Instant Shock deals …' and 'Instant Scry 1. Draw …'.


# Scenario: adding a set changes no other card's vector (Scenarios.md, "Card representation").

def test_adding_cards_leaves_every_existing_row_within_the_tolerance() -> None:
    before = build_embeddings([SHOCK, OPT], BASE, FakeEncoder())
    after = build_embeddings([SHOCK, OPT, CANCEL], BASE, FakeEncoder())
    rows = {n: after.matrix[i] for i, n in enumerate(after.names)}
    assert all(np.allclose(before.matrix[i], rows[n], atol=TOLERANCE, rtol=0) for i, n in enumerate(before.names))
