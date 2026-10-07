import pytest

from archetype_classifier.card_embeddings.combined_embedding import CombinedEmbeddingWeights


def values(weights: CombinedEmbeddingWeights) -> tuple[float, float, float, float]:
    return weights.text, weights.mana_value, weights.colour, weights.stats


def test_weights_keep_only_their_ratios_normalised_over_all_four() -> None:
    assert values(CombinedEmbeddingWeights(3, 1, 1, 1)) == pytest.approx((1 / 2, 1 / 6, 1 / 6, 1 / 6))
    assert values(CombinedEmbeddingWeights(1 / 2, 1 / 6, 1 / 6, 1 / 6)) == pytest.approx(values(CombinedEmbeddingWeights(3, 1, 1, 1)))
