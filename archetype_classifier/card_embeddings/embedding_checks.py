"""Embedding checks: card pairs whose place in each other's neighbour lists we know, as a report on any card similarity.

Each check reads one card's neighbour list and finds where another card ranks in it. A check that fails is reported, never raised: a representation
can fail one and still be the best available, so the caller decides what to do (the create_combined_embedding command warns).
"""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from archetype_classifier.card_embeddings.neighbours import Similarities, build_rank
from archetype_classifier.card_embeddings.text_embedding import TOLERANCE

Expectation = Literal['identical', 'near', 'far']
NEAR_RANK = 10  # near: the other card is in the top 10 of the card's list.
FAR_RANK = 100  # far: it ranks beyond 100.
# identical: the two cards' similarity is within TOLERANCE of 1.


@dataclass(frozen=True)
class Check:
    card: str  # Whose neighbour list is read.
    other: str  # Where it ranks in that list.
    expectation: Expectation

@dataclass(frozen=True)
class CheckResult:
    check: Check
    rank: int | None
    similarity: float | None
    passed: bool
    message: str


def build_check_results(cards: Similarities, checks: Sequence[Check]) -> list[CheckResult]:
    return [build_check_result(cards, check) for check in checks]

def build_check_result(cards: Similarities, check: Check) -> CheckResult:
    i, j = cards.names.index(check.card), cards.names.index(check.other)
    similarity = float(cards.similarities(i, i + 1)[0, j])
    rank = build_rank(cards, check.card, check.other)
    if check.expectation == 'identical':
        passed = similarity >= 1 - TOLERANCE
        message = f"{check.other}'s similarity to {check.card} is {similarity:.5f}; expected identical (at least {1 - TOLERANCE:.5f})"
    else:
        if check.expectation == 'far':
            passed, expected = rank > FAR_RANK, f'beyond {FAR_RANK}'
        else:
            passed, expected = rank <= NEAR_RANK, f'in the top {NEAR_RANK}'
        message = f"{check.other} is #{rank} in {check.card}'s list; expected {expected}"
    return CheckResult(check, rank, similarity, passed, message)
