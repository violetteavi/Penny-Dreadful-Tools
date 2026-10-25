"""Deck diffs (#62; 20261024_Deck_Diffs_Architecture.pdf): a deck D against a training row T, whose label is the target archetype.

A diff goes copy by copy: a card at 4 copies in T and 2 in D keeps 2 and removes 2.
"""
from dataclasses import dataclass

from archetype_classifier.data_loading.dataset import CardCount


@dataclass(frozen=True)
class DeckDiff:
    kept: tuple[CardCount, ...]  # Copies in both, in name order.
    removed: tuple[CardCount, ...]  # T's copies that D lacks.
    added: tuple[CardCount, ...]  # D's copies that T lacks.


def build_deck_diff(target: tuple[CardCount, ...], deck: tuple[CardCount, ...]) -> DeckDiff:
    before = {line.card: line.n for line in target}
    after = {line.card: line.n for line in deck}
    cards = sorted(before.keys() | after.keys())

    def lines(count: dict[str, int]) -> tuple[CardCount, ...]:
        return tuple(CardCount(card, count[card]) for card in cards if count.get(card, 0) > 0)
    return DeckDiff(lines({c: min(before.get(c, 0), after.get(c, 0)) for c in cards}), lines({c: before.get(c, 0) - after.get(c, 0) for c in cards}),
                    lines({c: after.get(c, 0) - before.get(c, 0) for c in cards}))
