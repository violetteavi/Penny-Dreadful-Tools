# Archetype Classifier

Exploratory work on automatically classifying Penny Dreadful decks into archetypes.

Status: **exploration**. Nothing here is used by the site yet.

See [CONTEXT.md](CONTEXT.md) for the vocabulary (deck, archetype tree, parent fallback, unseen card, …).

## Goal

Given a deck, predict its archetype. When the classifier is unsure between specific archetypes, it should fall back to their parent archetype. The less sure it is, the higher up the archetype tree its answer should go.

Today decks are labelled by a guess (hand-written rules, or the archetype of the most similar reviewed deck, see `maintenance/guess_league_archetypes.py`) which a person then reviews. A better classifier would mean better guesses and less reviewing.

## What makes it hard

- **Unseen cards.** A new set arrives about every two months, and each rotation brings cards that appear in no earlier deck. The classifier must cope with decks built partly from cards it has never seen.
- **Labels at every depth.** Over a third of decks are labelled with a parent archetype (for example Red Deck Wins rather than one of its children), because they have no clear home further down the tree.
- **Label quality.** Nearly every deck is flagged as reviewed, so the flag says little. The label history (who assigned each label, and whether it was a person or an automatic guess) is the better evidence.
- **Imbalance.** A handful of archetypes cover most decks; many have only a few dozen.

## Evaluation

- **Seasons:** train on seasons 1–38, validate and tune on season 39, and test on seasons 40–42. The test seasons are the main test of unseen cards, and are looked at rarely.
- **Season 43 is reserved** for a later final check. It is the current season, so its decks and labels are still changing; past seasons barely change.
- Also hold out 10% of decklists within the training seasons, keeping identical maindecks together.
- Splits are recorded as named schemes, so experiments can be re-run exactly and different splits compared.
- Score predictions against the archetype tree, not by exact match: see [ADR 0001](docs/adr/0001-score-guesses-with-hierarchical-f.md).

## Ground rules

- This package imports from the rest of the repo (`decksite.data`, `magic`); nothing else imports it. Merging it cannot change the site's behaviour.
- Code follows the repo's standards: typed, and passing `dev.py lint` and `dev.py types`.
- Machine-learning libraries go in an optional `archetypes` dependency group in `pyproject.toml`, installed with `uv sync --group archetypes`. Tests that need them use `pytest.importorskip`, and tests that need the database use the `functional` marker.
- Exported data and trained models are not committed.

## Running

Needs a local decksite database and cards database; see the setup instructions in the repository's top-level [README](../README.md).
