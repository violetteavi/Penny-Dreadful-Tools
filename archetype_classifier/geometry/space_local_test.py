"""Run 17's space on real data (#64). Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 3 in the experiments database, run 17, the real
site and cards databases and the saved embedding in embeddings/. It refits run 17's model, which takes a few minutes.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/geometry/space_local_test.py
"""
import os

import numpy as np
import pytest

from archetype_classifier.data_loading import loader
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
