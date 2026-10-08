"""A card's nearest neighbours by any similarity over a set of cards: card embeddings' cosine, or a combined similarity (combined.py).

    uv run python -m archetype_classifier.card_embeddings.neighbours "Shock" -n 10 [--encoder potion] [--recipe masked] [--season 43]
    uv run python -m archetype_classifier.card_embeddings.neighbours "Shock" -n 10 --combined potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39
"""
import argparse
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from archetype_classifier.card_embeddings.text import RECIPES
from archetype_classifier.card_embeddings.text_embedding import EMBEDDINGS_DIR, load_text_embeddings, text_embeddings_path
from archetype_classifier.data_loading import loader


class Similarities(Protocol):
    """Cards in name order, and the similarity of a block of them to every card."""
    @property
    def names(self) -> tuple[str, ...]: ...

    def similarities(self, start: int, stop: int) -> np.ndarray: ...

@dataclass(frozen=True)
class Neighbour:
    name: str
    similarity: float


def build_neighbours(cards: Similarities, card: str, n: int, among: Collection[str] | None = None) -> list[Neighbour]:
    """The n cards most similar to the card, best first, ties broken by name; the card itself is left out. among limits the cards searched."""
    if card not in cards.names:
        raise ValueError(f'{card} is not in these embeddings')
    i = cards.names.index(card)
    similarities = cards.similarities(i, i + 1)[0]
    candidates = [(float(s), name) for name, s in zip(cards.names, similarities) if name != card and (among is None or name in among)]
    return [Neighbour(name, s) for s, name in sorted(candidates, key=lambda c: (-c[0], c[1]))[:n]]


def build_rank(cards: Similarities, card: str, other: str) -> int:
    """Where other comes in card's neighbour list, counting from 1."""
    return [n.name for n in build_neighbours(cards, card, len(cards.names))].index(other) + 1

def build_all_neighbours(cards: Similarities, n: int, chunk: int = 1000) -> np.ndarray:
    """Every card's n nearest neighbours as row indices, one row per card, in build_neighbours' order. Cards must be in name order (as built), so
    that breaking ties by index breaks them by name. Cards are compared a chunk at a time to keep memory down."""
    top = np.empty((len(cards.names), n), dtype=np.int64)
    for start in range(0, len(cards.names), chunk):
        similarities = np.array(cards.similarities(start, start + chunk), dtype=np.float64)
        rows = np.arange(similarities.shape[0])
        similarities[rows, rows + start] = -np.inf  # Leave each card out of its own list.
        nth = -np.partition(-similarities, n - 1, axis=1)[:, n - 1]  # Each row's n-th best similarity.
        for row in rows:
            candidates = np.flatnonzero(similarities[row] >= nth[row])  # Everything at least as good, ties included.
            top[start + row] = candidates[np.lexsort((candidates, -similarities[row, candidates]))][:n]
    return top

def build_overlap(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """For each row, the share of the cards in two neighbour lists that they have in common."""
    return np.array([len(set(x) & set(y)) / len(x) for x, y in zip(a.tolist(), b.tolist())])


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Print a card\'s nearest neighbours from saved card embeddings.')
    parser.add_argument('card', help='the card\'s name as the site writes it, e.g. "Discovery // Dispersal"')
    parser.add_argument('--encoder', default='potion')
    parser.add_argument('--recipe', default='base', choices=sorted(RECIPES))
    parser.add_argument('-n', type=int, default=10, help='how many neighbours')
    parser.add_argument('--season', type=int, help='only cards legal in this season')
    parser.add_argument('--combined', help='a saved combined embedding\'s file name without .npz, instead of --encoder and --recipe')
    parser.add_argument('--dir', type=Path, default=EMBEDDINGS_DIR)
    args = parser.parse_args(argv)
    embeddings: Similarities
    if args.combined:
        from archetype_classifier.card_embeddings.combined_embedding import load_combined_embedding  # noqa: PLC0415  # It imports this module.
        embeddings, described = load_combined_embedding(args.dir / f'{args.combined}.npz'), args.combined
    else:
        path = text_embeddings_path(args.dir, args.encoder, RECIPES[args.recipe])
        if not path.exists():
            raise SystemExit(f'No embeddings at {path}: build them with build_text_embeddings and save_text_embeddings (card_embeddings.text_embedding), '
                             'or pass --combined for one made by experiments.create_combined_embedding')
        embeddings, described = load_text_embeddings(path), f'{args.encoder}, {args.recipe}'
    among = loader.load_legal_cards([args.season])[args.season] if args.season else None
    heading = f'{args.card}: {described}, {len(embeddings.names)} cards'
    print(heading + (f', among the {len(among)} legal in season {args.season}' if among is not None else ''))
    for i, n in enumerate(build_neighbours(embeddings, args.card, args.n, among), 1):
        print(f'{i:3}  {n.similarity:.3f}  {n.name}')


if __name__ == '__main__':
    main()
