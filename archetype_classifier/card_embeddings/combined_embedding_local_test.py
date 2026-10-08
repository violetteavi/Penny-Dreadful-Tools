"""The combined embedding against the real card pool and potion. Skipped unless PD_LOCAL_DATA=1 and the archetypes dependency group is installed.
Check results are printed, not asserted: they report on the representation rather than test the code.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/card_embeddings/combined_embedding_local_test.py
"""
import os
import random
from pathlib import Path

import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined_embedding import CombinedEmbedding, CombinedEmbeddingSettings, CombinedEmbeddingWeights, build_combined_embedding, build_season_set, load_combined_embedding, save_combined_embedding
from archetype_classifier.card_embeddings.embedding_checks import CHECKS, build_check_results
from archetype_classifier.card_embeddings.encoders import load_encoder
from archetype_classifier.card_embeddings.pool import Card, load_card_pool
from archetype_classifier.card_embeddings.text import MASKED

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local setup: set PD_LOCAL_DATA=1')
pytest.importorskip('sentence_transformers')

SAMPLE = 1000  # Cards legal in seasons 1-39 that the embedding is built over, besides the check cards.
CHECK_CARDS = sorted({name for check in CHECKS for name in (check.card, check.other)})
SETTINGS = CombinedEmbeddingSettings('potion', MASKED, build_season_set('1-38'), build_season_set('1-39'))


@pytest.fixture(scope='module')
def sample() -> list[Card]:
    pool = {c.name: c for c in load_card_pool()}
    embedded = sorted(n for n, c in pool.items() if c.seasons & SETTINGS.embedded_seasons)
    names = set(random.Random(7).sample(embedded, SAMPLE)) | {n for n in CHECK_CARDS if n in pool}
    return [pool[n] for n in sorted(names)]

@pytest.fixture(scope='module')
def embedding(sample: list[Card]) -> CombinedEmbedding:
    return build_combined_embedding(sample, SETTINGS, 'average', CombinedEmbeddingWeights(3, 1, 1, 1), load_encoder('potion'))


def test_every_check_card_is_in_the_embedding(embedding: CombinedEmbedding) -> None:
    assert [n for n in CHECK_CARDS if n not in embedding.names] == []
    for result in build_check_results(embedding, CHECKS):
        print(f"{'pass' if result.passed else 'FAIL'}  {result.message}")

def test_a_saved_embedding_loads_back_with_identical_similarities(embedding: CombinedEmbedding, tmp_path: Path) -> None:
    loaded = load_combined_embedding(save_combined_embedding(embedding, tmp_path))
    assert loaded.names == embedding.names
    assert np.array_equal(loaded.similarities(0, len(loaded.names)), embedding.similarities(0, len(embedding.names)))
