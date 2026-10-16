"""Run 17's space on real data (#64). Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 3 in the experiments database, run 17, the real
site and cards databases and the saved embedding in embeddings/. It refits run 17's model, which takes a few minutes.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/geometry/space_local_test.py
"""
import math
import os
from typing import cast

import numpy as np
import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.evaluation.model import JSON
from archetype_classifier.evaluation.store import load_model_record, load_run
from archetype_classifier.geometry.space import load_space

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
RUN = 17


def test_run_17s_space_has_the_rows_its_model_recorded() -> None:
    edb = loader.experiments_db()
    _, state = load_model_record(edb, load_run(edb, RUN).model_id)
    space = load_space(edb, RUN)
    assert len(space.rows.labels) == state['training_rows'] == 84_085
    assert int(space.rows.deck_counts.sum()) == state['training_decks'] == 162_869
    assert space.embedding is not None
    assert np.allclose(space.vectors.lines @ space.embedding, space.vectors.matrix)
    assert np.allclose(np.linalg.norm(space.vectors.matrix, axis=1), 1)


def test_run_17s_lines_carry_its_card_weights_and_square_root_copies() -> None:
    """Runs 14, 16 and 17 have the same rows, so the counts alone can't tell their spaces apart. With card weights and √copies, two basic lands in one
    list stand in the ratio √n1 w1 : √n2 w2, using the basic lands' weights the model recorded; run 14 would give n1 : n2."""
    edb = loader.experiments_db()
    _, state = load_model_record(edb, load_run(edb, RUN).model_id)
    weights = cast(dict[str, float], cast(dict[str, JSON], state['card_weights'])['basic_lands'])
    space = load_space(edb, RUN)
    column = {card: i for i, card in enumerate(space.cards)}
    checked = 0
    for row, maindeck in enumerate(space.rows.maindecks):
        basics = [line for line in maindeck if line.card in weights]
        if len(basics) < 2 or basics[0].n == basics[1].n:
            continue
        first, second = basics[:2]
        lines = space.vectors.lines.getrow(row).toarray()[0]
        expected = (math.sqrt(first.n) * weights[first.card]) / (math.sqrt(second.n) * weights[second.card])
        assert math.isclose(lines[column[first.card]] / lines[column[second.card]], expected, rel_tol=1e-3), (row, first, second)
        checked += 1
        if checked == 100:
            break
    assert checked == 100
