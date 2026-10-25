"""Deck diffs on run 17's space (#62): the Goblins worked example the 10-21 shift decisions were based on, and a case-study deck's match. Skipped
unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 3 in the experiments database, runs 17 and its guesses, the real site and cards databases and
the saved embedding in embeddings/. It refits run 17's model, which takes about a minute.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/geometry/diffs_local_test.py
"""
import os
from dataclasses import dataclass

import numpy as np
import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.evaluation.model import Model
from archetype_classifier.evaluation.store import load_guesses, load_model, load_run
from archetype_classifier.geometry.centroids import build_centroids, build_shares, build_spread
from archetype_classifier.geometry.contrasts import build_neighbour_contrasts, build_span_neighbours
from archetype_classifier.geometry.diffs import build_axis, build_contributions, build_deck_diff, build_shift
from archetype_classifier.geometry.pairs import build_match_row
from archetype_classifier.geometry.space import DeckSpace, build_model_space, build_placed_decks

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
RUN = 17
GOBLINS_ROW = 45161  # A Goblins training row of 5 decks that plays Murderous Redcap.


@dataclass(frozen=True)
class Run17:
    model: Model
    space: DeckSpace
    ids: dict[str, int]
    names: dict[int, str]

@pytest.fixture(scope='module')
def run_17() -> Run17:
    edb = loader.experiments_db()
    record, model = load_model(edb, load_run(edb, RUN).model_id)
    snapshot = loader.load_snapshot(edb, record.snapshot_id, record.scheme_id)
    return Run17(model, build_model_space(model), {a.name: a.id for a in snapshot.archetypes.values()}, {a.id: a.name for a in snapshot.archetypes.values()})


def test_the_goblins_worked_example(run_17: Run17) -> None:
    space = run_17.space
    goblins = run_17.ids['Goblins']
    assert space.rows.labels[GOBLINS_ROW] == goblins
    centroids = build_centroids(space)
    shares = build_shares(space, centroids)
    neighbours = build_span_neighbours(centroids, build_spread(space, centroids))
    assert [n.label_id for n in neighbours[goblins]] == [run_17.ids['Goblin Persist']]  # So the local contrast is Goblin Persist's shares.
    local = build_neighbour_contrasts(centroids, shares, neighbours)[goblins].local_contrast
    assert local is not None
    axis = build_axis(space, shares[centroids.index()[goblins]], local)
    assert axis is not None and axis.gap == pytest.approx(0.2011, abs=1e-4)

    target = space.rows.maindecks[GOBLINS_ROW]
    counts = {line.card: line.n for line in target}
    counts['Goblin King'] = counts.get('Goblin King', 0) + 1
    counts['Murderous Redcap'] -= 1
    deck = tuple(CardCount(card, n) for card, n in sorted(counts.items()) if n)
    placed = build_placed_decks(run_17.model, [target, deck])
    target_lines, deck_lines = placed.lines.toarray()
    shift = build_shift(axis, deck_lines, target_lines, movement=float(np.linalg.norm(placed.matrix[1] - placed.matrix[0])))
    assert (shift.raw, shift.fraction, shift.on_axis) == (pytest.approx(0.0214, abs=1e-4), pytest.approx(0.106, abs=1e-3), pytest.approx(0.51, abs=0.01))
    contributions = build_contributions(axis, space.cards, deck_lines, target_lines, build_deck_diff(target, deck))
    assert [(c.card, round(c.contribution, 4)) for c in contributions.cards] == [('Goblin King', 0.0071), ('Murderous Redcap', 0.0055)]
    assert contributions.rescaling == pytest.approx(0.0089, abs=1e-4)  # 41% of the shift.


def test_a_case_study_decks_match_is_its_run_17_guess(run_17: Run17) -> None:
    guess = load_guesses(loader.experiments_db(), RUN)[270580]  # The Izzet Twin miss.
    assert guess.guess_id is not None
    row = build_match_row(run_17.space.rows, int(guess.evidence['match_deck_id']), guess.guess_id)  # type: ignore[arg-type]
    assert run_17.names[int(run_17.space.rows.labels[row])] == 'Izzet Control'
