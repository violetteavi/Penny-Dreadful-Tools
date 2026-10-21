"""Spread, span neighbours and contrasts on run 17's space (#62): the numbers the #62 decisions were based on, from the exploration in
20261020_Spread_Neighbours_Either_Span.pdf and 20261020_Blended_Pushes.pdf. Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 3 in the
experiments database, run 17, the real site and cards databases and the saved embedding in embeddings/. It refits run 17's model, which takes about a
minute.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/geometry/contrasts_local_test.py
"""
import os
from dataclasses import dataclass

import numpy as np
import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.evaluation.store import load_model, load_run
from archetype_classifier.geometry.centroids import Centroids, build_centroids, build_shares, build_spread
from archetype_classifier.geometry.contrasts import (
    Neighbour,
    NeighbourContrast,
    build_blended_contrast,
    build_global_contrast,
    build_neighbour_contrasts,
    build_span_neighbours,
)
from archetype_classifier.geometry.signatures import build_push
from archetype_classifier.geometry.space import DeckSpace, build_model_space

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
RUN = 17


@dataclass(frozen=True)
class Run17:
    space: DeckSpace
    centroids: Centroids
    ids: dict[str, int]
    spread: np.ndarray
    shares: np.ndarray
    neighbours: dict[int, list[Neighbour]]
    contrasts: dict[int, NeighbourContrast]

@pytest.fixture(scope='module')
def run_17() -> Run17:
    edb = loader.experiments_db()
    record, model = load_model(edb, load_run(edb, RUN).model_id)
    space = build_model_space(model)
    snapshot = loader.load_snapshot(edb, record.snapshot_id, record.scheme_id)
    centroids = build_centroids(space)
    spread, shares = build_spread(space, centroids), build_shares(space, centroids)
    neighbours = build_span_neighbours(centroids, spread)
    return Run17(space, centroids, {a.name: a.id for a in snapshot.archetypes.values()}, spread, shares, neighbours,
                 build_neighbour_contrasts(centroids, shares, neighbours))


def test_izzet_twin_is_tight_and_sits_inside_nine_generic_archetypes_spans(run_17: Run17) -> None:
    twin = run_17.ids['Izzet Twin']
    assert np.isclose(run_17.spread[run_17.centroids.index()[twin]], 0.021826071402092806)
    names = {i: name for name, i in run_17.ids.items()}
    assert [(names[n.label_id], n.inside_mine, n.inside_theirs) for n in run_17.neighbours[twin]] == [
        (name, False, True) for name in ('Izzet Control', 'Curious Niv-Mizzet', 'Izzet Cloudpost Control', 'Jeskai Midrange', 'Combo', 'Combo-Control',
                                         'Control', 'Storm', 'Midrange')]

def test_slivers_has_no_neighbours(run_17: Run17) -> None:
    assert run_17.neighbours[run_17.ids['Slivers']] == []

def test_goblins_local_global_and_blended_pushes(run_17: Run17) -> None:
    goblins = run_17.ids['Goblins']
    own, global_contrast = run_17.shares[run_17.centroids.index()[goblins]], build_global_contrast(run_17.shares)
    contrast = run_17.contrasts[goblins]
    assert contrast.local_contrast is not None and contrast.neighbour_count == 1  # Goblin Persist.
    def top_10(contrast_shares: np.ndarray) -> list[str]:
        return [c.card for c in build_push(run_17.space, own, contrast_shares).cards[:10]]
    assert top_10(build_blended_contrast(contrast, global_contrast)) == [
        'Goblin Chieftain', 'Goblin Warchief', 'Foundry Street Denizen', 'Mogg War Marshal', 'Goblin King', 'Mogg Fanatic', 'Goblin Instigator',
        'Pashalik Mons', 'Moria Marauder', 'Goblin Piledriver']
    assert top_10(contrast.local_contrast) == [
        'Dragonskull Summit', 'Rootbound Crag', 'Murderous Redcap', 'Canyon Slough', 'Snow-Covered Mountain', 'Woodland Chasm', 'Graven Cairns',
        'Putrid Goblin', 'Earwig Squad', 'Foundry Street Denizen']
    assert top_10(global_contrast) == [
        'Goblin Warchief', 'Goblin Chieftain', 'Mogg War Marshal', 'Skirk Prospector', 'Goblin Ringleader', 'Goblin Matron', 'Pashalik Mons',
        'Goblin Piledriver', 'Foundry Street Denizen', 'Goblin King']
