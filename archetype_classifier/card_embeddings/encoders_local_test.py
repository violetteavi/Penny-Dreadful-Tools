"""The real encoders. Skipped unless PD_LOCAL_DATA=1 and the archetypes dependency group is installed (uv sync --group archetypes).
The first run downloads each model from Hugging Face.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/card_embeddings/encoders_local_test.py
"""
import os

import numpy as np
import pytest

from archetype_classifier.card_embeddings.encoders import ENCODERS, load_encoder

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local setup: set PD_LOCAL_DATA=1')
pytest.importorskip('sentence_transformers')


@pytest.mark.parametrize('name', sorted(ENCODERS))
def test_an_encoder_loads_at_its_pinned_revision_and_encodes_texts(name: str) -> None:
    encoder = load_encoder(name)
    assert (encoder.name, encoder.revision) == (name, ENCODERS[name].revision)
    vectors = encoder.encode(['Instant\nShock deals 2 damage to any target.', 'Creature — Beast'])
    assert vectors.shape == (2, ENCODERS[name].dimensions) and np.isfinite(vectors).all()
    counts = encoder.token_counts(['Creature — Beast', 'Creature — Beast ' * 400])
    print(f'\n{name}: max_tokens {encoder.max_tokens}, token counts {counts}')
    assert counts[0] < counts[1]
    assert encoder.max_tokens is None or counts[1] > encoder.max_tokens
