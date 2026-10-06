"""The #7 experiment. Stage 1: every encoder on the base recipe over the whole card pool. Stage 2: one encoder (potion) in each text format.

For each encoder it embeds the cards legal before season 43, then the 461 cards new in season 43 on their own, and merges them, which is how a new set
would be added. It times each step, checks that embedding cards in a different batch moves no vector beyond the tolerance, runs the card-representation
scenarios, and builds neighbour lists for the chosen cards and for the most-played new cards (among older cards only). It also finds the played cards
whose neighbour lists differ most between encoders. Embeddings go to archetype_classifier/embeddings/ (gitignored); results to docs/experiments/.

    uv run --group archetypes python -m archetype_classifier.experiments.card_encoders --stage 1 --date 20261005
    uv run --group archetypes python -m archetype_classifier.experiments.card_encoders --stage 1 --date 20261005 --encoders gte-modernbert

With --encoders, only those encoders are run; the others keep their results from the existing results file and their saved embeddings.

Stage 2 embeds the whole pool once per text format (--recipes) with each of --encoders (potion by default). For each format it runs the scenarios,
builds neighbour lists for the chosen cards and for cards whose lists stage 1 showed being pulled by names, measures how much of each card's top 10 it
shares with the base format, and lists the played cards whose neighbours each format changes most.

    uv run --group archetypes python -m archetype_classifier.experiments.card_encoders --stage 2 --date 20261005

Stage 2b combines potion's base-format text embedding with a standardised structured vector, at alpha = 0, 0.2, ... 1 (alpha weighs the text), for
each structured scheme (current, log, numbers). It runs the scenarios and the user's checks on every combination, lists the three focus cards in every
combination and the other chosen cards for the log scheme at a few alphas, with the stats text format alongside for reference.

    uv run --group archetypes python -m archetype_classifier.experiments.card_encoders --stage 2b --date 20261005
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

from archetype_classifier.card_embeddings.combined import build_combined, build_standardisation
from archetype_classifier.card_embeddings.embeddings import EMBEDDINGS_DIR, Embeddings, build_embeddings, embeddings_path, load_embeddings, merge_embeddings, save_embeddings
from archetype_classifier.card_embeddings.encoders import ENCODERS, load_encoder
from archetype_classifier.card_embeddings.neighbours import build_all_neighbours, build_neighbours, build_overlap, build_rank
from archetype_classifier.card_embeddings.pool import Card, load_card_pool
from archetype_classifier.card_embeddings.structured import Scheme, build_structured_vector
from archetype_classifier.card_embeddings.text import BASE, RECIPES, STATS, build_card_text
from decksite.database import db

OUT = Path(__file__).parents[1] / 'docs' / 'experiments'
ORDER = ('potion', 'minilm', 'bge-small', 'bge-base', 'gte-modernbert')  # Fastest first.
NEW_SEASON = 43
LIST_SIZE = 10
REPRINT_GROUPS = [["Ajani's Response", 'Grounded for Life', 'Seized from Slumber', 'Luminous Rebuke'], ['Llanowar Elves', 'Elvish Mystic', 'Fyndhorn Elves']]
VANILLAS = ['Plated Seastrider', 'Kalonian Tusker', "Garruk's Gorehorn", 'Coral Eel', 'Spined Wurm']
LIST_CARDS = [
    # Edge cases from the #7 grilling.
    'Seized from Slumber', 'Swift Response', 'Llanowar Elves', 'Shock', 'Burst Lightning', 'Kalonian Tusker', 'Hagra Mauling',
    # The user's staples.
    'Cancel', 'Distress', "Inventors' Fair", 'Eater of Virtue', 'Kumano Faces Kakkazan', 'Discovery // Dispersal', 'Horned Loch-Whale',
    # The most-played non-land cards in seasons 39-43.
    'Chain Lightning', 'Birds of Paradise', 'Malcolm, Alluring Scoundrel', "Archmage's Charm", 'Mana Leak', 'Luminarch Aspirant',
]
NAME_CARDS = [  # Stage 1 showed names pulling these cards' neighbours: other cards named Malcolm or ...Bolt, other Eldrazi titans, legendaries.
    'Plasma Bolt', 'Kozilek, Butcher of Truth', 'Ilharg, the Raze-Boar', 'Momo, Friendly Flier', 'Progenitus', 'Ertai Resurrected', 'Tersa Lightshatter',
]
NEAR_BURST = ['Shivan Fire', 'Roil Eruption']  # The cards the user judges closest in spirit to Burst Lightning.
STAGE2_RECIPES = ('base', 'json', 'json+masked', 'stats', 'labels')
CHANGED_SHOWN = 6  # Played cards per format whose top 10 it changes most against the base format.
FOCUS_CHECKS = {  # The user's reading of stage 2 (2026-10-05): each focus card, and the cards that should (or shouldn't) be near it.
    'Kalonian Tusker': ['Werewolf Pack Leader', 'Jibbirik Omnivore'],
    'Lightning Strike': ['Explosive Welcome'],  # Should drop: the same text, five more mana.
    'Eater of Virtue': ['Bonesplitter'],
}
ALPHAS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
SCHEMES: tuple[Scheme, ...] = ('current', 'log', 'numbers')
SHOWN_SCHEME, SHOWN_ALPHAS = 'log', (1.0, 0.8, 0.6, 0.4)  # For the chosen cards beyond the focus cards.
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

def build_scenarios(e: Embeddings) -> dict[str, Any]:
    """The card-representation scenarios, plus the user's Burst Lightning neighbours and Leaf Gilder's tie with Llanowar Elves."""
    return {
        'reprints_lowest_similarity': [min(similarity(e, g[0], other) for other in g[1:]) for g in REPRINT_GROUPS],
        'swift_response': {r: [build_rank(e, r, 'Swift Response'), similarity(e, r, 'Swift Response')] for r in REPRINT_GROUPS[0]},
        'shock_burst': [build_rank(e, 'Shock', 'Burst Lightning'), build_rank(e, 'Burst Lightning', 'Shock'), similarity(e, 'Shock', 'Burst Lightning')],
        'near_burst': {n: [build_rank(e, 'Burst Lightning', n), similarity(e, 'Burst Lightning', n)] for n in NEAR_BURST},
        'leaf_gilder': [build_rank(e, 'Llanowar Elves', 'Leaf Gilder'), similarity(e, 'Llanowar Elves', 'Leaf Gilder')],
        'vanillas': {f'{a} / {b}': similarity(e, a, b) for a, b in combinations(VANILLAS, 2)},
    }

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
        'scenarios': build_scenarios(embeddings),
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

def run_stage2(pool: Sequence[Card], encoder_names: Sequence[str], recipe_labels: Sequence[str], played: set[str]) -> dict[str, Any]:
    """Each encoder in each text format: timings, scenarios, lists, and how each format's top 10s differ from the base format's."""
    results: dict[str, Any] = {}
    for name in encoder_names:
        encoder = load_encoder(name)
        formats: dict[str, Any] = {}
        tops = {}
        for label in recipe_labels:
            embeddings, seconds = timed(build_embeddings, pool, RECIPES[label], encoder)
            save_embeddings(embeddings)
            tops[label] = build_all_neighbours(embeddings, LIST_SIZE)
            formats[label] = {'seconds': seconds, 'over_token_limit': embeddings.manifest['over_token_limit'], 'scenarios': build_scenarios(embeddings),
                              'lists': {card: neighbour_list(embeddings, card) for card in [*LIST_CARDS, *NAME_CARDS]}}
            print(f"{name} {label}: {seconds:.1f}s; Shock/Burst #{formats[label]['scenarios']['shock_burst'][0]}/#{formats[label]['scenarios']['shock_burst'][1]}", flush=True)
        names = embeddings.names
        candidates = [i for i, n in enumerate(names) if n in played]
        for label in recipe_labels:
            overlap = build_overlap(tops[label], tops['base'])
            formats[label]['overlap_with_base'] = float(overlap.mean())
            formats[label]['overlap_with_base_played'] = float(overlap[candidates].mean())
            if label != 'base':
                changed = sorted(candidates, key=lambda i: (overlap[i], names[i]))[:CHANGED_SHOWN]
                formats[label]['most_changed'] = [{'card': names[i], 'overlap': float(overlap[i]), 'base': [names[j] for j in tops['base'][i]],
                                                   'format': [names[j] for j in tops[label][i]]} for i in changed]
        results[name] = formats
    return results

def main_stage2b(args: argparse.Namespace, pool: Sequence[Card], recent: dict[str, int]) -> None:
    by_name = {c.name: c for c in pool}
    played = {n for n, decks in recent.items() if decks >= PLAYED}
    encoder = load_encoder('potion')
    text = build_embeddings(pool, BASE, encoder)
    stats_text = build_embeddings(pool, STATS, encoder)
    cards = [by_name[n] for n in text.names]
    candidates = [i for i, n in enumerate(text.names) if n in played]
    base_top = build_all_neighbours(text, LIST_SIZE)
    shown_cards = [c for c in [*LIST_CARDS, *NAME_CARDS] if c not in FOCUS_CHECKS]
    combos: dict[str, Any] = {}
    for scheme in SCHEMES:
        standardised = build_standardisation(np.stack([build_structured_vector(c, scheme) for c in cards]))
        rows = standardised.apply(np.stack([build_structured_vector(c, scheme) for c in cards]))
        for alpha in ALPHAS:
            e = build_combined(text, rows, alpha, scheme)
            top = build_all_neighbours(e, LIST_SIZE)
            overlap = build_overlap(top, base_top)
            combo: dict[str, Any] = {'scheme': scheme, 'alpha': alpha, 'scenarios': build_scenarios(e),
                     'focus': {card: {other: [build_rank(e, card, other), similarity(e, card, other)] for other in others} for card, others in FOCUS_CHECKS.items()},
                     'overlap_with_text_played': float(overlap[candidates].mean()),
                     'lists': {card: neighbour_list(e, card) for card in FOCUS_CHECKS}}
            if scheme == SHOWN_SCHEME and alpha in SHOWN_ALPHAS:
                combo['lists'] |= {card: neighbour_list(e, card) for card in shown_cards}
            combos[f'{scheme}@{alpha}'] = combo
            focus = '; '.join(f'{o} #{r[0]}' for checks in combo['focus'].values() for o, r in checks.items())
            print(f'{scheme} alpha {alpha}: {focus}', flush=True)
    reference: dict[str, Any] = {'scenarios': build_scenarios(stats_text), 'lists': {card: neighbour_list(stats_text, card) for card in [*FOCUS_CHECKS, *shown_cards]},
                 'focus': {card: {o: [build_rank(stats_text, card, o), similarity(stats_text, card, o)] for o in others} for card, others in FOCUS_CHECKS.items()}}
    results = {'stage': '2b', 'pool': len(pool), 'encoder': 'potion', 'text': BASE.label, 'alphas': ALPHAS, 'schemes': SCHEMES, 'focus_checks': FOCUS_CHECKS,
               'shown_scheme': SHOWN_SCHEME, 'shown_alphas': SHOWN_ALPHAS, 'shown_cards': shown_cards, 'played_cards': len(candidates),
               'combos': combos, 'stats_text': reference}
    shown = {*FOCUS_CHECKS, *shown_cards, *(o for others in FOCUS_CHECKS.values() for o in others)}
    for combo in [*combos.values(), reference]:
        shown |= {n for ns in combo['lists'].values() for n, _ in ns}
    results['card_text'] = {n: build_card_text(by_name[n], STATS) for n in sorted(shown)}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{args.date}_card_encoders_stage2b.json'
    path.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f'Wrote {path}')

def main_stage2(args: argparse.Namespace, pool: Sequence[Card], recent: dict[str, int]) -> None:
    by_name = {c.name: c for c in pool}
    encoder_names = args.encoders or ['potion']
    recipe_labels = args.recipes or list(STAGE2_RECIPES)
    if 'base' not in recipe_labels:
        recipe_labels = ['base', *recipe_labels]  # The comparison needs it.
    played = {n for n, decks in recent.items() if decks >= PLAYED}
    results: dict[str, Any] = {'stage': 2, 'pool': len(pool), 'list_cards': LIST_CARDS, 'name_cards': NAME_CARDS, 'near_burst': NEAR_BURST,
                               'played_cards': len(played & set(by_name)), 'encoders': run_stage2(pool, encoder_names, recipe_labels, played)}
    shown = {*LIST_CARDS, *NAME_CARDS, *NEAR_BURST}
    for formats in results['encoders'].values():
        for f in formats.values():
            shown |= {n for ns in f['lists'].values() for n, _ in ns}
            shown |= {n for c in f.get('most_changed', []) for n in [c['card'], *c['base'], *c['format']]}
    results['card_text'] = {label: {n: build_card_text(by_name[n], RECIPES[label]) for n in sorted(shown)} for label in recipe_labels}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{args.date}_card_encoders_stage2.json'
    if path.exists():  # Keep the other encoders' results: each run adds or replaces only its own.
        previous = json.loads(path.read_text())
        results['encoders'] = {**previous['encoders'], **results['encoders']}
        for label, texts in previous['card_text'].items():
            results['card_text'][label] = {**texts, **results['card_text'].get(label, {})}
    path.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f'Wrote {path}')

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--stage', choices=['1', '2', '2b'], required=True)
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the results file name')
    parser.add_argument('--encoders', nargs='+', choices=ORDER, help='stage 1: run only these, the rest come from the existing results file; stage 2: default potion')
    parser.add_argument('--recipes', nargs='+', choices=sorted(RECIPES), help=f'stage 2 only; default {", ".join(STAGE2_RECIPES)}')
    args = parser.parse_args()

    pool = load_card_pool()
    new = [c for c in pool if min(c.seasons) == NEW_SEASON]
    old = [c for c in pool if min(c.seasons) < NEW_SEASON]
    recent, latest = load_play_counts(39, NEW_SEASON), load_play_counts(NEW_SEASON, NEW_SEASON)
    new_shown = sorted((c.name for c in new if latest.get(c.name)), key=lambda n: (-latest[n], n))[:NEW_CARDS_SHOWN]
    print(f'{len(pool)} cards: {len(old)} before season {NEW_SEASON}, {len(new)} new in it', flush=True)
    names = {c.name for c in pool}
    focus = [n for card, others in FOCUS_CHECKS.items() for n in (card, *others)]
    if missing := [n for n in [*LIST_CARDS, *NAME_CARDS, *NEAR_BURST, 'Leaf Gilder', *focus, *VANILLAS, *(n for g in REPRINT_GROUPS for n in g)] if n not in names]:
        raise SystemExit(f'Not in the card pool: {", ".join(missing)}')
    if args.stage == '2':
        main_stage2(args, pool, recent)
        return
    if args.stage == '2b':
        main_stage2b(args, pool, recent)
        return

    path = OUT / f'{args.date}_card_encoders_stage{args.stage}.json'
    previous = json.loads(path.read_text())['encoders'] if args.encoders else {}
    results: dict[str, Any] = {'stage': 1, 'recipe': BASE.label, 'pool': len(pool), 'list_cards': LIST_CARDS,
                               'new_cards_shown': {n: latest[n] for n in new_shown}, 'card_text': {}, 'encoders': {}}
    by_name = {c.name: c for c in pool}
    all_embeddings = {}
    for name in ORDER:
        if args.encoders and name not in args.encoders:
            if name in previous:
                results['encoders'][name], all_embeddings[name] = previous[name], load_embeddings(embeddings_path(EMBEDDINGS_DIR, name, BASE))
        else:
            results['encoders'][name], all_embeddings[name] = run_encoder(name, old, new, new_shown)
    shown = set(LIST_CARDS) | set(new_shown) | {n for r in results['encoders'].values() for lists in (r['lists'], r['new_card_lists']) for ns in lists.values() for n, _ in ns}
    results['disagreement'] = build_disagreement(all_embeddings, {n for n, decks in recent.items() if decks >= PLAYED})
    shown |= {n for d in results['disagreement']['least_agreed'] for ns in [[d['card']], *d['lists'].values()] for n in ns}
    results['card_text'] = {n: build_card_text(by_name[n], BASE) for n in sorted(shown)}

    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f'Wrote {path}')

if __name__ == '__main__':
    main()
