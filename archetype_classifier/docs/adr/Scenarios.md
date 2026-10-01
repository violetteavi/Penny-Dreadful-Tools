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
- **Confirmed 2026-09-30.**

### Depth difference says whether a guess leans up or down the tree

Depth difference is the guess's depth minus the label's depth. Top-level archetypes have depth 0 and the root has depth −1. A guess is **on-path** when it is the label, one of its ancestors (including the root) or one of its descendants, and **off-path** otherwise.

- **Expect:** each pair in the table below gives the depth difference and path shown. For example, Red Deck Wins guessed for a Prisoner deck is −1 on-path (a parent fallback), Prisoner guessed for a Red Deck Wins deck is +1 on-path (too specific), and Mono Red Devotion guessed for a Prisoner deck is 0 off-path (a sibling).
- **Why it matters:** negative on-path differences are parent fallbacks and positive ones are too-specific guesses. This is the report the Tentative too-specific scenario says to watch. It is a diagnostic, not something to optimise.
- **Check:** score each pair.
- **Confirmed 2026-09-30.**

## Summarising a set of guesses

These scenarios score a whole set of decks. Unless a scenario says otherwise, they use the set below: every (label, guess) pair among five labels (Aggro, Red Deck Wins, Prisoner, Mono Red Devotion and Azorius Control) and six guesses (those five, or no guess), 30 pairs and 4,350 decks in all, each with its own maindeck. The deck counts are invented but plausible for a decent guesser: exact guesses are the most common, then nearby archetypes on the same branch, then no guess, with guesses on the wrong branch rarest.

In each row, ∩, Guessed and Label count archetypes after expanding the guess and the label with their ancestors (not the root). hP, hR, hF, depth difference and path are the scores of one deck in that row; — marks an undefined value.

| Label | Guess | Decks | ∩ | Guessed | Label | hP | hR | hF | Depth diff | Path |
|---|---|---|---|---|---|---|---|---|---|---|
| Prisoner | Prisoner | 1000 | 3 | 3 | 3 | 1.000 | 1.000 | 1.000 | 0 | on |
| Prisoner | Mono Red Devotion | 120 | 2 | 3 | 3 | 0.667 | 0.667 | 0.667 | 0 | off |
| Prisoner | Red Deck Wins | 150 | 2 | 2 | 3 | 1.000 | 0.667 | 0.800 | −1 | on |
| Prisoner | Aggro | 40 | 1 | 1 | 3 | 1.000 | 0.333 | 0.500 | −2 | on |
| Prisoner | Azorius Control | 10 | 0 | 2 | 3 | 0.000 | 0.000 | 0.000 | −1 | off |
| Prisoner | *root* | 60 | 0 | 0 | 3 | — | 0.000 | 0.000 | −3 | on |
| Mono Red Devotion | Prisoner | 100 | 2 | 3 | 3 | 0.667 | 0.667 | 0.667 | 0 | off |
| Mono Red Devotion | Mono Red Devotion | 600 | 3 | 3 | 3 | 1.000 | 1.000 | 1.000 | 0 | on |
| Mono Red Devotion | Red Deck Wins | 120 | 2 | 2 | 3 | 1.000 | 0.667 | 0.800 | −1 | on |
| Mono Red Devotion | Aggro | 30 | 1 | 1 | 3 | 1.000 | 0.333 | 0.500 | −2 | on |
| Mono Red Devotion | Azorius Control | 20 | 0 | 2 | 3 | 0.000 | 0.000 | 0.000 | −1 | off |
| Mono Red Devotion | *root* | 40 | 0 | 0 | 3 | — | 0.000 | 0.000 | −3 | on |
| Red Deck Wins | Prisoner | 180 | 2 | 3 | 2 | 0.667 | 1.000 | 0.800 | +1 | on |
| Red Deck Wins | Mono Red Devotion | 90 | 2 | 3 | 2 | 0.667 | 1.000 | 0.800 | +1 | on |
| Red Deck Wins | Red Deck Wins | 400 | 2 | 2 | 2 | 1.000 | 1.000 | 1.000 | 0 | on |
| Red Deck Wins | Aggro | 50 | 1 | 1 | 2 | 1.000 | 0.500 | 0.667 | −1 | on |
| Red Deck Wins | Azorius Control | 10 | 0 | 2 | 2 | 0.000 | 0.000 | 0.000 | 0 | off |
| Red Deck Wins | *root* | 30 | 0 | 0 | 2 | — | 0.000 | 0.000 | −2 | on |
| Aggro | Prisoner | 40 | 1 | 3 | 1 | 0.333 | 1.000 | 0.500 | +2 | on |
| Aggro | Mono Red Devotion | 30 | 1 | 3 | 1 | 0.333 | 1.000 | 0.500 | +2 | on |
| Aggro | Red Deck Wins | 60 | 1 | 2 | 1 | 0.500 | 1.000 | 0.667 | +1 | on |
| Aggro | Aggro | 200 | 1 | 1 | 1 | 1.000 | 1.000 | 1.000 | 0 | on |
| Aggro | Azorius Control | 20 | 0 | 2 | 1 | 0.000 | 0.000 | 0.000 | +1 | off |
| Aggro | *root* | 40 | 0 | 0 | 1 | — | 0.000 | 0.000 | −1 | on |
| Azorius Control | Prisoner | 10 | 0 | 3 | 2 | 0.000 | 0.000 | 0.000 | +1 | off |
| Azorius Control | Mono Red Devotion | 10 | 0 | 3 | 2 | 0.000 | 0.000 | 0.000 | +1 | off |
| Azorius Control | Red Deck Wins | 10 | 0 | 2 | 2 | 0.000 | 0.000 | 0.000 | 0 | off |
| Azorius Control | Aggro | 10 | 0 | 1 | 2 | 0.000 | 0.000 | 0.000 | −1 | off |
| Azorius Control | Azorius Control | 800 | 2 | 2 | 2 | 1.000 | 1.000 | 1.000 | 0 | on |
| Azorius Control | *root* | 70 | 0 | 0 | 2 | — | 0.000 | 0.000 | −2 | on |

### Micro averaging sums over decks

Summed over all 4,350 decks, weighting each row by its deck count: ∩ = 9,170, Guessed = 10,070, Label = 10,600.

- **Expect:** micro hP = 9,170 / 10,070 = **0.911**; micro hR = 9,170 / 10,600 = **0.865**; micro hF = **0.887**.
- **Why it matters:** this is the headline number (ADR 0001). The 240 decks with no guess add nothing to hP and lower hR.
- **Check:** score the set.
- **Confirmed 2026-09-30.**

### Macro averaging weighs every labelled archetype equally

Group the decks by label, compute micro hP, hR and hF within each group, then take the plain mean over the groups where each value is defined.

| Label | Decks | hP | hR | hF |
|---|---|---|---|---|
| Prisoner | 1,380 | 0.962 | 0.865 | 0.911 |
| Mono Red Devotion | 910 | 0.942 | 0.832 | 0.883 |
| Red Deck Wins | 760 | 0.827 | 0.914 | 0.869 |
| Aggro | 390 | 0.579 | 0.846 | 0.688 |
| Azorius Control | 910 | 0.947 | 0.879 | 0.912 |

- **Expect:**

  | Minimum decks | Archetypes that qualify | Macro hP | Macro hR | Macro hF |
  |---|---|---|---|---|
  | 1 | 5 of 5 | 0.851 | 0.867 | 0.852 |
  | 500 | 4 of 5 (Aggro left out) | 0.920 | 0.872 | 0.894 |
  | 800 | 3 of 5 (Aggro and Red Deck Wins left out) | 0.950 | 0.858 | 0.902 |

- **Also:** an archetype whose decks all got no guess has undefined hP. It is left out of macro hP but counts in macro hR and hF (both 0).
- **Why it matters:** micro averaging is dominated by the most common archetypes. Macro shows whether rarer ones, like Aggro here, are handled too. The minimum is required on every call and echoed in the result, with the count of archetypes that qualified, so two reports can't quietly differ.
- **Check:** score the set with minimums of 1, 500 and 800.
- **Confirmed 2026-09-30.**

### No archetype meets the macro minimum

Score the set with a minimum of 2,000 decks per archetype. The most common label, Prisoner, has 1,380.

- **Expect:** 0 of 5 archetypes qualify, macro hP, hR and hF are all undefined, and the scorer logs a warning saying that no archetype has 2,000 decks. Every other metric equals the result at any other minimum.
- **Why it matters:** a minimum set for the full test seasons can be too high for a small row, such as decks with 13 or more unseen cards. That row's macro averages have nothing to average, but its other metrics are still worth reading, so the run carries on.
- **Check:** score the set with a minimum of 2,000.
- **Proposed 2026-09-30, for review.**

### Coverage and exact-match rate

- **Expect:** coverage (the share of decks with a guess) is 4,110 / 4,350 = **0.945**. Exact-match rate is 3,000 / 4,350 = **0.690**; the 240 decks with no guess count as not matching.
- **Why it matters:** one minus the exact-match rate is the share of guesses a reviewer would change, comparable with the historical correction rate.
- **Check:** score the set.
- **Confirmed 2026-09-30.**

### Depth differences are counted separately on and off the path

- **Expect:**

  | Path | −3 | −2 | −1 | 0 | +1 | +2 | +3 | Decks | Mean |
  |---|---|---|---|---|---|---|---|---|---|
  | On | 100 | 170 | 360 | 3,000 | 330 | 70 | | 4,030 | −0.132 |
  | Off | | | 40 | 240 | 40 | | | 320 | 0.000 |

- **Why it matters:** here parent fallbacks (630 decks below 0 on-path) and too-specific guesses (400 above 0) largely cancel, so the mean alone hides both. The counts show them.
- **Check:** score the set.
- **Confirmed 2026-09-30.**

### Confusions are counted by label and guess

- **Expect:** every non-exact (label, guess) pair is counted, 1,350 decks over 25 pairs, each with its path. The six most common are:

  | Label | Guess | Decks | Path |
  |---|---|---|---|
  | Red Deck Wins | Prisoner | 180 | on |
  | Prisoner | Red Deck Wins | 150 | on |
  | Prisoner | Mono Red Devotion | 120 | off |
  | Mono Red Devotion | Red Deck Wins | 120 | on |
  | Mono Red Devotion | Prisoner | 100 | off |
  | Red Deck Wins | Mono Red Devotion | 90 | on |

  Exact matches count toward exact matches, not confusions.
- **Why it matters:** the most common confusions, shown by name, are the quickest way to see what a model gets wrong. Here the red archetypes blur into each other.
- **Check:** score the set.
- **Confirmed 2026-09-30.**

### A deck outside the tree is skipped with a warning

Add one more deck, labelled Prisoner and guessed as an archetype id that isn't in the tree the scorer was given (for example, one created after the snapshot).

- **Expect:** the scorer logs a warning naming the missing archetype id, skips the deck and carries on. Every metric equals the 4,350-deck result; the result reports **1** skipped deck and the missing id. The same happens when the label, rather than the guess, is missing from the tree.
- **Why it matters:** a missing archetype means the experiment is wired wrongly (for example, a perturbed tree without a mapping). Stopping the run would waste it; scoring the deck anyway would give numbers that are hard to interpret.
- **Check:** score the set plus the extra deck.
- **Confirmed 2026-09-30.**

## How much a number could move

Intervals come from a bootstrap: draw maindeck groups at random with replacement until there are as many as in the original, re-score, and repeat 1,000 times. A maindeck group is every deck with the same maindeck (same cards in the same quantities, whatever the sideboard, card order or player). The 95% interval is the middle 95% of the re-scored values. Intervals vary slightly with the seed, so the figures below are approximate; the checks compare intervals rather than match them exactly.

### Identical maindecks don't narrow the interval

Take the set, then add a twin of every deck: the same maindeck, label and guess.

- **Expect:** every point estimate and, with the same seed, every interval is unchanged. Micro hF stays 0.887, with an interval of about [0.881, 0.893].
- **Why it matters:** ten copies of one list are one piece of evidence about the classifier, not ten. Resampling single decks would make the intervals falsely narrow.
- **Check:** score both sets with the same seed.
- **Confirmed 2026-09-30.**

### Intervals are repeatable and recorded

- **Expect:** the same decks and the same seed give the same intervals. The result records the seed and the number of resamples. When every deck is an exact match, hF is 1.00 with interval [1.00, 1.00].
- **Why it matters:** anyone re-scoring stored guesses gets the same table.
- **Check:** score the set twice with one seed.
- **Confirmed 2026-09-30.**

### Fewer maindecks give a wider interval

Take the set again, but make every ten decks in a row share one maindeck, giving 435 maindeck groups instead of 4,350. Each row's count is a multiple of ten, so a group never mixes rows.

- **Expect:** the point estimates are unchanged, but the micro hF interval widens from about [0.881, 0.893] to about [0.867, 0.906].
- **Why it matters:** small rows of the results table, such as decks with 13 or more unseen cards, and rows full of copied decks, should look uncertain.
- **Check:** score both versions with one seed and compare interval widths.
- **Confirmed 2026-09-30.**

## Comparing two models

A comparison scores two models' guesses on the same decks. Each bootstrap draw scores both models on the same drawn decks and records the difference (B − A), so difficulty they share cancels out.

### A model compared with itself differs by nothing

- **Expect:** the difference in micro hF, hP, hR and exact-match rate is 0.00 with interval [0.00, 0.00].
- **Check:** compare the set's guesses with themselves.
- **Confirmed 2026-09-30.**

### A consistent small improvement is detected

Model A's guesses are the set's. Model B's are the same, except that 60 of the 120 Prisoner decks A guessed as Mono Red Devotion are guessed as Prisoner.

- **Expect:** micro hF rises from 0.887 to 0.893, and exact-match rate from 0.690 to 0.703. A's and B's separate hF intervals overlap (about [0.881, 0.893] and [0.887, 0.899]), but the paired difference's interval, about [+0.004, +0.007], lies entirely above 0.
- **Why it matters:** this is how we decide whether a model beats today's guesser. Setting two separate intervals side by side would miss a real improvement.
- **Check:** score A and B separately, then compare them, with one seed.
- **Confirmed 2026-09-30.**

### Decks only one model scored are left out of the comparison

Model A's guesses cover all 4,350 decks. Model B's cover 4,349, because one deck was skipped (its guess isn't in the tree).

- **Expect:** the comparison uses the 4,349 decks both models scored, logs a warning, and reports **1** deck left out.
- **Why it matters:** as with skipped decks, the run should carry on, and the difference should only ever be measured on decks both models were scored on.
- **Check:** compare the two sets.
- **Confirmed 2026-09-30.**

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

## Splitting decks

These scenarios belong to data loading (#19). A split scheme puts every deck in exactly one split: TRAIN, HELD_OUT, VALIDATION, TEST or EXCLUDED. It works in two steps, each using only the deck's own facts:

1. **Label status:** whether the deck's label can be trusted.
2. **Role, then split:** the role comes from the deck's season and held-out group, and the status decides between that role's split and EXCLUDED.

Each scenario states its scheme in full:
- **Season rule:** which seasons are training, validation and test, and what share of training-season maindecks is held out.
- **Status rule:** which statuses may be trained on (`train_statuses`) and which may be scored (`eval_statuses`).
- **Twins:** whether `allow_held_out_twins` is on.

Most scenarios use the **typical scheme**:
- **Season rule:** training seasons 1–38, validation season 39, test seasons 40–42, 10% of training-season maindecks held out.
- **Status rule:** `train_statuses` = {VERIFIED}, `eval_statuses` = {VERIFIED}.
- **Twins:** `allow_held_out_twins` off.

All scenarios here were proposed 2026-10-01.

### Label status depends on the history, the site label and the label rule

No split is involved. Scope rule: League and Gatherling decks, not labelled Unclassified or Commander. Each row is one deck from League unless it says otherwise. "Person" and "automatic" are entries in its label history, oldest first.

| Deck | Label history | Site label | Status under `LATEST_ENTRY_IS_HUMAN` | Status under `SITE_LABEL_IF_EVER_HUMAN` | Scored against |
|---|---|---|---|---|---|
| 1 | person: Prisoner | Prisoner | VERIFIED | VERIFIED | Prisoner |
| 2 | person: Prisoner, then automatic: Red Deck Wins, which the site refused to apply | Prisoner | UNVERIFIED | VERIFIED | Prisoner |
| 3 | person: Wildfire; a curator later moved the deck to Thryx-Wildfire without history | Thryx-Wildfire | UNVERIFIED | VERIFIED | Thryx-Wildfire |
| 4 | automatic: Red Deck Wins | Red Deck Wins | UNVERIFIED | UNVERIFIED | Red Deck Wins |
| 5 | none (the deck predates the label history) | Azorius Control | UNVERIFIED | UNVERIFIED | Azorius Control |
| 6 | none | none | UNLABELLED | UNLABELLED | nothing |
| 7 | person: Commander | Commander | OUT_OF_SCOPE | OUT_OF_SCOPE | nothing |
| 8 | person: Unclassified | Unclassified | OUT_OF_SCOPE | OUT_OF_SCOPE | nothing |
| 9 | person: Red Deck Wins, on a deck from an external deck site | Red Deck Wins | OUT_OF_SCOPE | OUT_OF_SCOPE | nothing |

- **Expect:** each deck gets the status and label in its row, under each rule.
- **Why it matters:**
  - Deck 2 is the 1,844 decks the old rule misclassified. A person's label stands on the site, but a later automatic guess that the site refused to apply made it look automatic.
  - Deck 3 is one of the 204 decks curators moved without history. The current label is the more recent human judgement.
- **Check:** compute the label facts from each history, then the status under each rule.

### A person's label and an automatic guess at the same moment

No split is involved. A deck's history has a person's label (Prisoner) and an automatic guess (Red Deck Wins) with the same timestamp, and the site label is Prisoner.

- **Expect:** under `LATEST_ENTRY_IS_HUMAN`, the person's label counts as the latest, so the deck is VERIFIED.
- **Why it matters:** the snapshot stores each label's time, not the order of the history entries, so a tie needs a rule.
- **Tentative:** revisit if ties turn out to be common in the real history.
- **Check:** compute the status from the two facts with equal times.

### A deck's split follows its role and its status

**Scheme:** the typical scheme (season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED}; twins off).

Each row is one deck. "Held out" means its maindeck falls in the held-out 10%.

| Deck | Season | Held out | Status | Split | Exclusion reason |
|---|---|---|---|---|---|
| A | 30 | no | VERIFIED | TRAIN | |
| B | 30 | no | UNVERIFIED | EXCLUDED | status not used for training |
| C | 30 | no | UNLABELLED | EXCLUDED | status not used for training |
| D | 30 | yes | VERIFIED | HELD_OUT | |
| E | 30 | yes | UNVERIFIED | EXCLUDED | status not used for evaluation |
| F | 39 | — | VERIFIED | VALIDATION | |
| G | 41 | — | VERIFIED | TEST | |
| H | 41 | — | UNLABELLED | EXCLUDED | status not used for evaluation |
| I | 43 | — | VERIFIED | EXCLUDED | reserved season |
| J | 30 | no | VERIFIED, but no maindeck cards | EXCLUDED | no maindeck cards |

- **Expect:** each deck gets the split and reason in its row.
- **Why it matters:** deck H is an unlabelled deck from a test season. It can only become TEST or EXCLUDED, never TRAIN, so no model can learn the test seasons' new cards from it.
- **Check:** assign each deck under the scheme.

### Widening the status rule changes only the decks with that status

**Scheme:** season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED, UNVERIFIED}, eval {VERIFIED}; twins off. The #6 baseline uses this rule, because the site's guesser matches against every reviewed, labelled deck.

- **Expect:** with the same decks as the previous scenario, deck B becomes TRAIN. Every other deck keeps its split and reason: C, which is UNLABELLED, is still EXCLUDED, and E, which is held out, is still EXCLUDED because the eval statuses are unchanged.
- **Check:** assign the same decks under both schemes and compare.

### A deck the snapshot doesn't contain is excluded

**Scheme:** the typical scheme. The deck was played after the snapshot was taken, so it has no row in the snapshot.

- **Expect:** asking for its split gives EXCLUDED, with reason "not in snapshot", whatever the scheme.
- **Check:** look up a deck id that isn't in the snapshot.

### Identical maindecks share a role by default

Decks A (season 30, VERIFIED) and B (season 31, VERIFIED) have the same maindeck.

- **Scheme, twins off:** the typical scheme.
- **Expect:**
  - if their maindeck is held out, both are HELD_OUT
  - if it isn't, both are TRAIN
  - A is never TRAIN while B is HELD_OUT, or the other way round
- **Scheme, twins on:** season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED}; `allow_held_out_twins` on.
- **Expect:** A and B are each held out according to their own deck id, so A can be TRAIN while B is HELD_OUT. About half of real held-out decks will then repeat a TRAIN maindeck, as in real use, where 48% of decks within a season repeat an earlier maindeck.
- **Scheme, different salt:** the typical scheme with a different salt.
- **Expect:** a different set of maindecks is held out.
- **Check:** assign both decks under each scheme.

### An excluded deck changes nothing else

**Scheme:** the typical scheme. There are three decks:
- **A:** season 30, not held out, VERIFIED, maindeck 4 Lightning Bolt and 20 Mountain. It becomes TRAIN.
- **B:** season 30, not held out, UNLABELLED, maindeck 4 Fireblast and 20 Mountain. It becomes EXCLUDED (status not used for training).
- **C:** season 41, VERIFIED, maindeck 4 Lightning Bolt, 4 Fireblast and 16 Mountain. It becomes TEST.

- **Expect:**
  - C has **4** unseen maindeck copies (the four Fireblast). B contains Fireblast but isn't a training deck, so it doesn't make Fireblast seen.
  - Removing B from the snapshot leaves A's and C's splits, statuses, labels and unseen counts exactly as they were. The only change in the report is one fewer deck excluded for "status not used for training".
- **Also, with twins on** (season rule as typical; status rule train {VERIFIED}, eval {VERIFIED}; `allow_held_out_twins` on): A is TRAIN, and its UNLABELLED twin's deck id falls in the held-out group, so the twin is EXCLUDED (status not used for evaluation). A is used exactly as if the twin didn't exist.
- **Why it matters:** an experiment should be the same whether or not data it doesn't use exists. That holds only if every count that looks at other decks counts included ones.
- **Check:** split the snapshot with and without the excluded deck, and compare every other deck.

### A card is unseen unless a training maindeck has it

**Scheme:** the typical scheme.

- **Expect:** a card that appears only in a TRAIN deck's sideboard, or only in HELD_OUT, VALIDATION, TEST or EXCLUDED decks, is unseen. A card that left the legal pool and returned is seen if any TRAIN maindeck has it.
- **Check:** count unseen copies for decks built around such cards.

### A maindeck in both TRAIN and HELD_OUT is reported, not fatal

**Scheme:** the typical scheme, which can't produce this case, so the splits are built by hand: a TRAIN deck and a HELD_OUT deck with the same maindeck.

- **Expect:** the split report lists the maindeck hash and both deck ids, logs a warning, and the split carries on.
- **Scheme, twins on:** season rule as typical; status rule train {VERIFIED}, eval {VERIFIED}; `allow_held_out_twins` on.
- **Expect:** the same overlap is expected and isn't reported.
- **Check:** run the overlap check on the hand-built splits under each scheme.

### A deck set holds exactly the decks in its splits

No scheme is involved: the splits are given. A snapshot has three TRAIN, two HELD_OUT, one VALIDATION, one TEST and two EXCLUDED decks.

- **Expect:**
  - a deck set of TRAIN has the three TRAIN decks
  - a deck set of HELD_OUT and VALIDATION has those three decks
  - asking for EXCLUDED raises an error
  - asking for TEST raises an error unless `include_test` is set, and then returns the one TEST deck
  - two deck sets with the same decks have the same fingerprint, in whatever order the decks were added; adding a deck changes it
- **Check:** build each deck set and compare.

### Older schemes load with today's defaults

Scheme 1 was stored before the status rule and twins flag existed. Its stored season rule is training seasons 1–38, validation season 39, test seasons 40–42, with 10% held out.

- **Expect:** it loads with the typical scheme's status rule and twins setting:
  - scope rule League and Gatherling
  - label rule `LATEST_ENTRY_IS_HUMAN`
  - `train_statuses` {VERIFIED}, `eval_statuses` {VERIFIED}
  - `allow_held_out_twins` off

  Its HELD_OUT, VALIDATION and TEST decks are then exactly its old ground-truth decks in those splits.
- **Check:**
  - load scheme 1's stored parameters
  - once, after the rebuild, compare against the backup database `archetype_experiments_v0`
