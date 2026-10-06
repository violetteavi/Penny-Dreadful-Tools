import math

import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined import GroupedSimilarity, Standardisation, build_centring, build_combined, build_group_shares, build_standardisation
from archetype_classifier.card_embeddings.embeddings import Embeddings
from archetype_classifier.card_embeddings.neighbours import build_neighbours
from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.structured import build_front_numbers


def unit(*rows: list[float]) -> np.ndarray:
    matrix = np.array(rows, dtype=np.float32)
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

NAMES = ('Burst Lightning', 'Explosive Welcome', 'Lightning Strike', 'Shock')
TEXT = Embeddings(NAMES, unit([1, 0.1], [1, 0.3], [1, 0.2], [1, 0]), {'encoder': 'fake'})  # By text, all four are burn.
STRUCTURED = np.array([[1, 0], [8, 0], [2, 0], [1, 1]], dtype=np.float32)  # Mana value, and one more column.


# Standardising: each column to mean 0 and spread 1, with the statistics frozen when fitted.

def test_standardising_gives_each_column_mean_0_and_spread_1() -> None:
    standardised = build_standardisation(STRUCTURED).apply(STRUCTURED)
    assert standardised.mean(axis=0) == pytest.approx([0, 0], abs=1e-6)
    assert standardised.std(axis=0) == pytest.approx([1, 1], abs=1e-6)

def test_a_column_that_never_varies_standardises_to_zero() -> None:
    constant = np.array([[1, 5], [2, 5], [3, 5]], dtype=np.float32)
    assert build_standardisation(constant).apply(constant)[:, 1].tolist() == [0, 0, 0]

def test_new_cards_are_standardised_with_the_fitted_statistics_so_existing_rows_never_move() -> None:
    old, new = STRUCTURED[:3], STRUCTURED[3:]
    standardisation = build_standardisation(old)
    assert np.array_equal(standardisation.apply(np.concatenate([old, new]))[:3], standardisation.apply(old))


# Combining: alpha times the text cosine plus (1 - alpha) times the structured cosine.

def cosine(e: Embeddings, a: str, b: str) -> float:
    return float(e.matrix[e.names.index(a)] @ e.matrix[e.names.index(b)])

def test_alpha_1_is_the_text_embedding_alone() -> None:
    combined = build_combined(TEXT, STRUCTURED, 1.0)
    assert all(build_neighbours(combined, n, 3) == build_neighbours(TEXT, n, 3) for n in NAMES)

def test_alpha_0_is_the_structured_vector_alone() -> None:
    combined = build_combined(TEXT, STRUCTURED, 0.0)
    structured = Embeddings(NAMES, STRUCTURED / np.linalg.norm(STRUCTURED, axis=1, keepdims=True), {})
    assert all([x.name for x in build_neighbours(combined, n, 3)] == [x.name for x in build_neighbours(structured, n, 3)] for n in NAMES)

def test_the_combined_cosine_is_the_weighted_sum_of_the_two_cosines_and_rows_stay_unit_length() -> None:
    combined = build_combined(TEXT, STRUCTURED, 0.6)
    structured = Embeddings(NAMES, STRUCTURED / np.linalg.norm(STRUCTURED, axis=1, keepdims=True), {})
    for a, b in (('Shock', 'Lightning Strike'), ('Shock', 'Explosive Welcome')):
        assert cosine(combined, a, b) == pytest.approx(0.6 * cosine(TEXT, a, b) + 0.4 * cosine(structured, a, b), abs=1e-6)
    assert np.linalg.norm(combined.matrix, axis=1) == pytest.approx(np.ones(4), abs=1e-6)

def test_the_manifest_records_alpha_and_the_structured_scheme() -> None:
    assert build_combined(TEXT, STRUCTURED, 0.4, 'log').manifest == {'encoder': 'fake', 'alpha': 0.4, 'structured': 'log'}

def test_a_card_with_an_all_zero_structured_row_keeps_only_its_text() -> None:
    zeros = np.zeros_like(STRUCTURED)
    assert np.allclose(build_combined(TEXT, zeros, 0.5).matrix[:, :2], np.sqrt(0.5) * TEXT.matrix)

def test_structured_rows_must_match_the_text_rows() -> None:
    with pytest.raises(ValueError, match='4 cards of text but 3 structured rows'):
        build_combined(TEXT, STRUCTURED[:3], 0.5)


# How much of each card's standardised vector each column group takes up, averaged over cards.

def test_group_shares_average_each_groups_share_of_each_rows_squared_length() -> None:
    rows = np.array([[3, 4, 0], [0, 0, 2], [0, 0, 0]], dtype=np.float32)  # Shares: (9/25, 16/25, 0) and (0, 0, 1); an all-zero row is skipped.
    shares = build_group_shares(rows, ('front.mana_value', 'front.colour.R', 'back.mana_value'), lambda c: c.split('.')[1])
    assert shares == pytest.approx({'mana_value': (9 / 25 + 1) / 2, 'colour': (16 / 25) / 2})


# Stage 2d: exact thirds (#7 spec, 2026-10-05). Mana value and stats compare log values when their (present, variable) pairs match and score 0 when not;
# colour is the centred cosine rescaled to 0-1; the three are weighted a third each and mixed with the text cosine by alpha.

def face_card(name: str, mana_cost: str, type_line: str, power: str | None = None, toughness: str | None = None, loyalty: str | None = None) -> Card:
    return Card(name, 'normal', (Face(name, mana_cost, 0, type_line, '', power, toughness, loyalty),))

CARDS = [
    face_card('Adeline, Resplendent Cathar', '{1}{W}{W}', 'Legendary Creature — Human Knight', '*', '4'),
    face_card('Chandra, Pyrogenius', '{4}{R}{R}', 'Legendary Planeswalker — Chandra', loyalty='5'),
    face_card('Chandra, Pyromaster', '{2}{R}{R}', 'Legendary Planeswalker — Chandra', loyalty='4'),
    face_card('Fireball', '{X}{R}', 'Sorcery'),
    face_card('Forest', '', 'Basic Land — Forest'),
    face_card('Island', '', 'Basic Land — Island'),
    face_card('Jace, Wielder of Mysteries', '{1}{U}{U}{U}', 'Legendary Planeswalker — Jace', loyalty='4'),
    face_card('Jibbirik Omnivore', '{1}{G}', 'Creature — Beast', '3', '2'),
    face_card('Kalonian Tusker', '{G}{G}', 'Creature — Beast', '3', '3'),
    face_card('Lhurgoyf', '{2}{G}{G}', 'Creature — Lhurgoyf', '*', '1+*'),
    face_card('Lightning Strike', '{1}{R}', 'Instant'),
    face_card('Ornithopter', '{0}', 'Artifact Creature — Thopter', '0', '2'),
    face_card('Rolling Thunder', '{X}{R}{R}', 'Sorcery'),
    face_card('Searing Spear', '{1}{R}', 'Instant'),
    face_card('Shock', '{R}', 'Instant'),
]
NUMBERS = build_front_numbers(CARDS)
POOL_COLOUR_MEANS = np.array([0.210, 0.204, 0.208, 0.209, 0.205])  # W U B R G across the real pool.
CENTRING = Standardisation(POOL_COLOUR_MEANS, np.ones(5))
CARD_TEXT = Embeddings(NUMBERS.names, unit(*[[1.0, i / 10] for i in range(len(CARDS))]), {})

def groups(a: str, b: str, alpha: float = 0.5) -> dict[str, float]:
    return GroupedSimilarity(CARD_TEXT, NUMBERS, CENTRING, alpha).group_similarities(a, b)

@pytest.mark.parametrize(('a', 'b', 'expected'), [
    ('Lightning Strike', 'Searing Spear', 1.0),
    ('Lightning Strike', 'Jace, Wielder of Mysteries', math.exp(-math.log(5 / 3))),  # 2 against 4: about 0.60.
    ('Fireball', 'Shock', 0.0),  # Variable against fixed.
    ('Fireball', 'Rolling Thunder', math.exp(-math.log(3 / 2))),  # Fixed parts 1 and 2: about 0.67.
    ('Forest', 'Island', 1.0),  # Neither has a mana cost.
    ('Forest', 'Ornithopter', 0.0),  # No cost against {0}.
])
def test_mana_value_similarity(a: str, b: str, expected: float) -> None:
    assert groups(a, b)['mana value'] == pytest.approx(expected)

@pytest.mark.parametrize(('a', 'b', 'expected'), [
    ('Lightning Strike', 'Shock', 1.0),
    ('Ornithopter', 'Lightning Strike', 0.0),
    ('Kalonian Tusker', 'Jibbirik Omnivore', 0.75),  # exp(-|log 4 - log 3|).
    ('Kalonian Tusker', 'Lhurgoyf', 0.0),  # Fixed against variable.
    ('Adeline, Resplendent Cathar', 'Jace, Wielder of Mysteries', 0.0),
    ('Chandra, Pyromaster', 'Jace, Wielder of Mysteries', 1.0),
    ('Chandra, Pyrogenius', 'Jace, Wielder of Mysteries', 5 / 6),  # exp(-|log 6 - log 5|).
])
def test_stats_similarity(a: str, b: str, expected: float) -> None:
    assert groups(a, b)['stats'] == pytest.approx(expected)

def test_colour_similarity_is_the_centred_cosine_rescaled_to_0_1() -> None:
    assert groups('Lightning Strike', 'Shock')['colour'] == pytest.approx(1.0)
    assert groups('Adeline, Resplendent Cathar', 'Jace, Wielder of Mysteries')['colour'] == pytest.approx(0.376, abs=1e-3)  # W against U.

def test_the_structured_similarity_weighs_each_group_a_third_and_alpha_mixes_in_the_text() -> None:
    g = groups('Chandra, Pyrogenius', 'Jace, Wielder of Mysteries', alpha=0.6)
    assert g['structured'] == pytest.approx((g['mana value'] + g['colour'] + g['stats']) / 3)
    assert g['similarity'] == pytest.approx(0.6 * g['text'] + 0.4 * g['structured'])
    assert g['structured'] == pytest.approx((math.exp(-math.log(7 / 5)) + 0.376 + 5 / 6) / 3, abs=1e-3)  # The spec's 0.64.

def test_alpha_1_is_the_text_cosine_and_alpha_0_the_structured_similarity() -> None:
    text_only = GroupedSimilarity(CARD_TEXT, NUMBERS, CENTRING, 1.0)
    assert np.allclose(text_only.similarities(0, len(CARDS)), CARD_TEXT.similarities(0, len(CARDS)))
    numbers_only = GroupedSimilarity(CARD_TEXT, NUMBERS, CENTRING, 0.0)
    i, j = NUMBERS.names.index('Kalonian Tusker'), NUMBERS.names.index('Jibbirik Omnivore')
    assert numbers_only.similarities(i, i + 1)[0, j] == pytest.approx(groups('Kalonian Tusker', 'Jibbirik Omnivore')['structured'])

def test_the_neighbour_functions_work_on_the_grouped_similarity() -> None:
    similarity = GroupedSimilarity(CARD_TEXT, NUMBERS, CENTRING, 0.0)
    assert build_neighbours(similarity, 'Lightning Strike', 1)[0].name == 'Searing Spear'  # Identical numbers; the text is ignored at alpha 0.

def test_colour_centring_is_fitted_once_and_frozen() -> None:
    old, new = NUMBERS.colours[:10], NUMBERS.colours[10:]
    centring = build_centring(old)
    assert np.allclose(centring.mean, old.mean(axis=0)) and np.array_equal(centring.scale, np.ones(5))
    assert np.array_equal(centring.apply(np.concatenate([old, new]))[:10], centring.apply(old))

def test_text_and_numbers_must_be_for_the_same_cards_in_the_same_order() -> None:
    with pytest.raises(ValueError, match='The text and the numbers are for different cards'):
        GroupedSimilarity(Embeddings(tuple(reversed(NUMBERS.names)), CARD_TEXT.matrix, {}), NUMBERS, CENTRING, 0.5)
