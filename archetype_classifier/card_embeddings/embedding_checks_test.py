import numpy as np
import pytest

from archetype_classifier.card_embeddings.embedding_checks import Check, build_check_results
from archetype_classifier.card_embeddings.text_embedding import TOLERANCE


class Ranked:
    """A Similarities where card's neighbour list is exactly the given cards in order: the n-th has similarity 1 - n / 1000. Fillers are not cards."""
    def __init__(self, card: str, in_order: list[str]) -> None:
        self.names = tuple(sorted([card, *in_order]))
        self.matrix = np.eye(len(self.names))
        i = self.names.index(card)
        for n, other in enumerate(in_order, 1):
            j = self.names.index(other)
            self.matrix[i, j] = self.matrix[j, i] = 1 - n / 1000

    def similarities(self, start: int, stop: int) -> np.ndarray:
        return self.matrix[start:stop]

class Paired:
    """Two cards with a given similarity."""
    def __init__(self, card: str, other: str, similarity: float) -> None:
        self.names = tuple(sorted([card, other]))
        self.matrix = np.array([[1, similarity], [similarity, 1]])

    def similarities(self, start: int, stop: int) -> np.ndarray:
        return self.matrix[start:stop]

def fillers(n: int) -> list[str]:
    return [f'filler {i:03}' for i in range(1, n + 1)]


def test_near_passes_at_rank_10_and_fails_at_rank_11() -> None:
    near = Check('Shock', 'Burst Lightning', 'near')
    [at_10] = build_check_results(Ranked('Shock', [*fillers(9), 'Burst Lightning']), [near])
    [at_11] = build_check_results(Ranked('Shock', [*fillers(10), 'Burst Lightning']), [near])
    assert (at_10.passed, at_10.rank, at_10.similarity) == (True, 10, pytest.approx(0.990))
    assert (at_11.passed, at_11.rank) == (False, 11)
    assert at_11.message == "Burst Lightning is #11 in Shock's list; expected in the top 10"


def test_far_fails_at_rank_100_and_passes_at_rank_101() -> None:
    far = Check('Shock', 'Explosive Welcome', 'far')
    [at_100] = build_check_results(Ranked('Shock', [*fillers(99), 'Explosive Welcome']), [far])
    [at_101] = build_check_results(Ranked('Shock', [*fillers(100), 'Explosive Welcome']), [far])
    assert (at_100.passed, at_100.rank) == (False, 100)
    assert at_100.message == "Explosive Welcome is #100 in Shock's list; expected beyond 100"
    assert (at_101.passed, at_101.rank) == (True, 101)


def test_identical_passes_within_the_tolerance_of_1_and_fails_beyond_it() -> None:
    identical = Check('Seized from Slumber', 'Luminous Rebuke', 'identical')
    [within] = build_check_results(Paired('Seized from Slumber', 'Luminous Rebuke', 1 - TOLERANCE), [identical])
    [beyond] = build_check_results(Paired('Seized from Slumber', 'Luminous Rebuke', 1 - 2 * TOLERANCE), [identical])
    assert within.passed
    assert not beyond.passed
    assert beyond.message == "Luminous Rebuke's similarity to Seized from Slumber is 0.99998; expected identical (at least 0.99999)"


@pytest.mark.parametrize(('check', 'missing'), [
    (Check("Ajani's Response", 'Seized from Slumber', 'identical'), "Ajani's Response"),
    (Check('Shock', "Ajani's Response", 'near'), "Ajani's Response"),
])
def test_a_check_whose_card_is_missing_fails_with_a_message_and_never_raises(check: Check, missing: str) -> None:
    [result] = build_check_results(Paired('Shock', 'Seized from Slumber', 0.5), [check])
    assert (result.passed, result.rank, result.similarity) == (False, None, None)
    assert result.message == f'{missing} is not in these cards'
