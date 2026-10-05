import pytest

from archetype_classifier.card_embeddings.encoders import ENCODERS, load_encoder


def test_every_encoder_is_pinned_to_a_full_revision() -> None:
    assert set(ENCODERS) == {'bge-small', 'bge-base', 'potion', 'minilm'}
    assert all(len(spec.revision) == 40 for spec in ENCODERS.values())

def test_an_unknown_encoder_is_named_in_the_error_with_the_known_ones() -> None:
    with pytest.raises(ValueError, match='No encoder called bge-large; known: bge-base, bge-small, minilm, potion'):
        load_encoder('bge-large')
