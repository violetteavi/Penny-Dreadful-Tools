"""The card-representation scenarios against the real encoders and the real card pool. Skipped unless PD_LOCAL_DATA=1 and the archetypes
dependency group is installed. Ranks and similarities that don't yet have an agreed cut-off are printed, not asserted (Scenarios.md).

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/card_embeddings/scenarios_local_test.py
"""
import os
import random

import numpy as np
import pytest

from archetype_classifier.card_embeddings.embeddings import TOLERANCE, Embeddings, build_embeddings
from archetype_classifier.card_embeddings.encoders import ENCODERS, Encoder, load_encoder
from archetype_classifier.card_embeddings.neighbours import build_neighbours
from archetype_classifier.card_embeddings.pool import Card, load_card_pool
from archetype_classifier.card_embeddings.text import BASE, MASKED, STATS, TextRecipe

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local setup: set PD_LOCAL_DATA=1')
pytest.importorskip('sentence_transformers')

REPRINT_GROUPS = [["Ajani's Response", 'Grounded for Life', 'Seized from Slumber', 'Luminous Rebuke'], ['Llanowar Elves', 'Elvish Mystic', 'Fyndhorn Elves']]
BEASTS = ['Plated Seastrider', 'Kalonian Tusker', "Garruk's Gorehorn"]
VANILLAS = [*BEASTS, 'Coral Eel', 'Spined Wurm']
SCENARIO_CARDS = [*(n for g in REPRINT_GROUPS for n in g), 'Swift Response', 'Shock', 'Burst Lightning', *VANILLAS]
SAMPLE = 1000  # Cards from season 42 that every embedding is built over, besides the scenario cards.


@pytest.fixture(scope='module')
def pool() -> dict[str, Card]:
    return {c.name: c for c in load_card_pool()}

@pytest.fixture(scope='module')
def sample(pool: dict[str, Card]) -> list[Card]:
    in_42 = sorted(n for n, c in pool.items() if 42 in c.seasons)
    names = set(random.Random(7).sample(in_42, SAMPLE)) | set(SCENARIO_CARDS)
    return [pool[n] for n in sorted(names)]

@pytest.fixture(scope='module', params=sorted(ENCODERS))
def encoder(request: pytest.FixtureRequest) -> Encoder:
    return load_encoder(request.param)

@pytest.fixture(scope='module')
def embedded(encoder: Encoder, sample: list[Card]) -> dict[str, Embeddings]:
    """The sample embedded once per text format for each encoder, shared by every test in the file."""
    return {recipe.label: build_embeddings(sample, recipe, encoder) for recipe in (BASE, STATS, MASKED)}

def similarity(embeddings: Embeddings, a: str, b: str) -> float:
    return float(embeddings.matrix[embeddings.names.index(a)] @ embeddings.matrix[embeddings.names.index(b)])

def rank(embeddings: Embeddings, card: str, other: str) -> int:
    return [n.name for n in build_neighbours(embeddings, card, len(embeddings.names))].index(other) + 1


@pytest.mark.parametrize('recipe', [BASE, STATS, MASKED], ids=lambda r: r.label)
def test_functional_reprints_get_the_same_vector(embedded: dict[str, Embeddings], recipe: TextRecipe) -> None:
    embeddings = embedded[recipe.label]
    for group in REPRINT_GROUPS:
        assert all(similarity(embeddings, group[0], other) == pytest.approx(1, abs=TOLERANCE) for other in group[1:])

def test_near_equivalents_and_names_in_text_are_reported(encoder: Encoder, embedded: dict[str, Embeddings]) -> None:
    for recipe in (BASE, MASKED):
        embeddings = embedded[recipe.label]
        print(f"\n{encoder.name} {recipe.label}: Swift Response is #{rank(embeddings, 'Seized from Slumber', 'Swift Response')} for Seized from Slumber "
              f"({similarity(embeddings, 'Seized from Slumber', 'Swift Response'):.3f}); "
              f"Burst Lightning is #{rank(embeddings, 'Shock', 'Burst Lightning')} for Shock, Shock #{rank(embeddings, 'Burst Lightning', 'Shock')} "
              f"for Burst Lightning ({similarity(embeddings, 'Shock', 'Burst Lightning'):.3f})", end='')

def test_the_vanilla_beasts_are_identical_in_the_base_arm_and_the_stats_arm_is_reported(encoder: Encoder, embedded: dict[str, Embeddings]) -> None:
    base = embedded[BASE.label]
    assert all(similarity(base, BEASTS[0], b) == pytest.approx(1, abs=TOLERANCE) for b in BEASTS[1:])
    stats = embedded[STATS.label]
    pairs = [(a, b) for i, a in enumerate(VANILLAS) for b in VANILLAS[i + 1:]]
    print(f'\n{encoder.name}: ' + '; '.join(f'{a} / {b} base {similarity(base, a, b):.3f} stats {similarity(stats, a, b):.3f}' for a, b in pairs), end='')

def test_adding_the_cards_new_in_season_43_moves_no_other_vector(encoder: Encoder, pool: dict[str, Card], sample: list[Card], embedded: dict[str, Embeddings]) -> None:
    new = [c for c in pool.values() if min(c.seasons) == 43]
    assert len(new) == 461
    before = embedded[BASE.label]
    after = build_embeddings([*sample, *new], BASE, encoder)
    rows = dict(zip(after.names, after.matrix))
    worst = max(float(np.abs(before.matrix[i] - rows[n]).max()) for i, n in enumerate(before.names))
    print(f'\n{encoder.name}: largest change {worst:.2e} over {len(before.names)} cards', end='')
    assert worst <= TOLERANCE
