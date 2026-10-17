"""Run 17's space on real data (#64), built as the experiment builds it: store.load_model refits the stored model, then build_model_space reads
its space off it. Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 3 in the experiments database, run 17, the real
site and cards databases and the saved embedding in embeddings/. It refits run 17's model, which takes about a minute.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/geometry/space_local_test.py
"""
import logging
import os

import numpy as np
import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.evaluation.store import identity_hash, load_model, load_model_record, load_run
from archetype_classifier.geometry.space import build_model_space

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
RUN = 17
RUN_17_PARAMS = {'embedding': 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39', 'weights': 'idf', 'copies': 'sqrt'}


def test_run_17s_space_is_its_stored_model_refitted_reproducibly(caplog: pytest.LogCaptureFixture) -> None:
    """The stored fingerprints say which space this is. load_model refuses a changed embedding or changed card weights, and warns when the training
    decks no longer rebuild to the stored fingerprint; here that warning would mean the space isn't run 17's, so it must not appear."""
    edb = loader.experiments_db()
    model_id = load_run(edb, RUN).model_id
    stored, state = load_model_record(edb, model_id)
    with caplog.at_level(logging.WARNING):
        record, model = load_model(edb, model_id)
    space = build_model_space(model)
    assert not [r for r in caplog.records if 'not reproducible' in r.getMessage()]
    assert record == stored
    assert identity_hash(record) == edb.value('SELECT identity_hash FROM model WHERE id = %s', [model_id])
    assert (record.name, record.params, record.scheme_id) == ('embedding nearest deck', RUN_17_PARAMS, 3)
    assert len(space.rows.labels) == state['training_rows'] == 84_085
    assert int(space.rows.deck_counts.sum()) == state['training_decks'] == record.training_count == 162_869
    assert space.embedding is not None
    assert np.allclose(space.vectors.lines @ space.embedding, space.vectors.matrix)
    assert np.allclose(np.linalg.norm(space.vectors.matrix, axis=1), 1)
