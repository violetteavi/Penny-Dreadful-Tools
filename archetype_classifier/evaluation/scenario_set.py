"""The example tree and deck set from the scoring scenarios in docs/adr/Scenarios.md, for tests."""
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import ArchetypeTree, ScoredDeck

AGGRO, RED_DECK_WINS, PRISONER, PROLIFERATE_RED, MONO_RED_DEVOTION, CONTROL, AZORIUS_CONTROL = range(1, 8)
NO_GUESS = None

TREE = ArchetypeTree({a.id: a for a in [
    ArchetypeSnapshot(AGGRO, 'Aggro', None, 0),
    ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1),
    ArchetypeSnapshot(PRISONER, 'Prisoner', RED_DECK_WINS, 2),
    ArchetypeSnapshot(PROLIFERATE_RED, 'Proliferate Red', RED_DECK_WINS, 2),
    ArchetypeSnapshot(MONO_RED_DEVOTION, 'Mono Red Devotion', RED_DECK_WINS, 2),
    ArchetypeSnapshot(CONTROL, 'Control', None, 0),
    ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1),
]})

# Decks per (label, guess), as in the table under "Summarising a set of guesses".
COUNTS: dict[tuple[int, int | None], int] = {
    (PRISONER, PRISONER): 1000, (PRISONER, MONO_RED_DEVOTION): 120, (PRISONER, RED_DECK_WINS): 150,
    (PRISONER, AGGRO): 40, (PRISONER, AZORIUS_CONTROL): 10, (PRISONER, NO_GUESS): 60,
    (MONO_RED_DEVOTION, PRISONER): 100, (MONO_RED_DEVOTION, MONO_RED_DEVOTION): 600, (MONO_RED_DEVOTION, RED_DECK_WINS): 120,
    (MONO_RED_DEVOTION, AGGRO): 30, (MONO_RED_DEVOTION, AZORIUS_CONTROL): 20, (MONO_RED_DEVOTION, NO_GUESS): 40,
    (RED_DECK_WINS, PRISONER): 180, (RED_DECK_WINS, MONO_RED_DEVOTION): 90, (RED_DECK_WINS, RED_DECK_WINS): 400,
    (RED_DECK_WINS, AGGRO): 50, (RED_DECK_WINS, AZORIUS_CONTROL): 10, (RED_DECK_WINS, NO_GUESS): 30,
    (AGGRO, PRISONER): 40, (AGGRO, MONO_RED_DEVOTION): 30, (AGGRO, RED_DECK_WINS): 60,
    (AGGRO, AGGRO): 200, (AGGRO, AZORIUS_CONTROL): 20, (AGGRO, NO_GUESS): 40,
    (AZORIUS_CONTROL, PRISONER): 10, (AZORIUS_CONTROL, MONO_RED_DEVOTION): 10, (AZORIUS_CONTROL, RED_DECK_WINS): 10,
    (AZORIUS_CONTROL, AGGRO): 10, (AZORIUS_CONTROL, AZORIUS_CONTROL): 800, (AZORIUS_CONTROL, NO_GUESS): 70,
}

def scenario_decks(decks_per_maindeck: int = 1) -> list[ScoredDeck]:
    """The 4,350 decks of the scenario set, numbered from 1 in the order of COUNTS.

    Each run of `decks_per_maindeck` consecutive decks shares a maindeck. Every count is a multiple of ten, so with up to ten decks per maindeck a maindeck never spans two (label, guess) pairs.
    """
    assert all(n % decks_per_maindeck == 0 for n in COUNTS.values())
    pairs = [pair for pair, n in COUNTS.items() for _ in range(n)]
    return [ScoredDeck(i + 1, label, guess, f'maindeck-{i // decks_per_maindeck}') for i, (label, guess) in enumerate(pairs)]
