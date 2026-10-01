# Penny Dreadful

Penny Dreadful is a Magic Online format restricted to very cheap cards. This context covers the vocabulary of decks, cards and archetypes, and how decks come to be classified into archetypes.

## Language

### Format and time

**Penny Dreadful**:
A Magic Online format in which only cards costing 0.02 tix or less are legal.
_Avoid_: PD (in prose), penny

**Set**:
A release of new Magic cards, roughly every two months, which triggers a rotation.
_Avoid_: Expansion, edition

**Rotation**:
The recalculation of which cards are legal, based on repeated price checks over a week, when a new set is released.
_Avoid_: Legality update

**Supplemental rotation**:
A smaller mid-season rotation that only adds newly cheap cards from one set to the existing legal card pool.

**Season**:
The period between two rotations, identified by a number and the code of the set that started it.
_Avoid_: Format period

**Legal card pool**:
The set of cards that may be played in a given season; it changes at every rotation.
_Avoid_: Card pool, legal list

### Cards

**Card**:
A distinct Magic card, identified by its canonical name regardless of printing.
_Avoid_: Printing (a printing is one physical/edition version of a card)

**Canonical name**:
The single name a card is known by, merging alternate printings and flavor names.

**Playability**:
The fraction of decks that include a card, counted only in seasons where that card was legal.
_Avoid_: Popularity

**Unseen card**:
A card that appears in a deck but occurs in none of the decks a classifier learned from, typically because it arrived in a new set. A card that left the legal card pool and later returned is not unseen if older decks contain it.
_Avoid_: New card (ambiguous with newly printed)

### Decks and competitions

**Deck**:
One person's submitted list of cards at one point in time, made of a maindeck and a sideboard.
_Avoid_: Decklist (use for the card list itself), build

**Maindeck**:
The cards a deck starts each game with, usually 60.
_Avoid_: Main, mainboard

**Sideboard**:
The additional cards a player may swap into the maindeck between games.

**Deck name**:
The free-text name a player gives their deck; a hint about its archetype but never authoritative.

**Competition**:
An event decks are entered into, either a league or a tournament.
_Avoid_: Event

**League**:
A month-long competition in which players enter a deck and play matches at any time; the source of most decks.

**Tournament**:
A scheduled competition with a fixed start, run through Gatherling, with finishing positions.

**Source**:
Where a deck was obtained from (league, Gatherling, or an external deck site).

### Archetypes and classification

**Archetype**:
A named strategy category a deck belongs to, such as Red Deck Wins or Azorius Control.
_Avoid_: Deck type, category, class

**Archetype tree**:
The hierarchy of archetypes, from broad strategies (Aggro, Control, Combo, Midrange, Ramp and their hybrids such as Aggro-Control) down to specific ones.
_Avoid_: Taxonomy

**Top-level archetype**:
An archetype with no parent in the archetype tree, such as Aggro, Control, Combo, Midrange, Ramp or a hybrid like Aggro-Control.
_Avoid_: Root (the root is the whole tree, above every top-level archetype)

**Leaf archetype**:
An archetype with no children in the archetype tree, describing a specific strategy.

**Parent archetype**:
An archetype with children, at any depth: a broad strategy like Midrange or a specific one like Red Deck Wins (whose children include Prisoner). It is a deck's label when the deck fits it but has no clear home in any of its descendants.
_Avoid_: Generic archetype, catch-all

**Parent fallback**:
Labelling a deck with a parent archetype because no descendant archetype fits it with confidence; the less certain the classification, the higher up the archetype tree the label goes. This is also the right label for a deck playing a strategy that has no archetype yet.

**Unclassified**:
A placeholder meaning nobody has decided the deck's archetype yet; not a label for decks that fit no archetype, which get a parent fallback instead.

**Label**:
The archetype currently assigned to a deck.
_Avoid_: Tag, classification (as a noun for the result)

**Rule**:
A hand-written definition of an archetype as cards a deck must contain (in minimum quantities) and cards it must not contain.

**Similarity**:
A score between 0 and 1 of how alike two maindecks are, weighting shared rarely played cards more heavily.

**Guess**:
A label proposed automatically, by rules or by copying the archetype of the most similar reviewed deck.
_Avoid_: Prediction (reserve for a classifier's output)

**Review**:
A person validating a guess, or changing it to a different archetype.
_Avoid_: Approval, tagging

**Label history**:
The record of every label a deck has had, when it was assigned, and whether a person or an automatic guess assigned it; the best evidence of label quality.

**Mistagged deck**:
A deck whose label disagrees with the archetype its matching rule gives.

**Doubled deck**:
A deck matched by rules for more than one archetype.

**Overlooked deck**:
A deck labelled with an archetype that has rules, none of which match it.

### Evaluation

**Train set**:
Every deck a classifier may learn from: all decks from the training seasons, whatever their source or label, except held-out decks.
_Avoid_: Pool, training pool (a pool is the **Legal card pool**)

**Eval set**:
The decks a classifier's predictions are scored on, each with the label it is scored against, drawn from any combination of training, held-out, validation and test decks.
_Avoid_: Dataset, test set (the test seasons are only one possible part of it)

## Relationships

- A **Set** release triggers a **Rotation**, which starts a new **Season** with a new **Legal card pool**.
- A **Deck** belongs to one **Season** and usually one **Competition**, and has exactly one **Label** (an **Archetype**) at a time.
- An **Archetype** has at most one parent in the **Archetype tree**; a **Deck** may be labelled at any depth.
- A **Guess** becomes a trusted **Label** only through **Review**.
- Each **Rotation** can introduce **Unseen cards** into **Decks** relative to any classifier trained on earlier **Seasons**.
- Held-out, validation and test decks are never in the **Train set**; a deck that repeats a held-out maindeck is held out with it. Training decks may also be in an **Eval set**, where their scores measure fit rather than generalisation.

## Flagged ambiguities

- "Reviewed" in the data is not reliable evidence that a person confirmed a label; use **Label history** instead.
- "New card" can mean newly printed or newly legal; use **Unseen card** when the point is that a classifier hasn't seen it.
- "Test" means only the test seasons, never the whole **Eval set**.
- "Pool" means the **Legal card pool**, never the decks a classifier learns from.
