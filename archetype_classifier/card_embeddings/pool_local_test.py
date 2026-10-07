"""The card pool against the real local databases. Skipped unless PD_LOCAL_DATA=1.

    PD_LOCAL_DATA=1 uv run pytest -s archetype_classifier/card_embeddings/pool_local_test.py
"""
import os

import pytest

from archetype_classifier.card_embeddings.pool import Card, load_card_pool
from magic import layout

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')


@pytest.fixture(scope='module')
def pool() -> dict[str, Card]:
    return {c.name: c for c in load_card_pool()}

def test_the_pool_holds_every_card_ever_legal_in_a_playable_layout(pool: dict[str, Card]) -> None:
    print(f'\n{len(pool)} cards in the pool')
    assert 25_000 < len(pool) < 26_000
    assert all(layout.is_playable_layout(c.layout) for c in pool.values())

def test_cards_are_keyed_by_their_site_names_with_faces_in_order(pool: dict[str, Card]) -> None:
    assert [f.name for f in pool['Discovery // Dispersal'].faces] == ['Discovery', 'Dispersal']
    assert [f.name for f in pool['Kumano Faces Kakkazan'].faces] == ['Kumano Faces Kakkazan', 'Etching of Kumano']
    assert (pool['Kumano Faces Kakkazan'].faces[1].power, pool['Kumano Faces Kakkazan'].faces[1].toughness) == ('2', '2')
    assert 43 in pool['Shock'].seasons and 'Lightning Bolt' not in pool

def test_non_game_cards_are_left_out(pool: dict[str, Card]) -> None:
    assert not any(c.faces[0].type_line.startswith(('Plane ', 'Phenomenon', 'Scheme', 'Vanguard')) for c in pool.values())
