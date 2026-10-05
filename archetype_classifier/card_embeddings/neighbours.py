"""A card's nearest neighbours in a set of card embeddings, by cosine similarity.

    uv run python -m archetype_classifier.card_embeddings.neighbours "Shock" --encoder bge-small -n 10 [--recipe stats] [--season 43]
"""
import argparse
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path

from archetype_classifier.card_embeddings.embeddings import EMBEDDINGS_DIR, Embeddings, embeddings_path, load_embeddings
from archetype_classifier.card_embeddings.text import RECIPES
from archetype_classifier.data_loading import loader


@dataclass(frozen=True)
class Neighbour:
    name: str
    similarity: float


def build_neighbours(embeddings: Embeddings, card: str, n: int, among: Collection[str] | None = None) -> list[Neighbour]:
    """The n cards most similar to the card, best first, ties broken by name; the card itself is left out. among limits the cards searched."""
    if card not in embeddings.names:
        raise ValueError(f'{card} is not in these embeddings')
    similarities = embeddings.matrix @ embeddings.matrix[embeddings.names.index(card)]  # Rows are unit length, so a dot product is the cosine.
    candidates = [(float(s), name) for name, s in zip(embeddings.names, similarities) if name != card and (among is None or name in among)]
    return [Neighbour(name, s) for s, name in sorted(candidates, key=lambda c: (-c[0], c[1]))[:n]]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Print a card\'s nearest neighbours from saved card embeddings.')
    parser.add_argument('card', help='the card\'s name as the site writes it, e.g. "Discovery // Dispersal"')
    parser.add_argument('--encoder', default='bge-small')
    parser.add_argument('--recipe', default='base', choices=sorted(RECIPES))
    parser.add_argument('-n', type=int, default=10, help='how many neighbours')
    parser.add_argument('--season', type=int, help='only cards legal in this season')
    parser.add_argument('--dir', type=Path, default=EMBEDDINGS_DIR)
    args = parser.parse_args(argv)
    path = embeddings_path(args.dir, args.encoder, RECIPES[args.recipe])
    if not path.exists():
        raise SystemExit(f'No embeddings at {path}: build them with python -m archetype_classifier.experiments.card_encoders')
    embeddings = load_embeddings(path)
    among = loader.load_legal_cards([args.season])[args.season] if args.season else None
    heading = f'{args.card}: {args.encoder}, {args.recipe}, {len(embeddings.names)} cards'
    print(heading + (f', among the {len(among)} legal in season {args.season}' if among is not None else ''))
    for i, n in enumerate(build_neighbours(embeddings, args.card, args.n, among), 1):
        print(f'{i:3}  {n.similarity:.3f}  {n.name}')


if __name__ == '__main__':
    main()
