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
- **How it's measured:** through hierarchical precision, reported beside the headline hierarchical F (β = 1). See [ADR 0001](0001-score-guesses-with-hierarchical-f.md), which records β = 0.8 as the alternative if this scenario becomes firm.
- **Revisit if:** the penalty pushes models to guess only top-level archetypes such as Aggro, Midrange or Combo. The depth-difference report shows whether guesses lean up or down the tree.

### A wrong child on the right branch beats a top-level fallback

A deck is labelled **Prisoner**.

- **Expect:** guessing **Mono Red Devotion** (a wrong child of Red Deck Wins, on the right branch) scores higher than guessing **Aggro** (the correct top-level archetype). Plain hierarchical F gives 0.67 against 0.50.
- **Why it matters:** retreating to a top-level archetype tells a reviewer very little. The metric should not reward a model for playing safe that way.
- **Confirmed 2026-09-28.**

### No guess scores as a guess of the root

A deck is labelled **Prisoner**, and the model gives no guess, because it isn't confident even in a top-level archetype.

- **Expect:** no guess is scored as a guess of the root. It expands to the empty set, so the deck's hP is undefined (it has no guessed archetypes to be right or wrong about), hR is 0.00, hF is 0.00, and it is not an exact match.
- **Why it matters:** no answer isn't a wrong answer, but it isn't help to a reviewer either. It costs recall and leaves precision alone, so a model can't look better by declining to answer; coverage (below) shows how often it does.
- **Check:** score no guess against the Prisoner label.
- **Proposed 2026-09-30, for review.**

### Depth difference says whether a guess leans up or down the tree

Depth difference is the guess's depth minus the label's depth. Top-level archetypes have depth 0 and the root (no guess) has depth −1. A guess is **on-path** when it is the label, one of its ancestors (including the root) or one of its descendants, and **off-path** otherwise.

| Label | Guess | Depth difference | Path |
|---|---|---|---|
| Prisoner | Prisoner | 0 | on |
| Prisoner | Red Deck Wins | −1 | on |
| Prisoner | no guess | −3 | on |
| Red Deck Wins | Prisoner | +1 | on |
| Azorius Control | Mono Red Devotion | +1 | off |

- **Expect:** each pair gives the depth difference and path shown.
- **Why it matters:** negative on-path differences are parent fallbacks, positive ones are too-specific guesses. This is the report the Tentative too-specific scenario says to watch. It is a diagnostic, not something to optimise.
- **Check:** score each pair.
- **Proposed 2026-09-30, for review.**

## Summarising a set of guesses

These scenarios score a whole set of decks. Unless a scenario says otherwise, they use these four decks, one maindeck each:

| Deck | Label | Guess | Guessed ∩ label | Guessed | Label |
|---|---|---|---|---|---|
| 1 | Prisoner | Prisoner | 3 | 3 | 3 |
| 2 | Prisoner | Red Deck Wins | 2 | 2 | 3 |
| 3 | Azorius Control | Mono Red Devotion | 0 | 3 | 2 |
| 4 | Prisoner | no guess | 0 | 0 | 3 |

The last three columns count archetypes after expanding each side with its ancestors (not the root).

### Micro averaging sums over decks

- **Expect:** micro hP = (3 + 2 + 0 + 0) / (3 + 2 + 3 + 0) = 5/8 = **0.625**; micro hR = 5 / (3 + 3 + 2 + 3) = 5/11 = **0.455**; micro hF = **0.526**.
- **Why it matters:** this is the headline number (ADR 0001). Deck 4's missing guess leaves hP unchanged and lowers hR.
- **Check:** score the four decks.
- **Proposed 2026-09-30, for review.**

### Macro averaging weighs every labelled archetype equally

Group the decks by label, compute micro hP, hR and hF within each group, then take the plain mean over groups.

| Label | Decks | hP | hR | hF |
|---|---|---|---|---|
| Prisoner | 1, 2, 4 | 1.00 | 0.556 | 0.714 |
| Azorius Control | 3 | 0.00 | 0.00 | 0.00 |

- **Expect:** with a minimum of 1 deck per archetype, macro hP = **0.50**, macro hR = **0.278**, macro hF = **0.357**, over 2 of 2 archetypes. With a minimum of 2 decks, Azorius Control is left out: macro hP = **1.00**, hR = **0.556**, hF = **0.714**, over 1 of 2 archetypes.
- **Also:** an archetype whose decks all got no guess has undefined hP. It is left out of macro hP but counts in macro hR and hF (both 0).
- **Why it matters:** micro averaging is dominated by the most common archetypes. Macro shows whether rarer archetypes are handled too. The minimum is required on every call and echoed in the result, with the count of archetypes that qualified, so two reports can't quietly differ.
- **Check:** score the four decks with minimums of 1 and 2.
- **Proposed 2026-09-30, for review.**

### Coverage and exact-match rate

- **Expect:** coverage (the share of decks with a guess) is 3/4 = **0.75**. Exact-match rate is 1/4 = **0.25**; deck 4's missing guess counts as not matching.
- **Why it matters:** one minus the exact-match rate is the share of guesses a reviewer would change, comparable with the historical correction rate.
- **Check:** score the four decks.
- **Proposed 2026-09-30, for review.**

### Depth differences are counted separately on and off the path

- **Expect:** on-path depth differences are {−3: 1, −1: 1, 0: 1} (mean −1.33); off-path are {+1: 1} (mean +1.00).
- **Check:** score the four decks.
- **Proposed 2026-09-30, for review.**

### Confusions are counted by label and guess

- **Expect:** the non-exact (label → guess) pairs are counted: Prisoner → Red Deck Wins 1 (on-path), Azorius Control → Mono Red Devotion 1 (off-path), Prisoner → no guess 1. The exact match (deck 1) counts toward exact matches, not confusions.
- **Why it matters:** the most common confusions, shown by name, are the quickest way to see what a model gets wrong.
- **Check:** score the four decks.
- **Proposed 2026-09-30, for review.**

### A deck outside the tree is skipped with a warning

Add a fifth deck, labelled Prisoner and guessed as an archetype id that isn't in the tree the scorer was given (for example, one created after the snapshot).

- **Expect:** the scorer logs a warning naming the missing archetype id, skips the deck and carries on. Every metric equals the four-deck result; the result reports **1** skipped deck and the missing id. The same happens when the label, rather than the guess, is missing from the tree.
- **Why it matters:** a missing archetype means the experiment is wired wrongly (for example, a perturbed tree without a mapping). Stopping the run would waste it; scoring the deck anyway would give numbers that are hard to interpret.
- **Check:** score the five decks.
- **Proposed 2026-09-30, for review.**

## How much a number could move

Intervals come from a bootstrap: draw maindeck groups at random with replacement until there are as many as in the original, re-score, and repeat 1,000 times. A maindeck group is every deck with the same maindeck (same cards in the same quantities, whatever the sideboard, card order or player). The 95% interval is the middle 95% of the re-scored values.

### Identical maindecks don't narrow the interval

Take a set of decks, then add a twin of every deck: the same maindeck, label and guess.

- **Expect:** every point estimate and, with the same seed, every interval is unchanged.
- **Why it matters:** ten copies of one list are one piece of evidence about the classifier, not ten. Resampling single decks would make the intervals falsely narrow.
- **Check:** score both sets with the same seed.
- **Proposed 2026-09-30, for review.**

### Intervals are repeatable and recorded

- **Expect:** the same decks and the same seed give the same intervals. The result records the seed and the number of resamples. When every deck is an exact match, hF is 1.00 with interval [1.00, 1.00].
- **Why it matters:** anyone re-scoring stored guesses gets the same table.
- **Check:** score the same decks twice with one seed.
- **Proposed 2026-09-30, for review.**

### Fewer maindecks give a wider interval

- **Expect:** 20 maindeck groups, 12 of them exact matches and 8 wrong-branch guesses, give a wider hF interval than 2,000 groups in the same proportions. The point estimates are equal.
- **Why it matters:** small rows of the results table, such as decks with 13 or more unseen cards, should look uncertain.
- **Check:** score both sets with one seed and compare interval widths.
- **Proposed 2026-09-30, for review.**

## Comparing two models

A comparison scores two models' guesses on the same decks. Each bootstrap draw scores both models on the same drawn decks and records the difference (B − A), so difficulty they share cancels out.

### A model compared with itself differs by nothing

- **Expect:** the difference in micro hF, hP, hR and exact-match rate is 0.00 with interval [0.00, 0.00].
- **Check:** compare a set of guesses with itself.
- **Proposed 2026-09-30, for review.**

### A consistent small improvement is detected

100 decks labelled Prisoner, one maindeck each. Model A guesses Prisoner for 60 and Azorius Control for 40. Model B guesses the same, except it gets 10 of A's wrong decks right: 70 exact matches.

- **Expect:** A's and B's separate hF intervals overlap, but the paired difference's interval lies entirely above 0.
- **Why it matters:** this is how we decide whether a model beats today's guesser. Setting two separate intervals side by side would miss a real improvement.
- **Check:** score A and B separately, then compare them, with one seed.
- **Proposed 2026-09-30, for review.**

### Decks only one model scored are left out of the comparison

Model A's guesses cover decks 1–100. Model B's cover decks 1–99, because deck 100 was skipped (its guess isn't in the tree).

- **Expect:** the comparison uses decks 1–99, logs a warning, and reports **1** deck left out.
- **Why it matters:** as with skipped decks, the run should carry on, and the difference should only ever be measured on decks both models were scored on.
- **Check:** compare the two sets.
- **Proposed 2026-09-30, for review.**

## Parent fallback

These scenarios belong to the model, which turns its confidence into a single guess. The scorer only ever sees that guess.

### Unsure between children, sure of the parent

A deck is clearly Red Deck Wins, but the classifier splits its confidence among the children. For example (invented probabilities): Prisoner 0.38, Proliferate Red 0.21, Mono Red Devotion 0.12, Red Deck Wins with no child 0.17, giving 0.88 for the Red Deck Wins subtree.

- **Expect:** the guess is **Red Deck Wins**, not Prisoner, even though Prisoner is the most likely single archetype.
- **Check:** apply the fallback rule to a deck with this confidence profile.

### Less sure, higher up

The same deck, but the classifier is also unsure whether it is Red Deck Wins or another Aggro archetype. The Red Deck Wins subtree falls below the threshold, while Aggro as a whole stays above it.

- **Expect:** the guess climbs to **Aggro**. It never jumps to another branch, such as Azorius Control, whose subtree is unlikely.
- **Check:** as above, with lower confidence in the Red Deck Wins subtree.
