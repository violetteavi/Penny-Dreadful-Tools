"""Embedding checks: card pairs whose place in each other's neighbour lists we know, as a report on any card similarity.

Each check reads one card's neighbour list and finds where another card ranks in it. A check that fails is reported, never raised: a representation
can fail one and still be the best available, so the caller decides what to do (the create_combined_embedding command warns).
"""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from archetype_classifier.card_embeddings.neighbours import Neighbour, Similarities, build_neighbours, build_rank
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

# The checks agreed in #41 (2026-10-07), from the #7 readings. Every card is real and legal by season 39.
CHECKS = (
    Check('Seized from Slumber', 'Luminous Rebuke', 'identical'),  # Functional reprints: same masked text, same numbers.
    Check('Llanowar Elves', 'Elvish Mystic', 'identical'),
    Check('Llanowar Elves', 'Fyndhorn Elves', 'identical'),
    Check('Lightning Strike', 'Searing Spear', 'identical'),
    Check('Seized from Slumber', 'Swift Response', 'near'),  # Same job; collapsed under average thirds in #7, so expected to warn.
    Check('Shock', 'Burst Lightning', 'near'),
    Check('Burst Lightning', 'Shivan Fire', 'near'),  # The user's reading in #7: true neighbours.
    Check('Burst Lightning', 'Roil Eruption', 'near'),
    Check('Kalonian Tusker', 'Werewolf Pack Leader', 'near'),
    Check('Kalonian Tusker', 'Jibbirik Omnivore', 'near'),
    Check('Eater of Virtue', 'Bonesplitter', 'near'),  # Rank 108 in #7 stage 2e, so expected to warn.
    Check('Llanowar Elves', 'Leaf Gilder', 'near'),
    Check('Shock', 'Explosive Welcome', 'far'),  # Shared role in the text, nine mana apart.
)

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
    if missing := next((name for name in (check.card, check.other) if name not in cards.names), None):
        return CheckResult(check, None, None, False, f'{missing} is not in these cards')
    i, j = cards.names.index(check.card), cards.names.index(check.other)
    similarity = float(cards.similarities(i, i + 1)[0, j])
    rank = build_rank(cards, check.card, check.other)
    listed = f"{check.other} is #{rank} in {check.card}'s list; expected"
    if check.expectation == 'identical':
        passed = similarity >= 1 - TOLERANCE
        message = f"{check.other}'s similarity to {check.card} is {similarity:.5f}; expected identical (at least {1 - TOLERANCE:.5f})"
    elif check.expectation == 'far':
        passed, message = rank > FAR_RANK, f'{listed} beyond {FAR_RANK}'
    else:
        passed, message = rank <= NEAR_RANK, f'{listed} in the top {NEAR_RANK}'
    return CheckResult(check, rank, similarity, passed, message)

def build_check_lists(cards: Similarities, checks: Sequence[Check], n: int) -> dict[str, list[Neighbour]]:
    """The top n neighbours of each checked card, once per card, for reading beside the results; cards not in these cards are skipped."""
    return {card: build_neighbours(cards, card, n) for card in dict.fromkeys(c.card for c in checks) if card in cards.names}
