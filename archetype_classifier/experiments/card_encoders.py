"""The #7 experiment, stage 1: every encoder on the base recipe over the whole card pool.

For each encoder it embeds the cards legal before season 43, then the 461 cards new in season 43 on their own, and merges them, which is how a new set
would be added. It times each step, checks that embedding cards in a different batch moves no vector beyond the tolerance, runs the card-representation
scenarios, and builds neighbour lists for the chosen cards and for the most-played new cards (among older cards only). It also finds the played cards
whose neighbour lists differ most between encoders. Embeddings go to archetype_classifier/embeddings/ (gitignored); results to docs/experiments/.

    uv run --group archetypes python -m archetype_classifier.experiments.card_encoders --stage 1 --date 20261005
"""
import argparse
import json
import random
import time
from collections.abc import Sequence
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from archetype_classifier.card_embeddings.embeddings import Embeddings, build_embeddings, merge_embeddings, save_embeddings
from archetype_classifier.card_embeddings.encoders import ENCODERS, load_encoder
from archetype_classifier.card_embeddings.neighbours import build_all_neighbours, build_neighbours, build_overlap, build_rank
from archetype_classifier.card_embeddings.pool import Card, load_card_pool
from archetype_classifier.card_embeddings.text import BASE, build_card_text
from decksite.database import db

OUT = Path(__file__).parents[1] / 'docs' / 'experiments'
ORDER = ('potion', 'minilm', 'bge-small', 'bge-base')  # Fastest first.
NEW_SEASON = 43
LIST_SIZE = 10
REPRINT_GROUPS = [["Ajani's Response", 'Grounded for Life', 'Seized from Slumber', 'Luminous Rebuke'], ['Llanowar Elves', 'Elvish Mystic', 'Fyndhorn Elves']]
VANILLAS = ['Plated Seastrider', 'Kalonian Tusker', "Garruk's Gorehorn", 'Coral Eel', 'Spined Wurm']
LIST_CARDS = [
    # Edge cases from the #7 grilling.
    'Seized from Slumber', 'Swift Response', 'Llanowar Elves', 'Shock', 'Burst Lightning', 'Kalonian Tusker', 'Shatterskull Smashing',
    # The user's staples.
    'Cancel', 'Distress', "Inventor's Fair", 'Eater of Virtue', 'Kumano Faces Kakkazan', 'Discovery // Dispersal', 'Horned Loch-Whale',
    # The most-played non-land cards in seasons 39-43.
    'Chain Lightning', 'Birds of Paradise', 'Malcolm, Alluring Scoundrel', "Archmage's Charm", 'Mana Leak', 'Luminarch Aspirant',
]
NEW_CARDS_SHOWN = 12  # The most-played cards new in season 43.
PLAYED = 20  # Decks in seasons 39-43 a card needs to count as played, for the disagreement list.
DISAGREEMENT_SHOWN = 15


def load_play_counts(first_season: int, last_season: int) -> dict[str, int]:
    """How many decks in the given seasons play each card in their maindeck, using the experiment snapshot's seasons."""
    sql = '''SELECT dc.card, COUNT(DISTINCT dc.deck_id) AS decks FROM deck_card AS dc
             JOIN archetype_experiments.deck_snapshot AS d ON d.deck_id = dc.deck_id AND d.snapshot_id = 1
             WHERE dc.sideboard = 0 AND d.season_id BETWEEN %s AND %s GROUP BY dc.card'''
    return {r['card']: int(r['decks']) for r in db().select(sql, [first_season, last_season])}  # type: ignore[misc]

def timed(f: Any, *args: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    result = f(*args)
    return result, time.perf_counter() - start

def similarity(e: Embeddings, a: str, b: str) -> float:
    return float(e.matrix[e.names.index(a)] @ e.matrix[e.names.index(b)])

def neighbour_list(e: Embeddings, card: str, among: set[str] | None = None) -> list[list[Any]]:
    return [[n.name, round(n.similarity, 4)] for n in build_neighbours(e, card, LIST_SIZE, among)]

def run_encoder(name: str, old: Sequence[Card], new: Sequence[Card], new_shown: Sequence[str]) -> tuple[dict[str, Any], Embeddings]:
    encoder, load_seconds = timed(load_encoder, name)
    old_embeddings, old_seconds = timed(build_embeddings, old, BASE, encoder)
    new_embeddings, new_seconds = timed(build_embeddings, new, BASE, encoder)
    embeddings = merge_embeddings(old_embeddings, new_embeddings)
    save_embeddings(embeddings)
    rebatched = build_embeddings(random.Random(43).sample(list(old), len(new)), BASE, encoder)  # The same cards in a different batch.
    rows = dict(zip(old_embeddings.names, old_embeddings.matrix))
    batch_change = max(float(np.abs(rows[n] - v).max()) for n, v in zip(rebatched.names, rebatched.matrix))
    old_names = set(old_embeddings.names)
    result = {
        'model_id': ENCODERS[name].model_id, 'revision': ENCODERS[name].revision, 'dimensions': ENCODERS[name].dimensions,
        'max_tokens': encoder.max_tokens, 'over_token_limit': embeddings.manifest['over_token_limit'],
        'seconds': {'load': load_seconds, 'old_cards': old_seconds, 'new_cards': new_seconds}, 'cards': {'old': len(old), 'new': len(new)},
        'largest_batch_change': batch_change,
        'scenarios': {
            'reprints_lowest_similarity': [min(similarity(embeddings, g[0], other) for other in g[1:]) for g in REPRINT_GROUPS],
            'swift_response': {r: [build_rank(embeddings, r, 'Swift Response'), similarity(embeddings, r, 'Swift Response')] for r in REPRINT_GROUPS[0]},
            'shock_burst': [build_rank(embeddings, 'Shock', 'Burst Lightning'), build_rank(embeddings, 'Burst Lightning', 'Shock'),
                            similarity(embeddings, 'Shock', 'Burst Lightning')],
            'vanillas': {f'{a} / {b}': similarity(embeddings, a, b) for a, b in combinations(VANILLAS, 2)},
        },
        'lists': {card: neighbour_list(embeddings, card) for card in LIST_CARDS},
        'new_card_lists': {card: neighbour_list(embeddings, card, old_names) for card in new_shown},
    }
    print(f"{name}: loaded in {load_seconds:.0f}s; {len(old)} cards in {old_seconds:.0f}s, {len(new)} new in {new_seconds:.1f}s; "
          f"largest batch change {batch_change:.1e}; {result['over_token_limit']} cards over the token limit", flush=True)
    return result, embeddings

def build_disagreement(all_embeddings: dict[str, Embeddings], played: set[str]) -> dict[str, Any]:
    """How much the encoders' top-10 lists overlap: on average per pair, and for the played cards they agree on least."""
    tops = {name: build_all_neighbours(e, LIST_SIZE) for name, e in all_embeddings.items()}
    names = next(iter(all_embeddings.values())).names
    pairs = {f'{a} / {b}': build_overlap(tops[a], tops[b]) for a, b in combinations(all_embeddings, 2)}
    mean_by_card = np.mean(list(pairs.values()), axis=0)
    candidates = [i for i, n in enumerate(names) if n in played]
    least = sorted(candidates, key=lambda i: (mean_by_card[i], names[i]))[:DISAGREEMENT_SHOWN]
    return {
        'mean_overlap_by_pair': {p: float(v.mean()) for p, v in pairs.items()},
        'played_cards': len(candidates),
        'least_agreed': [{'card': names[i], 'mean_overlap': float(mean_by_card[i]),
                          'lists': {enc: [names[j] for j in tops[enc][i]] for enc in all_embeddings}} for i in least],
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--stage', type=int, choices=[1], required=True)
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the results file name')
    args = parser.parse_args()

    pool = load_card_pool()
    new = [c for c in pool if min(c.seasons) == NEW_SEASON]
    old = [c for c in pool if min(c.seasons) < NEW_SEASON]
    recent, latest = load_play_counts(39, NEW_SEASON), load_play_counts(NEW_SEASON, NEW_SEASON)
    new_shown = sorted((c.name for c in new if latest.get(c.name)), key=lambda n: (-latest[n], n))[:NEW_CARDS_SHOWN]
    print(f'{len(pool)} cards: {len(old)} before season {NEW_SEASON}, {len(new)} new in it', flush=True)

    results: dict[str, Any] = {'stage': 1, 'recipe': BASE.label, 'pool': len(pool), 'list_cards': LIST_CARDS,
                               'new_cards_shown': {n: latest[n] for n in new_shown}, 'card_text': {}, 'encoders': {}}
    by_name = {c.name: c for c in pool}
    all_embeddings = {}
    for name in ORDER:
        results['encoders'][name], all_embeddings[name] = run_encoder(name, old, new, new_shown)
    shown = set(LIST_CARDS) | set(new_shown) | {n for r in results['encoders'].values() for lists in (r['lists'], r['new_card_lists']) for ns in lists.values() for n, _ in ns}
    results['disagreement'] = build_disagreement(all_embeddings, {n for n, decks in recent.items() if decks >= PLAYED})
    shown |= {n for d in results['disagreement']['least_agreed'] for ns in [[d['card']], *d['lists'].values()] for n in ns}
    results['card_text'] = {n: build_card_text(by_name[n], BASE) for n in sorted(shown)}

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{args.date}_card_encoders_stage{args.stage}.json'
    path.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f'Wrote {path}')

if __name__ == '__main__':
    main()
