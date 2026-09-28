# Scenarios

Concrete cases the parts of the archetype classifier must get right. Each one names real cards, decks or archetypes, says what should happen, and says how to check it, so it can become a test or an evaluation check.

Terms follow [CONTEXT.md](../../CONTEXT.md). Scenarios marked **Tentative** are agreed for now but may change; each says what would make us revisit it.

## Card representation

### Functional reprints get the same representation

Ajani's Response, Grounded for Life, Seized from Slumber and Luminous Rebuke are the same card under four names. All four are {4}{W} instants reading "This spell costs {3} less to cast if it targets a tapped creature. Destroy target creature."

- **Expect:** the card representation treats them as one card. Their vectors are identical or nearly so, and each is closer to the other three than to any card with different rules text.
- **Why it matters:** new sets often reprint an effect under a new name. Here, Ajani's Response and Grounded for Life first appear in season 42, so they are unseen cards in the test split, while Seized from Slumber (from season 35) and Luminous Rebuke (from season 36) are in the training data. A classifier can only use the new names if the representation maps them onto the old ones.
- **Check:** pairwise similarity among the four, and each card's nearest neighbours in the whole card pool.

### Near-equivalent cards are close

Swift Response ({1}{W} instant, "Destroy target tapped creature.") does the same job as the four cards above: against a tapped creature, all five cost two mana and destroy it.

- **Expect:** Swift Response is very close to the four reprints, among their nearest neighbours in the card pool, though not identical to them.
- **Check:** Swift Response's rank and similarity in each reprint's nearest-neighbour list. The exact rank or similarity cut-off is to be set once card embeddings are measured.

## Scoring against the archetype tree

Examples use this part of the tree:

- Aggro › Red Deck Wins › Prisoner, Proliferate Red, Mono Red Devotion
- Control › Azorius Control

### A correct parent fallback beats a wrong branch

A deck is labelled **Prisoner**. Guesses, from best to worst:

| Guess | Kind of answer | hP | hR | Tree distance |
|---|---|---|---|---|
| Prisoner | Exact | 1.00 | 1.00 | 0 |
| Red Deck Wins | Correct parent fallback | 1.00 | 0.67 | 1 |
| Mono Red Devotion | Wrong child, right branch | 0.67 | 0.67 | 2 |
| Azorius Control | Wrong branch | 0.00 | 0.00 | 5 |

hP and hR are hierarchical precision and recall: each archetype is extended with its ancestors (not counting the root), and the two sets are compared. Tree distance counts edges between guess and label, passing through the root.

- **Expect:** the tree-aware metric ranks the four guesses in this order.
- **Check:** score each guess against the Prisoner label.
- **Confirmed 2026-09-28:** a correct parent fallback (Red Deck Wins) scores better than a wrong child on the right branch (Mono Red Devotion). Both hierarchical F and tree distance rank them this way.

### A too-specific guess on a parent label is penalised

A deck is labelled **Red Deck Wins**, a parent archetype, because it has no clear home in any child.

- **Expect:** the guess Prisoner scores below the exact guess Red Deck Wins (hP 0.67, hR 1.00, tree distance 1), and above Azorius Control.
- **Tentative:** a too-specific guess costs more than a parent fallback that is the same distance off. For example, guessing Prisoner for a Red Deck Wins deck scores below guessing Red Deck Wins for a Prisoner deck. Hierarchical precision separates them (0.67 against 1.00). Plain hierarchical F scores both 0.80 and tree distance scores both 1, so neither produces this ordering on its own.
- **Revisit if:** the penalty pushes models to guess only top-level archetypes such as Aggro, Midrange or Combo. The exact size of the penalty is settled in [How should predictions be scored against the archetype tree?](https://github.com/violetteavi/Penny-Dreadful-Tools/issues/5).

### A wrong child on the right branch beats a top-level fallback

A deck is labelled **Prisoner**.

- **Expect:** guessing **Mono Red Devotion** (a wrong child of Red Deck Wins, on the right branch) scores higher than guessing **Aggro** (the correct top-level archetype). Plain hierarchical F gives 0.67 against 0.50.
- **Why it matters:** retreating to a top-level archetype tells a reviewer very little. The metric should not reward a model for playing safe that way.
- **Confirmed 2026-09-28.**

## Parent fallback

### Unsure between children, sure of the parent

A deck is clearly Red Deck Wins, but the classifier splits its confidence among the children. For example (invented probabilities): Prisoner 0.38, Proliferate Red 0.21, Mono Red Devotion 0.12, Red Deck Wins with no child 0.17, giving 0.88 for the Red Deck Wins subtree.

- **Expect:** the guess is **Red Deck Wins**, not Prisoner, even though Prisoner is the most likely single archetype.
- **Check:** apply the fallback rule to a deck with this confidence profile.

### Less sure, higher up

The same deck, but the classifier is also unsure whether it is Red Deck Wins or another Aggro archetype. The Red Deck Wins subtree falls below the threshold, while Aggro as a whole stays above it.

- **Expect:** the guess climbs to **Aggro**. It never jumps to another branch, such as Azorius Control, whose subtree is unlikely.
- **Check:** as above, with lower confidence in the Red Deck Wins subtree.
