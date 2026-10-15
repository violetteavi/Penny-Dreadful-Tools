"""Card weights on rule-level decks (Scenarios.md, "Deck representations"). Real weights are checked in representation_local_test.py."""
import hashlib
import logging
import math

import pytest

from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.model import PredictDeck, TrainingDeck
from archetype_classifier.models.card_weights import COPIES, build_card_weights

RED_DECK_WINS, AZORIUS_CONTROL = 16, 49
BOTH = frozenset({'Shock', 'Burst Lightning', 'Mountain', 'Essence Scatter', 'Divination', 'Island'})
LEGAL = {30: BOTH | {'Negate'}, 31: BOTH}  # Real legality: Negate is legal in season 30 but not 31; Smaug's Fury only in season 43.


def lines(counts: dict[str, int]) -> tuple[CardCount, ...]:
    return tuple(sorted((CardCount(c, n) for c, n in counts.items()), key=lambda c: c.card))

def deck(deck_id: int, season_id: int, maindeck: dict[str, int], sideboard: dict[str, int] | None = None) -> TrainingDeck:
    label = AZORIUS_CONTROL if 'Island' in maindeck else RED_DECK_WINS
    return TrainingDeck(PredictDeck(deck_id, 'League', lines(maindeck), lines(sideboard or {})), season_id, label, True, LabelStatus.VERIFIED)

RED = {'Shock': 4, 'Mountain': 56}
TRAINING = [
    deck(1, 30, RED), deck(2, 30, RED, {'Negate': 4}), deck(3, 30, {'Negate': 4, 'Island': 56}), deck(4, 30, {'Essence Scatter': 4, 'Island': 56}),
    deck(5, 31, RED), deck(6, 31, {'Burst Lightning': 4, 'Mountain': 56}), deck(7, 31, {'Essence Scatter': 4, 'Island': 56}), deck(8, 31, {'Essence Scatter': 4, 'Island': 56}),
]


# Scenario: card weights follow the legality-aware IDF.

@pytest.mark.parametrize(('card', 'weight'), [
    ('Mountain', 1.5878), ('Island', 1.5878),  # 4 of 8 decks: the lowest.
    ('Shock', 1.8109), ('Essence Scatter', 1.8109),  # The repeated list counts twice.
    ('Negate', 1.9163),  # Legal in season 30 only (4 decks); its sideboard copies don't count.
    ('Burst Lightning', 2.5041),  # Played as often as Negate, but legal for longer.
    ("Smaug's Fury", 2.6094),  # Never legal: one average season (4 decks), unplayed.
    ('Divination', 3.1972),  # Legal and never played: the highest weight here.
])
def test_card_weights_follow_the_legality_aware_idf(card: str, weight: float) -> None:
    assert round(build_card_weights(TRAINING, LEGAL).weight(card), 4) == weight

def test_the_never_legal_weight_is_an_unplayed_card_from_one_average_season() -> None:
    weights = build_card_weights(TRAINING, LEGAL)
    assert weights.never_legal == math.log(1 + 8 / 2) + 1
    assert weights.weight('A card nobody has heard of') == weights.never_legal

def test_seasons_without_training_decks_count_nothing() -> None:
    weights = build_card_weights(TRAINING, {**LEGAL, 29: frozenset({'Divination'})})
    assert round(weights.weight('Divination'), 4) == 3.1972


# Scenario: a card played outside its legal seasons counts that season, with a warning.

def test_a_card_played_outside_its_legal_seasons_counts_that_season(caplog: pytest.LogCaptureFixture) -> None:
    training = [*TRAINING[:7], deck(8, 31, {'Essence Scatter': 4, 'Negate': 1, 'Island': 55})]
    with caplog.at_level(logging.WARNING):
        weights = build_card_weights(training, LEGAL)
    assert round(weights.weight('Negate'), 4) == 2.0986
    assert weights.outside_legal == ('Negate',)
    assert caplog.text.count('outside') == 1
    assert '1 card played outside its legal seasons, counted as legal there; most played: Negate' in caplog.text

def test_no_warning_when_every_card_was_legal(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        assert build_card_weights(TRAINING, LEGAL).outside_legal == ()
    assert caplog.text == ''

def test_the_warning_names_the_five_most_played_cards(caplog: pytest.LogCaptureFixture) -> None:
    played = {f'Card {k}': 1 for k in range(6)}
    training = [deck(10 + k, 30, {**{c: 1 for c in list(played)[:k + 1]}, 'Mountain': 59 - k}) for k in range(6)]
    with caplog.at_level(logging.WARNING):
        weights = build_card_weights(training, LEGAL)
    assert weights.outside_legal == ('Card 0', 'Card 1', 'Card 2', 'Card 3', 'Card 4', 'Card 5')  # Most played first.
    assert '6 cards played outside their legal seasons, counted as legal there; most played: Card 0, Card 1, Card 2, Card 3, Card 4' in caplog.text


# Scenario: fitted models load back, and refuse changed weights (the hash and summary they store).

def test_the_hash_changes_with_the_weights_but_not_the_order_of_decks() -> None:
    weights = build_card_weights(TRAINING, LEGAL)
    assert build_card_weights(list(reversed(TRAINING)), LEGAL).hash() == weights.hash()
    assert build_card_weights(TRAINING, {30: BOTH | {'Negate'}, 31: BOTH - {'Divination'}}).hash() != weights.hash()  # Divination dropped from season 31.
    assert build_card_weights(TRAINING, {30: BOTH, 31: BOTH}).hash() == weights.hash()  # Negate dropped from season 30 changes nothing: a deck plays it there.

def test_the_summary_names_the_basic_lands_and_never_holds_the_table() -> None:
    summary = build_card_weights(TRAINING, LEGAL).summary()
    assert summary == {'cards': 7, 'never_legal_weight': 2.6094, 'basic_lands': {'Island': 1.5878, 'Mountain': 1.5878}, 'played_outside_legal_seasons': [],
                       'unseen_weight': 'idf', 'typical_weight': 1.6994, 'card_weights_hash': build_card_weights(TRAINING, LEGAL).hash()}


# Copies: each maindeck line counts copies(n) times its weight.

def test_copies_are_linear_or_square_root() -> None:
    assert (COPIES['linear'](4), COPIES['sqrt'](4), COPIES['sqrt'](56)) == (4, 2, math.sqrt(56))


# Scenario: with unseen_weight=typical, an unseen card weighs as a typical card.

def test_the_typical_weight_is_the_median_over_training_maindeck_lines() -> None:
    weights = build_card_weights(TRAINING, LEGAL, unseen='typical')
    assert round(weights.typical, 4) == 1.6994  # 16 lines: the mean of the 8th (1.5878) and 9th (1.8109).
    assert weights.typical == (math.log(9 / 5) + 1 + math.log(9 / 4) + 1) / 2

def test_the_median_of_an_odd_number_of_lines_is_the_middle_one() -> None:
    training = [*TRAINING, deck(9, 31, {'Mountain': 60})]  # 17 lines.
    weights = build_card_weights(training, LEGAL, unseen='typical')
    line_weights = sorted(weights.weight(line.card) for d in training for line in d.deck.maindeck)
    assert len(line_weights) == 17 and weights.typical == line_weights[8]

@pytest.mark.parametrize(('card', 'typical', 'idf'), [
    ('Divination', 1.6994, 3.1972),  # Legal, never played.
    ("Smaug's Fury", 1.6994, 2.6094),  # Never legal.
    ('A card nobody has heard of', 1.6994, 2.6094),
    ('Burst Lightning', 2.5041, 2.5041),  # Played: unchanged.
    ('Mountain', 1.5878, 1.5878),
])
def test_unseen_cards_weigh_as_a_typical_card(card: str, typical: float, idf: float) -> None:
    assert round(build_card_weights(TRAINING, LEGAL, unseen='typical').weight(card), 4) == typical
    assert round(build_card_weights(TRAINING, LEGAL).weight(card), 4) == idf  # The default is today's rule.

def test_an_unknown_unseen_rule_is_refused() -> None:
    with pytest.raises(ValueError, match="unseen must be one of \\('idf', 'typical'\\), not 'median'"):
        build_card_weights(TRAINING, LEGAL, unseen='median')

def test_with_no_training_decks_the_typical_weight_is_one() -> None:
    assert build_card_weights([], LEGAL, unseen='typical').typical == 1.0


# Not a scenario: the default rule keeps today's hash, so stored models (runs 10-12) still load.

def test_the_default_hash_is_unchanged_and_the_typical_rule_changes_it() -> None:
    weights = build_card_weights(TRAINING, LEGAL)
    text = ';'.join(f'{card}:{w:.6f}' for card, w in sorted(weights.idf.items())) + f';never legal:{weights.never_legal:.6f}'
    assert weights.hash() == hashlib.sha1(text.encode()).hexdigest()
    typical = build_card_weights(TRAINING, LEGAL, unseen='typical')
    assert typical.hash() != weights.hash()
    assert typical.hash() == hashlib.sha1(f'{text};unseen typical:{typical.typical:.6f}'.encode()).hexdigest()

def test_the_summary_records_the_unseen_rule_and_typical_weight() -> None:
    summary = build_card_weights(TRAINING, LEGAL, unseen='typical').summary()
    assert (summary['unseen_weight'], summary['typical_weight']) == ('typical', 1.6994)
    assert build_card_weights(TRAINING, LEGAL).summary()['unseen_weight'] == 'idf'
