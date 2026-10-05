from pathlib import Path

import numpy as np
import pytest

from archetype_classifier.card_embeddings.embeddings import Embeddings, save_embeddings
from archetype_classifier.card_embeddings.neighbours import Neighbour, build_neighbours, main
from archetype_classifier.data_loading import loader


def unit(*rows: list[float]) -> np.ndarray:
    matrix = np.array(rows, dtype=np.float32)
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

# Shock and Burst Lightning point the same way; Lightning Strike is close; Cancel and Counterspell are elsewhere, at the same angle from Shock.
EMBEDDINGS = Embeddings(('Burst Lightning', 'Cancel', 'Counterspell', 'Lightning Strike', 'Shock'),
                        unit([1, 0, 0], [0, 1, 0], [0, 0, 1], [3, 1, 0], [1, 0, 0]), {})


def test_the_nearest_cards_come_first_with_their_cosine_similarity_and_the_card_itself_left_out() -> None:
    neighbours = build_neighbours(EMBEDDINGS, 'Shock', 2)
    assert [n.name for n in neighbours] == ['Burst Lightning', 'Lightning Strike']
    assert [n.similarity for n in neighbours] == pytest.approx([1.0, 3 / np.sqrt(10)])
    assert all(isinstance(n, Neighbour) for n in neighbours)

def test_ties_are_broken_by_name() -> None:
    assert [n.name for n in build_neighbours(EMBEDDINGS, 'Shock', 4)][2:] == ['Cancel', 'Counterspell']

def test_among_limits_the_cards_searched() -> None:
    assert [n.name for n in build_neighbours(EMBEDDINGS, 'Shock', 5, among={'Cancel', 'Lightning Strike', 'Shock'})] == ['Lightning Strike', 'Cancel']

def test_an_unknown_card_is_named_in_the_error() -> None:
    with pytest.raises(ValueError, match='Lightning Bolt is not in these embeddings'):
        build_neighbours(EMBEDDINGS, 'Lightning Bolt', 3)


# The command-line tool.

@pytest.fixture
def saved(tmp_path: Path) -> Path:
    save_embeddings(Embeddings(EMBEDDINGS.names, EMBEDDINGS.matrix, {'encoder': 'fake', 'recipe': {'stats': False, 'mask': False}}), tmp_path)
    return tmp_path

def test_the_tool_prints_a_cards_neighbours_from_saved_embeddings(saved: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(['Shock', '--encoder', 'fake', '-n', '2', '--dir', str(saved)])
    assert capsys.readouterr().out == ('Shock: fake, base, 5 cards\n'
                                       '  1  1.000  Burst Lightning\n'
                                       '  2  0.949  Lightning Strike\n')

def test_season_limits_the_tool_to_cards_legal_that_season(saved: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loader, 'load_legal_cards', lambda seasons: {43: frozenset({'Shock', 'Cancel', 'Counterspell'})})
    main(['Shock', '--encoder', 'fake', '-n', '5', '--season', '43', '--dir', str(saved)])
    assert capsys.readouterr().out == ('Shock: fake, base, 5 cards, among the 3 legal in season 43\n'
                                       '  1  0.000  Cancel\n'
                                       '  2  0.000  Counterspell\n')

def test_the_tool_says_how_to_build_missing_embeddings(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match='No embeddings at .*bge-small__stats.npy: build them with python -m archetype_classifier.experiments.card_encoders'):
        main(['Shock', '--recipe', 'stats', '--dir', str(tmp_path)])
