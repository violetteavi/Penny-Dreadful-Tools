from collections.abc import Iterator

import pytest

from archetype_classifier.data_loading import loader
from shared.database import Database

EXPERIMENTS_TEST_DB = 'archetype_experiments_test'


@pytest.fixture
def experiments_db() -> Iterator[Database]:
    """A fresh, empty experiments database for one test, dropped afterwards."""
    edb = loader.experiments_db(EXPERIMENTS_TEST_DB)
    edb.execute(f'DROP DATABASE IF EXISTS {EXPERIMENTS_TEST_DB}')
    edb.execute(f'CREATE DATABASE {EXPERIMENTS_TEST_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    edb.execute(f'USE {EXPERIMENTS_TEST_DB}')
    yield edb
    edb.execute(f'DROP DATABASE IF EXISTS {EXPERIMENTS_TEST_DB}')
