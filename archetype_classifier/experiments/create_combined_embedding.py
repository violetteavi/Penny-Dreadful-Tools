"""The #41 command: build a combined embedding over the ever-legal cards, save it beside the other embeddings, and report the embedding checks.

Every argument is required. --weights takes four non-negative numbers (text, mana value, colour, stats); only their ratios matter. Seasons take
ranges and single seasons, such as 1-3,6-8,10. A failed check is logged as a warning, never fatal: the checks report on the representation,
and the tests are what check the code. The results go to <stem>.checks.json beside the embedding.

    uv run --group archetypes python -m archetype_classifier.experiments.create_combined_embedding \\
        --encoder potion --recipe masked --approach average --weights 3,1,1,1 --fit-seasons 1-38 --embedded-seasons 1-39
"""
import argparse
import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import get_args

from archetype_classifier.card_embeddings.combined_embedding import CombinedEmbeddingSettings, CombinedEmbeddingWeights, CombiningApproach, build_combined_embedding, build_season_set, save_combined_embedding
from archetype_classifier.card_embeddings.embedding_checks import CHECKS, build_check_lists, build_check_results
from archetype_classifier.card_embeddings.encoders import ENCODERS, load_encoder
from archetype_classifier.card_embeddings.pool import load_card_pool
from archetype_classifier.card_embeddings.text import RECIPES
from archetype_classifier.card_embeddings.text_embedding import EMBEDDINGS_DIR

logger = logging.getLogger(__name__)
LIST_SIZE = 10


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--encoder', required=True, choices=sorted(ENCODERS))
    parser.add_argument('--recipe', required=True, choices=sorted(RECIPES))
    parser.add_argument('--approach', required=True, choices=get_args(CombiningApproach))
    parser.add_argument('--weights', required=True, help='text, mana value, colour, stats, e.g. 3,1,1,1')
    parser.add_argument('--fit-seasons', required=True, help='the seasons whose cards the statistics are fitted on, e.g. 1-38')
    parser.add_argument('--embedded-seasons', required=True, help='the seasons whose cards are embedded, e.g. 1-39')
    parser.add_argument('--dir', type=Path, default=EMBEDDINGS_DIR)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    weights = CombinedEmbeddingWeights(*(float(w) for w in args.weights.split(',')))
    settings = CombinedEmbeddingSettings(args.encoder, RECIPES[args.recipe], build_season_set(args.fit_seasons), build_season_set(args.embedded_seasons))
    start = time.perf_counter()
    embedding = build_combined_embedding(load_card_pool(), settings, args.approach, weights, load_encoder(args.encoder))
    path = save_combined_embedding(embedding, args.dir)
    seconds = time.perf_counter() - start
    print(f'{len(embedding.names)} cards in {seconds:.0f} s, saved to {path}')

    results = build_check_results(embedding, CHECKS)
    for result in results:
        if result.passed:
            print(f'pass  {result.message}')
        else:
            logger.warning(result.message)
    lists = build_check_lists(embedding, CHECKS, LIST_SIZE)
    for card, neighbours in lists.items():
        print(f'\n{card}')
        for i, n in enumerate(neighbours, 1):
            print(f'{i:3}  {n.similarity:.3f}  {n.name}')

    report = {'embedding': path.name, 'cards': len(embedding.names), 'seconds': round(seconds, 1),
              'passed': sum(r.passed for r in results), 'checks': [{**asdict(r.check), 'rank': r.rank, 'similarity': r.similarity, 'passed': r.passed,
                                                                    'message': r.message} for r in results],
              'lists': {card: [[n.name, round(n.similarity, 4)] for n in neighbours] for card, neighbours in lists.items()}}
    checks_path = path.with_name(f'{path.stem}.checks.json')
    checks_path.write_text(json.dumps(report, indent=1))
    print(f'\n{report["passed"]} of {len(results)} checks passed; results in {checks_path}')


if __name__ == '__main__':
    main()
