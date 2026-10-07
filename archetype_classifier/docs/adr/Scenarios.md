# Scenarios

Concrete cases the parts of the archetype classifier must get right. Each one names real cards, decks or archetypes, says what should happen, and says how to check it, so it can become a test or an evaluation check.

Terms follow [CONTEXT.md](../../CONTEXT.md). Scenarios marked **Tentative** are agreed for now but may change; each says what would make us revisit it.

## Card representation

A card is represented by its **text** and its **numbers** ([the #7 spec](https://github.com/violetteavi/Penny-Dreadful-Tools/issues/7#issuecomment-6010768554)):
- **Text:** each face's type line and rules text, faces joined, embedded by potion-base-8M. The rules text is Scryfall's oracle text with reminder text kept, in one of two formats: **base** (as it stands) and **masked** (each face's own name written as `~`).
- **Numbers:** the front face's mana value, power, toughness and loyalty, each as (present, variable, fixed), and its colours. A split card sums both halves' mana values and takes both halves' colours. They're compared by **exact thirds** or **average thirds**, so that mana value, colour and stats each count for a third.

Other text formats tried in #7 (cost and stats in the text, inline labels, JSON) are on the tag `card-encoder-exploration`, with the experiments that compared them.

### Functional reprints get the same representation

Two groups of cards are each one card under several names:

- **Removal:** Ajani's Response, Grounded for Life, Seized from Slumber and Luminous Rebuke are all {4}{W} instants reading "This spell costs {3} less to cast if it targets a tapped creature. Destroy target creature."
- **Mana elves:** Llanowar Elves, Elvish Mystic and Fyndhorn Elves are all {G} 1/1 Creature — Elf Druid reading "{T}: Add {G}."

- **Expect:** the card representation treats each group as one card. Their vectors are identical, and each is closer to the rest of its group than to any card with different text.
- **Why it matters:** new sets often reprint an effect under a new name. Here, Ajani's Response and Grounded for Life first appear in season 42, so they are unseen cards in the test split, while Seized from Slumber (from season 35) and Luminous Rebuke (from season 36) are in the training data. A classifier can only use the new names if the representation maps them onto the old ones. The elves show the same thing for a creature, where the stats, cost and type line must match too.
- **Note:** within each group, Scryfall's oracle text, type line, cost and stats are already identical and none of them contains the card's name. So every encoder passes this scenario in both formats. It checks the card-text builder (no name, no printing details leaking in), not the choice of encoder.
- **Check:** pairwise similarity within each group (exactly 1), and each card's nearest neighbours in the whole card pool.

### Near-equivalent cards are close

Swift Response ({1}{W} instant, "Destroy target tapped creature.") does the same job as the four cards above: against a tapped creature, all five cost two mana and destroy it.

- **Expect:** Swift Response is very close to the four reprints, among their nearest neighbours in the card pool, though not identical to them.
- **Check:** Swift Response's rank and similarity in each reprint's nearest-neighbour list. The exact rank or similarity cut-off is to be set once card embeddings are measured.

### A card's name in its own text doesn't push it away from its peers

Shock ({R} instant, "Shock deals 2 damage to any target.") and Burst Lightning ({R} instant, "Kicker {4} (You may pay an additional {4} as you cast this spell.) Burst Lightning deals 2 damage to any target. If this spell was kicked, it deals 4 damage instead.") do the same job for the same cost: two damage to any target for one red mana. Burst Lightning can also be kicked for four damage. Both are legal in seasons 39 and 43.

Scryfall's oracle text still names the card wherever a spell deals damage. Of the 1,603 legal faces whose text names the card, 816 are damage sources like these.

- **Expect:** Burst Lightning is among Shock's nearest neighbours, and Shock among Burst Lightning's, in both formats. They are not identical: the kicker is a real difference. In the masked format, where both names become `~`, they are at least as close as in the base format.
- **Why it matters:** burn spells are the core of Red Deck Wins and its children. If a name in the text pulls apart two cards that do the same thing, an unseen burn spell won't land next to the burn spells a classifier knows.
- **Check:** each card's rank and similarity in the other's nearest-neighbour list, in the base and masked formats. The cut-off is to be set once card embeddings are measured.
- **Measured in #7:** with potion, text alone puts them at #47 / #77 in the base format, but #204 / #159 masked, because the names had been doing some of the work. Adding the numbers brings them back to about #20–50.

### Vanilla creatures differ only in cost, stats and type line

Vanilla creatures have no rules text, so their text is only their type line:

| Card | Cost | Type line | Stats |
|---|---|---|---|
| Plated Seastrider | {U}{U} | Creature — Beast | 1/4 |
| Kalonian Tusker | {G}{G} | Creature — Beast | 3/3 |
| Garruk's Gorehorn | {4}{G} | Creature — Beast | 7/3 |
| Coral Eel | {1}{U} | Creature — Fish | 2/1 |
| Spined Wurm | {4}{G} | Creature — Wurm | 5/4 |

All five are vanilla in the cards database, and all were legal in at least one season. The three Beasts have only the subtype Beast, so nothing but their cost and stats tells them apart. They were legal together in seasons 17–26.

- **Expect:**
  - **Text:** the three Beasts have the same text, `Creature — Beast`, in both formats, so their text vectors are identical (similarity 1). Coral Eel and Spined Wurm differ from them only by subtype.
  - **Numbers:** they tell all five apart, by mana value, colour, power and toughness.
- **Why it matters:** cost and stats decide what a vanilla creature does in a deck, and the text can't tell these cards apart. The numbers have to.
- **Check:** the Beasts' text similarities are 1, and the five cards' front-face numbers all differ.

### Missing stats are absent, not zero

A card's numbers record mana value, power, toughness and loyalty each as three values: **present** (the face prints it; for mana value, the face has a mana cost), **variable** (it holds `*` or `X`) and **fixed** (the number written in it, with `*` and `X` counting 0). The colours are five yes/no values from the mana cost, where a hybrid or Phyrexian symbol counts towards each of its colours.

| Card | Mana value | Power | Toughness | Loyalty | Colours |
|---|---|---|---|---|---|
| Distress ({B}{B} sorcery) | (yes, no, 2) | absent | absent | absent | B |
| Ornithopter ({0} artifact creature, 0/2) | (yes, no, 0) | **(yes, no, 0)** | (yes, no, 2) | absent | none |
| Lhurgoyf ({2}{G}{G} creature, \*/1+\*) | (yes, no, 4) | (yes, **yes**, 0) | (yes, **yes**, 1) | absent | G |
| Jace, Wielder of Mysteries ({1}{U}{U}{U} planeswalker, loyalty 4) | (yes, no, 4) | absent | absent | (yes, no, 4) | U |
| Fireball ({X}{R} sorcery) | (yes, **yes**, 1) | absent | absent | absent | R |
| Forest (land) | **absent** | absent | absent | absent | none |
| Fire // Ice (split, {1}{R} and {1}{U}) | (yes, no, **4**) | absent | absent | absent | R, U |

- **Expect:** each card gets exactly the values in the table. Distress's power reads "absent", and Ornithopter's reads "present, and 0". The two are never equal.
- **Why it matters:** a sorcery has no power. A value of 0 alone would make it look like a 0-power creature, which Ornithopter really is. Likewise, a land has no mana cost, which differs from Ornithopter's real {0}.
- **Check:** build each card's front-face numbers and compare them with the table.
- **Defense is left out for now.** The cards database stores no defense for the 36 legal battles. Scryfall does report it, on the battle face: Invasion of Ikoria has `"defense": "6"`, and its back face, Zilortha, Apex of Ikoria, is 8/8. Our cards import drops it, for two reasons: the `face` table has no `defense` column, and `single_face_value` in `magic/multiverse.py` copies `power`, `toughness` and `loyalty` but not `defense`. Upstream issue [PennyDreadfulMTG#11170](https://github.com/PennyDreadfulMTG/Penny-Dreadful-Tools/issues/11170) (2023) covers adding it. Decided 2026-10-05: defense stays out of a card's numbers until the import is fixed ([#38](https://github.com/violetteavi/Penny-Dreadful-Tools/issues/38), a standalone upstream PR); #36 can add it afterwards.

### Reprints whose text names the card are identical when masked

Lightning Strike and Searing Spear are both {1}{R} instants reading "[this card] deals 3 damage to any target." Scryfall's text names each card ("Lightning Strike deals 3 damage…", "Searing Spear deals 3 damage…"), so their base text differs only in the name.

- **Expect:** in the masked format their text is identical ("~ deals 3 damage to any target."), so their text vectors are identical (similarity 1). In the base format they are not.
- **Why it matters:** the first reprint scenario's cards don't name themselves, so it can't catch this. Reprints that do are common among burn spells; potion put Searing Spear only #22 for Lightning Strike in the base format.
- **Check:** the masked texts are equal, and the masked text similarity is 1.

### A modal double-faced card is close to cards like each of its faces

Hagra Mauling // Hagra Broodpit is removal on its front ({2}{B}{B} instant, "This spell costs {1} less to cast if an opponent controls no basic lands. Destroy target creature.") and a land on its back ("This land enters tapped. {T}: Add {B}."). Murder ({1}{B}{B} instant, "Destroy target creature.") does the front's job; Barren Moor (land, "This land enters tapped. {T}: Add {B}. Cycling {B}") does the back's.

- **Expect:** both Murder and Barren Moor are among Hagra Mauling's nearest neighbours.
- **Why it matters:** a modal double-faced card is played as either face, so a deck playing it resembles decks playing either kind of card.
- **Not yet met** ([#40](https://github.com/violetteavi/Penny-Dreadful-Tools/issues/40)): with potion on masked text, Hagra Mauling's neighbours are tapped lands and other modal double-faced cards (text alone), or generic 4-mana black cards (with average thirds at α 0.5), and neither list has Murder or cheap removal. No test until #40.
- **Check:** Murder's and Barren Moor's ranks in Hagra Mauling's list.

### Adding a set changes no other card's vector

Season 43 added 461 cards that are new to the pool, 148 of them from The Hobbit (HOB).

- **Expect:** embed the cards legal in seasons 1–42, then embed the full pool including those 461. Every card in both runs gets the same vector, up to floating-point noise from batching (each element within 1e-5).
- **The numbers too:** a card's numbers depend only on the card. The statistics that combine them with the text (colour centring, and for average thirds the fill values, standardisation and group scales) are fitted once and frozen. So a new set's cards are scaled with the old statistics, and no existing card moves. Refitting is a deliberate new version, not a side effect of adding a set.
- **Why it matters:** a new set arrives about every two months. A frozen encoder reads each card on its own, so adding cards should need no other change: no re-embedding of old cards and no retraining of the encoder. If old vectors moved, every model built on them would have to be refitted at each set.
- **Check:** compare the two runs' vectors for the shared cards. Also report how long the 461 new cards take to embed with each encoder.
- **How it's checked:** a unit test with a fake encoder; a local test with each real encoder over a sample (1,000 cards from season 42 plus the scenario cards, then the same with the 461 added); and the #7 stage 1 experiment (on the tag `card-encoder-exploration`), which embedded the 461 on their own and merged them in, as a new set would really be added, and re-embedded 461 older cards in a different batch to measure the noise (at most 1.3e-7).

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

All scenarios here were confirmed 2026-10-01.

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
| K | 30 | no | VERIFIED, but a 59-card maindeck (4 Shock, 55 Mountain) | EXCLUDED | maindeck under 60 cards |

- **Expect:** each deck gets the split and reason in its row.
- **Why it matters:**
  - Deck H is an unlabelled deck from a test season. It can only become TEST or EXCLUDED, never TRAIN, so no model can learn the test seasons' new cards from it.
  - Decks J and K have broken data. Every legal maindeck has at least 60 cards, and the local database has 19 decks with fewer, as few as 8, which are probably broken imports.
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

**Scheme:** the typical scheme. There are three 60-card decks, and every card in them is legal in both seasons 30 and 41:
- **A:** season 30, not held out, VERIFIED, maindeck 4 Shock and 56 Mountain. It becomes TRAIN.
- **B:** season 30, not held out, UNLABELLED, maindeck 4 Burst Lightning and 56 Mountain. It becomes EXCLUDED (status not used for training).
- **C:** season 41, VERIFIED, maindeck 4 Shock, 4 Burst Lightning and 52 Mountain. It becomes TEST.

- **Expect:**
  - C has **4** unseen maindeck copies (the four Burst Lightning). B contains Burst Lightning but isn't a training deck, so it doesn't make Burst Lightning seen.
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

### A large maindeck loads in full

Deck 217677, "Life is EZ 112", is a season 29 League deck labelled Life is Ez. It has a 112-card maindeck and a 15-card sideboard. Maindecks can be much larger than 60 cards: 10,365 local decks are, up to 1,400 cards.

- **Expect:**
  - the snapshot freezes it, with a maindeck hash over all 112 cards
  - it isn't excluded, because 112 is at least 60
  - loading its contents returns 112 maindeck cards and 15 sideboard cards
- **Why it matters:** nothing in loading or hashing may assume a 60-card maindeck.
- **Check:**
  - a seeded test with a 112-card maindeck (4 Shock and 108 Mountain, both legal in season 29), so it runs without the local dump
  - once, in the rebuild verification, deck 217677 itself

### Card legality is per season

- **Expect:** loading the legal cards for seasons 30 and 41 gives Shock, Burst Lightning and Mountain in both. Lightning Bolt and Fireblast are in neither.
- **Why it matters:** the baseline's playability weights count only the seasons in which each card was legal, as the site does.
- **Check:**
  - a seeded test that inserts those legal-card rows
  - once, in the rebuild verification, the real seasons 30 and 41

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

## Model inputs

These scenarios belong to the experiment harness (#26). A deck set picks the decks, and conversion functions only change their shape: they attach each deck's cards and keep just the fields a model may see.

The decks used below:
- **Deck 1:** season 39, League, VERIFIED, labelled Red Deck Wins. Maindeck 4 Shock and 56 Mountain; sideboard 2 Smash to Smithereens.
- **Deck 2:** season 39, League, VERIFIED, labelled Azorius Control. Maindeck 4 Essence Scatter and 56 Island; sideboard 2 Negate.
- **Deck 3:** season 30, League, UNVERIFIED (labelled Red Deck Wins by an automatic guess only), reviewed. Maindeck 4 Shock and 56 Mountain.
- **Deck 4:** season 30, League, UNLABELLED, not reviewed. Maindeck 4 Shock and 56 Mountain.

Every card is legal in seasons 30 and 39.

All scenarios here were confirmed 2026-10-01.

### Labelled and prediction decks come from the same deck set

**Scheme:** the typical scheme (season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED}; twins off). Decks 1 and 2 are VALIDATION. The deck set is VALIDATION.

- **Expect:**
  - **Labelled decks:** deck 1 is labelled Red Deck Wins and deck 2 Azorius Control, each with its maindeck hash as its group key.
  - **Prediction decks:** the same two decks with the same cards and source, and no label at all.
  - **Both:** each deck's maindeck is its 60 cards and its sideboard its 2 cards, kept apart.
- **Why it matters:** a model tunes on labelled decks and predicts on label-free ones, so the answer can't leak into a prediction.
- **Check:** convert the VALIDATION deck set both ways and compare.

### Training decks carry the site label and the label status

**Scheme:** season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED, UNVERIFIED, UNLABELLED}, eval {VERIFIED}; twins off. Decks 3 and 4 are TRAIN. The deck set is TRAIN.

- **Expect:**
  - **Deck 3:** archetype Red Deck Wins (its site label), status UNVERIFIED, reviewed.
  - **Deck 4:** no archetype, status UNLABELLED, not reviewed.
  - **Both:** season 30.
- **Why it matters:** a model trained on several statuses needs to tell them apart, and one that mimics the site needs the reviewed flag.
- **Check:** convert the TRAIN deck set.

### The same deck always gives the same input

**Scheme:** the typical scheme. Deck 1's contents are given with their lines in a different order.

- **Expect:** the prediction deck is identical: maindeck and sideboard lines come out sorted by card name.
- **Why it matters:** a model, and a fingerprint of its inputs, must not depend on the order the database returned rows in.
- **Check:** convert deck 1 from both orders and compare.

### A deck whose contents are missing is skipped with a warning

**Scheme:** the typical scheme. The deck set has decks 1 and 2, but contents are given only for deck 1, for example because deck 2 was deleted from the site after the snapshot.

- **Expect:** each conversion returns deck 1 only, and logs a warning naming deck 2 and a count of **1** skipped deck. Deck 1's input is exactly as if deck 2 weren't in the set.
- **Why it matters:** data problems are non-fatal: the run carries on and says what it skipped.
- **Check:** convert the deck set with deck 2's contents missing.

### A model is found by its name

- **Expect:** a model class registered under a name, such as "most common archetype", can be looked up by that name, and an unknown name raises an error that lists the registered names.
- **Why it matters:** a stored model records only its name, version and parameters, so loading it needs the class from its name.
- **Check:** register a model class, then look it up by name, and look up a name that isn't registered.

## Storing models and runs

These scenarios belong to the model and run store (#23). A fitted model is saved as its record and what fitting learned, never its decks. A run is saved as one guess per deck, never as scores.

They use a mock model, **most common archetype**: fitting stores the most common archetype among the training decks, and it always guesses that archetype. It's the simplest real model to save and load, and a floor every later model should beat.

**Decks:** 60-card League decks of 4 Shock and 56 Mountain (Red Deck Wins), or 4 Essence Scatter and 56 Island (Azorius Control), all legal in seasons 30 and 39. Unless a scenario says otherwise:
- **Training decks:** 101, 102 and 103 (Red Deck Wins) and 104 and 105 (Azorius Control), VERIFIED, season 30.
- **Validation decks:** 201 (Red Deck Wins) and 202 (Azorius Control), VERIFIED, season 39.

**Scheme**, unless a scenario says otherwise: the typical scheme (season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED}; twins off). Snapshot 1 and scheme 1. The model trains on {TRAIN} and tunes on {VALIDATION}, with seed 0.

**What identifies what:**
- A model's **identity** is its name, version, parameters, snapshot, scheme, training splits, validation splits and seed.
- A model also records **fingerprints** of the decks it actually trained and tuned on: the deck ids left after skipping any with missing contents.
- A run records its model, its scope, and a fingerprint of the decks it actually predicted on.

**The rules:**
- **The same model on the same decks must give the same result, or it's an error.**
- **Data that changed underneath** (a deck since deleted from the site) is a warning. The old record stays valid, and anything new gets a new id.
- **Ids are never reused.**

All scenarios here were confirmed 2026-10-01.

### The mock model guesses the most common training archetype

- **Expect:**
  - every deck it predicts on, whatever its cards, is guessed **Red Deck Wins**, with evidence of 3 training decks out of 5
  - its saved state is the Red Deck Wins archetype id and the two counts behind its evidence (3 and 5), so a reloaded model reports the evidence it was fitted with
- **Expect, with a tie** (decks 101, 102, 104 and 105): the archetype with the lower id wins, so fitting twice always gives the same guess.
- **Expect, with no labelled training decks:** every deck gets no guess.
- **Check:** fit on each set of training decks, then predict on decks 201 and 202.

### A saved model loads back and predicts the same

The mock model is fitted and saved. It gets id 1.

- **Expect:**
  - **The record:** name "most common archetype", version 1, its parameters, snapshot 1, scheme 1, seed 0, training splits {TRAIN}, validation splits {VALIDATION}, fit time, and:
    - training: **5** decks and the fingerprint of decks 101–105
    - validation: **2** decks and the fingerprint of decks 201 and 202
  - **Its state:** the Red Deck Wins archetype id and the counts 3 and 5, as JSON.
  - **Loading model 1:** gives back the same record and a model whose predictions on 201 and 202 are identical, with no warning.
- **Why it matters:** a stored model has to be reusable later without refitting, and its record has to say exactly which decks trained and tuned it.
- **Check:** save, load, and predict again.

### Saving the same model again returns its id

Model 1 is fitted again: same identity, same decks.

A model counts as **the same model** as a stored one when all three of these match, checked in order:
1. **Identity:** name, version, parameters, snapshot, scheme, training splits, validation splits and seed.
2. **Decks:** the training and validation fingerprints, so it learned from exactly the same decks.
3. **Result:** its state, what fitting learned.

If only the first two match, the same model gave a different result (the next scenario). If only the identity matches, the data changed underneath (the one after).

- **Expect:** all three match model 1, so saving returns id **1**. No new model is stored, and nothing is logged.
- **Why it matters:** re-running an experiment shouldn't pile up copies of one model.
- **Check:** fit and save twice, then count the stored models.

### A fit that isn't deterministic fails loudly

A stand-in model whose fitting picks its archetype at random, ignoring the seed, is fitted twice with the same identity on the same decks, and its two states differ.

- **Expect:**
  - the first save gets an id
  - the second raises an error that names that id and both states, and stores nothing
- **Why it matters:** the same model on the same decks must give the same result. A seed that doesn't control all the randomness is a bug to fix, not a second result to keep.
- **Check:** save the stand-in model twice.

### Training data that changed underneath gives a new model and a warning

Model 1 was saved. Then decks 101 and 102, two of the Red Deck Wins decks, are deleted from the site, so their contents are missing. The mock model is fitted again with the same identity.

- **Expect:**
  - **Fitting:** decks 101 and 102 are skipped with a warning (as in "Model inputs"), so the model trains on **3** decks: one Red Deck Wins and two Azorius Control. It now guesses **Azorius Control**, with evidence of 2 training decks out of 3.
  - **Saving:** the training fingerprint differs from model 1's, so it's saved as model **2**, with a warning that the training decks changed since model 1 and model 1 can no longer be reproduced.
  - **Model 1:** keeps its id, record and state, so it still guesses Red Deck Wins. It still loads and predicts, with a warning that its 5 recorded training decks now rebuild as 3.
- **Why it matters:** a model keeps its value even when its training data is gone. We just can't reproduce it, and nothing new may take its id.
- **Check:** save model 1, remove the contents of decks 101 and 102, refit and save, then load model 1.

### A different identity is a different model

Starting from model 1, change one part of the identity at a time:
- seed 1
- validation splits {HELD_OUT, VALIDATION}
- another scheme
- version 2

- **Expect:** each is saved as a new model with its own id, and nothing is logged. Training the same model on different data is a normal experiment.
- **Check:** save model 1 and each variant, then count the stored models.

### A run stores one guess per deck, never scores

Model 1 predicts on validation decks 201, 202 and 203. Deck 203 is a third validation deck, and the prediction for it has no guess, as a model gives when it's unsure.

- **Expect:**
  - **The run record:** model 1, scope {VALIDATION}, row-set version, **3** decks, the fingerprint of decks 201–203, a prediction hash, and the time and duration. It gets id 1.
  - **The guesses:** they load back exactly, including deck 203's missing guess (stored as null) and each guess's evidence.
  - **The hash:** the same predictions in another order give the same prediction hash.
- **Why it matters:** scores are recomputed from stored guesses (decision F).
- **Check:** save the run, load its guesses, and hash the predictions in two orders.

### The same model on the same decks must guess the same

Run 1 above is saved. Model 1 then predicts on decks 201–203 again.

- **Expect, with the same guesses:** saving returns run id **1**. No new run is stored.
- **Expect, with deck 202 guessed differently:** saving raises an error that names run 1 and both prediction hashes, and stores nothing.
- **Expect, after deck 202 is deleted from the site:** the model predicts on decks 201 and 203 only, so the input fingerprint differs. The run is saved as run **2**, with a warning that its decks changed since run 1. Run 1 keeps its id and guesses.
- **Why it matters:** a different result from the same model on the same decks is a bug, and must not be stored as a second answer. Changed data is not a bug, so it's kept, and flagged.
- **Check:** save run 1, then each variant.

### A relabel on the site changes nothing in an existing snapshot

Model 1 was saved from snapshot 1. Deck 106 (season 30, a 60-card list of 4 Negate and 56 Island) was in snapshot 1 with only an automatic label, Azorius Control: UNVERIFIED, so EXCLUDED under the typical scheme. Afterwards, a person reviews it on the site and relabels it **Azorius Tempo**, so it's now VERIFIED.

- **Expect, in snapshot 1:**
  - deck 106 is still UNVERIFIED Azorius Control and EXCLUDED
  - model 1 still loads quietly: its training decks rebuild exactly
  - refitting model 1 returns id 1
- **Expect, in snapshot 2,** taken after the relabel:
  - deck 106 is VERIFIED Azorius Tempo, and becomes TRAIN if its maindeck isn't held out
  - fitting the mock model there is a different identity (snapshot 2), so it's saved as a new model with no warning
  - it trains on 6 decks: 3 Red Deck Wins, 2 Azorius Control and 1 Azorius Tempo, so it still guesses Red Deck Wins (3 out of 6)
- **Why it matters:** labels, label facts, statuses and the archetype tree are frozen in a snapshot, and only deck contents are read live. So a relabel can never change what an existing model learned from. A newer snapshot sees it, as a new experiment.
- **Check:** save model 1, relabel deck 106 on the site, load and refit model 1, then take snapshot 2 and fit on it.

### Every look at the test seasons is logged

- **Expect:** each call to log a test look records the run, the rows scored (for example "test, overall" and "test, by unseen copies") and the time. Three looks give three entries, in order.
- **Why it matters:** the test seasons are looked at rarely, and the log shows how often.
- **Check:** log three looks for one run and read the log back.

## Rows of the results table

These scenarios belong to the row set (#27). A row is a named, versioned group of scored decks, such as "test, 13+ unseen copies". Rows are built from the deck set that was scored, and the training deck set, then each row is scored from a run's stored guesses with the metrics module. Scores are never stored (decision F).

**Decks.** Each is a VERIFIED League deck unless it says otherwise. "Maindeck A" means two decks share an identical maindeck.

| Deck | Split | Unseen maindeck copies | Maindeck |
|---|---|---|---|
| 101 | TRAIN | 0 | A |
| 102 | TRAIN | 0 | B |
| 301 | HELD_OUT | 0 | its own |
| 302 | HELD_OUT | 3 | its own |
| 201 | VALIDATION | 0 | A (repeats deck 101) |
| 202 | VALIDATION | 0 | its own |
| 401 | TEST | 0 | B (repeats deck 102) |
| 402 | TEST | 2 | its own |
| 403 | TEST | 7 | its own |
| 404 | TEST | 15 | its own |

**Scheme**, unless a scenario says otherwise: the typical scheme (season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED}; twins off). The model trained on {TRAIN} and tuned on {VALIDATION}.

**Repeated maindeck:** another TRAIN deck has the same maindeck. Only a deck with 0 unseen copies can repeat one, since every card in a TRAIN maindeck is seen.

All scenarios here were proposed 2026-10-01.

### Scoring held-out and validation decks gives their rows

The scored deck set is {HELD_OUT, VALIDATION}.

- **Expect these rows,** and no others:

  | Row | Decks |
  |---|---|
  | held-out, no unseen cards | 301 |
  | held-out, unseen cards | 302 |
  | validation | 201, 202 |
  | validation, new maindeck | 202 |
  | validation, repeated maindeck | 201 |

- **Expect, flags:** the validation rows are marked tuned on. Nothing is marked trained on.
- **Expect, no held-out maindeck rows:** with twins off, every held-out deck is new by construction, so those rows would say nothing.
- **Why it matters:** these are the rows we read most often while developing, and the repeated-maindeck row shows how much of a score comes from decks the model has effectively seen.
- **Check:** build the rows for the scored and training deck sets, and score each from a run's guesses.

### Test rows split by unseen copies, and need the gate

The scored deck set is {TEST}.

- **Expect these rows, with the gate:**

  | Row | Decks |
  |---|---|
  | test, overall | 401, 402, 403, 404 |
  | test, 0 unseen copies | 401 |
  | test, 1–4 unseen copies | 402 |
  | test, 5–12 unseen copies | 403 |
  | test, 13+ unseen copies | 404 |
  | test, new maindeck | 402, 403, 404 |
  | test, repeated maindeck | 401 |

- **Expect, without the gate:** scoring raises an error, and nothing is scored or logged. The deck set itself can only be built with `include_test`, but the rows check again.
- **Expect, with the gate:** one test look is logged for the run, naming the seven test rows scored.
- **Why it matters:** the test seasons are the main measure of unseen cards, and they're looked at rarely.
- **Check:** score the test rows with and without the gate, and read the run's test looks.

### Scoring the training decks gives one in-sample row

The scored deck set is {TRAIN}.

- **Expect:** one row, "train, in-sample", with decks 101 and 102, marked trained on.
- **Why it matters:** it shows how well the model fits the decks it learned from, which isn't a generalisation score.
- **Check:** build and score the rows for the TRAIN deck set.

### Unverified labels get their own row

**Scheme:** season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED, UNVERIFIED}; twins off. Deck 303 is HELD_OUT and UNVERIFIED (labelled by an automatic guess only), with 0 unseen copies. The scored deck set is {HELD_OUT}.

- **Expect:**
  - "held-out, no unseen cards" still holds deck 301 only, and "held-out, unseen cards" deck 302 only: the other rows hold VERIFIED decks only
  - a row "held-out, unverified labels" holds deck 303
- **Expect, under the typical scheme:** deck 303 is EXCLUDED, so there's no unverified row.
- **Check:** build the rows under both schemes.

### Rows the model tuned on are flagged

The model tuned on {HELD_OUT, VALIDATION} instead. The scored deck set is {HELD_OUT, VALIDATION}.

- **Expect:** every held-out and validation row is marked tuned on. Their scores are optimistic, and a report says so.
- **Check:** score the rows with the model's validation splits {HELD_OUT, VALIDATION}.

### A deck with no stored guess is skipped with a warning

The run's guesses cover deck 201 but not deck 202, for example because deck 202's contents were missing when the run was made.

- **Expect:** "validation" is scored on deck 201 only. A warning names deck 202 and a count of **1** skipped deck, and the row's results record that 1 deck was skipped. A deck whose stored guess is "no guess" is different: it's scored, as a guess of the root.
- **Why it matters:** data problems are non-fatal, but a row's deck count must say what it really covers.
- **Check:** score the validation rows from guesses that leave out deck 202.

### A row with no decks is left out

The scored deck set is {HELD_OUT}, but neither held-out deck has unseen cards (deck 302 has 0 unseen copies instead).

- **Expect:** there's no "held-out, unseen cards" row, and a log line names it as empty. The metrics module can't score an empty set, and an empty row would show nothing.
- **Check:** build the rows when one would be empty.

### Rows are versioned

- **Expect:** the row set has a version number, 1. Any change to which rows exist or which decks they hold bumps it, and every report records it, with the metrics version and PR number (decision F).
- **Check:** the version is exposed beside the row-building function.

## Experiment reports

These scenarios belong to the report (#28). A report turns one stored run into a Markdown write-up, committed in `docs/experiments/`. Scores are recomputed from the run's stored guesses every time a report is made, never stored (decision F). The report records the versions and PR numbers needed to recover what produced them.

**Decks** (from "Rows of the results table"), each VERIFIED, under the typical scheme (season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED}, eval {VERIFIED}; twins off):

| Deck | Split | Label |
|---|---|---|
| 101 | TRAIN | Red Deck Wins |
| 102 | TRAIN | Azorius Control |
| 301 | HELD_OUT | Red Deck Wins |
| 302 | HELD_OUT | Azorius Control |
| 201 | VALIDATION | Red Deck Wins |
| 202 | VALIDATION | Azorius Control |

The tree: Aggro › Red Deck Wins, and Control › Azorius Control.

**Runs:**
- **Run 1:** model 1, the mock "most common archetype" model, version 1, trained on {TRAIN} and tuned on {VALIDATION}. Scope {HELD_OUT, VALIDATION}. It guesses Red Deck Wins for every deck.
- **Run 2:** a baseline run of another model on the same decks. It guesses Red Deck Wins for 301 and 201, and **Control** (a parent fallback) for 302 and 202.

The report is made with a macro minimum of 1 deck per archetype, and PR numbers #6 and #31.

All scenarios here were confirmed 2026-10-02.

### The header says exactly what produced the numbers

- **Expect:** a header listing:
  - **The run:** run id 1, scope {HELD_OUT, VALIDATION}, 4 decks predicted, its prediction hash, and when it was made.
  - **The model:** model id 1, "most common archetype" version 1, its parameters, seed, snapshot 1, scheme 1 by name, training splits {TRAIN} and validation splits {VALIDATION}, and its training and validation deck counts.
  - **The code:** `METRICS_VERSION` 1, `ROWS_VERSION` 1, and PRs #6 and #31.
- **Why it matters:** a committed report is the record of what was measured. Numbers may not reproduce after a metric change, but the versions and PRs say which code produced them.
- **Check:** render run 1 and read the header.

### The results table has one line per row, with intervals

- **Expect:** one line per row from the row set, in its order: "held-out, no unseen cards", "held-out, unseen cards", "validation", "validation, new maindeck" and "validation, repeated maindeck". Each line gives:
  - decks and distinct maindecks
  - micro hF, hP and hR, each with its 95% interval
  - exact-match rate and coverage
  - macro hF, with the number of archetypes it averages
  - notes: "tuned on" for the validation rows, "trained on" where it applies, and how many decks were skipped for having no stored guess
- **Expect, for "validation"** (decks 201 and 202): micro hP **0.50**, hR **0.50**, hF **0.50**, exact match **0.50**, coverage **1.00**. Deck 201 is exact. Deck 202, Azorius Control guessed as Red Deck Wins, shares nothing with its label.
- **Why it matters:** n and intervals on every line keep small rows from looking more certain than they are.
- **Check:** render run 1 and read the "validation" line.

### Archetypes appear by name, and confusions link to example decks

- **Expect:** a "Top confusions" section for each scored split, using that split's widest row ("held-out" combines both held-out rows, then "validation"). Each confusion shows:
  - the label and guess by name ("Azorius Control → Red Deck Wins")
  - whether it's on or off the label's path (here, off)
  - its deck count
  - up to 3 example decks, linked as `https://pennydreadfulmagic.com/decks/202/`
- **Expect, an archetype missing from the snapshot's tree:** it shows as "missing archetype 999", never as a bare id.
- **Why it matters:** the confusions are where a reviewer starts, and the links let anyone open the decks behind them, since local deck ids match the public site.
- **Check:** render run 1 and read the validation confusions.

### A baseline run is compared deck by deck

Run 1 is rendered with run 2 as its baseline.

- **Expect:** a "Compared with run 2" section, with one line per row, giving run 1 minus run 2 for hF, hP, hR and exact-match rate, each with its paired interval, plus the number of decks compared and left out. For "validation":
  - **Run 2:** micro hP **1.00**, hR **0.75**, hF **0.86**. Deck 202's guess, Control, is correct as far as it goes.
  - **Difference** (run 1 minus run 2): hP **−0.50**, hR **−0.25**, hF **−0.36**, exact match **0.00**.
  - 2 decks compared, 0 left out.
- **Expect, without a baseline:** no comparison section.
- **Why it matters:** this is how we decide whether a model beats today's guesser. Two separate intervals side by side would miss a consistent difference.
- **Check:** render run 1 with and without run 2 as its baseline.

### A validation curve is shown when the model has one

- **Expect:** a model whose state includes a validation curve, a list of (threshold, hP, hR, hF), gets a "Validation curve" table, with the chosen threshold marked. The mock model has no threshold, so its report says "No validation curve: this model has no threshold to tune."
- **Check:** render a run of the mock model, and of a stand-in model whose state has a three-point curve.

### Test results need the gate, and each report logs one look

A run whose scope is {TEST}.

- **Expect:**
  - rendering it without `include_test` raises an error, and nothing is logged
  - with it, the report renders and one test look is logged for the run, naming the test rows
- **Why it matters:** a report is the usual way test numbers are seen, so it goes through the same gate as scoring.
- **Check:** render the test run with and without the gate, then read its test looks.

### The same run always gives the same report

- **Expect:** rendering run 1 twice gives identical Markdown, byte for byte. The bootstrap uses the metrics module's fixed seed, and the report contains no time of its own, only the run's stored time.
- **Why it matters:** a re-rendered report shows a real difference only when something real changed.
- **Check:** render run 1 twice and compare.

### A report is written to `docs/experiments/` from the command line

- **Expect:** running the report command with a run id, an optional baseline run id, the PR numbers, the macro minimum, `include_test` when needed, and an output path writes the Markdown there. The command prints the path.
- **Check:** run the command for run 1 into a temporary folder and compare the file with the rendered Markdown.

### Metrics are versioned

- **Expect:** the metrics module has a version number, 1. Any change to how a metric is computed bumps it, and every report records it.
- **Check:** the version is exposed beside the scoring functions.

## The similarity baseline

These scenarios belong to the similarity baseline (#6). It's today's guesser, reimplemented with sparse matrices so it can guess for tens of thousands of decks:
- **Weights:** each card is weighted by 1 / max(playability, 0.001), with playability computed by the site's formula from the training decks only.
- **Similarity:** the summed weights of the maindeck lines two decks share (same card *and* quantity), divided by the larger deck total, as a rounded whole percentage.
- **Candidates:** only decks sharing a non-basic maindeck card name are compared.
- **Picking a label:** a League deck copies the label of its highest-ranked match that is reviewed and labelled. A Gatherling deck copies the label of its single top match.
- **Threshold:** a match must reach it. With no qualifying match, the deck gets no guess (the root).

**Scheme** for every scenario here is scheme 2, "similarity baseline": season rule 1–38 / 39 / 40–42 with 10% held out; status rule train {VERIFIED, UNVERIFIED}, eval {VERIFIED}; twins off. The model trains on its 202,385 TRAIN decks and tunes on its 2,249 VALIDATION decks (season 39).

**Real decks.** Unless a scenario says it's a rule-level check, the decks are real decks from snapshot 1, identified by id. The numbers were computed with the site's own formula and checked against its `similarity_score`.

All scenarios here were proposed 2026-10-02 and revised the same day to use real decks.

### Weights come from the training decks, by the site's formula

- **Expect:**
  - **Typical weights:**

    | Card | Playability | Weight |
    |---|---|---|
    | Island | 0.38226 | 2.6 |
    | Mountain | 0.32338 | 3.1 |
    | Burst Lightning | 0.13110 | 7.6 |
    | Make Disappear | 0.00173 | 578.0 |

  - **The floor:** 79% of the 23,416 cards legal in the training seasons have playability below 0.001, so they weigh the floor, **1,000**. That's also the weight of a card no training deck plays, such as Archmage's Charm in season 39.
  - **Only training decks** and the training seasons count. A card played only in a sideboard counts 0.2 of a deck, and playability is rounded to 5 decimals, as on the site.
- **Why it matters:** the weights must not see the decks being scored. Most of the card pool sits at the floor, so an unseen card weighs no more than a rarely played one.
- **Check:** fit on scheme 2's TRAIN decks and read the weights of these cards.

### A deck identical to training decks matches at 100%, and ties go to the higher id

Deck 269508, a season 39 League "Oops All Lands" deck with 0 unseen copies (21 distinct cards, total weight 2,106). Its maindeck is identical to two training decks, 264496 and 264554.

- **Expect:**
  - **Scores:** 264554 and 264496 at **100**, then 262588 at 79.
  - **Ranking:** the tie at 100 goes to the higher deck id, so 264554 comes first.
  - **Guess:** Oops All Lands, with evidence: match 264554, score 100, rule League.
- **Check:** predict deck 269508 at the site's threshold of 20.

### A match needs the same card and quantity

Deck 269508 again, against training deck 262588, another Oops All Lands deck.

- **Expect:** a score of **79**, not 100. They share most cards, but these lines differ in quantity, so they don't count as shared:
  - Deserted Temple: 4 in 269508, 2 in 262588
  - Temple of Deceit: 4 and 3
  - Temple of Malady: 4 and 1
  - Temple of Epiphany: 4 and 2
  - Island: 4 and 1

  Cards in only one of the two decks also don't count: Forbidden Orchard, Flooded Grove, Temple of Silence, Temple of Enlightenment, Geier Reach Sanitarium and Forest.
- **Check:** score 269508 against 262588.

### Unseen cards lower the chance of a usable match

Real season 39 League decks. No season 39 deck has more than 27 unseen copies, since basic lands are always seen.

- **Expect:**

  | Deck | Label | Unseen copies | Unseen lines | Total weight | Best match | Guess at 20 |
  |---|---|---|---|---|---|---|
  | 269508 | Oops All Lands | 0 | none | 2,106 | 264554 at 100 (Oops All Lands) | Oops All Lands, exact |
  | 269653 | Izzet Madcap | 5 | 4 Archmage's Charm, 1 Shark Typhoon | 3,079 | 244684 at **21** (Izzet Spells) | **Izzet Spells: wrong branch** |
  | 269833 | Azorius Legends Aggro | 5 | 1 Jill, Shiva's Dominant, 4 Seachrome Coast | 2,642 | 264566 at 17 (Azorius Legends Aggro) | no guess |
  | 269466 | Hardened Scales Affinity | 12 | 4 Marketback Walker, 4 Rust Harvester, 4 Stomping Ground | 3,615 | 264841 at 9 (Hardened Scales Affinity) | no guess |
  | 269940 | Midrange | 27 (the most in season 39) | seven lines, including 3 Breeding Pool and 4 Zanarkand, Ancient Metropolis | 10,254 | 269227 at 10 (Mono Blue Control) | no guess |

- **Expect, deck 269653:** its 21% comes almost entirely from one shared line, 4 Make Disappear (weight 578). Its two unseen lines add 2,000 to its total, while a near-match on the rest of the deck still counts for little. Its label, Izzet Madcap, is under Control › Izzet Control, and the guess, Izzet Spells, is under Aggro-Control, so it scores hF 0 with no partial credit.
- **Expect, on the whole validation season:** the share of decks whose best match reaches 20 falls with unseen copies. In a sample of 300, it's:

  | Unseen copies | 0 | 1–3 | 4–5 | 6–8 | 9–12 | 13+ |
  |---|---|---|---|---|---|---|
  | Best match ≥ 20 | 98 / 100 | 33 / 38 | 32 / 51 | 27 / 62 | 7 / 31 | 2 / 18 |

  The experiment reports the full rows.
- **Why it matters:** a deck's total weight counts its unseen cards at 1,000 each, while they can never be shared. So a few new cards make a good match look weak, or let a single rare shared card produce a confident wrong guess. This is what later models must beat after a rotation.
- **Check:** predict these five decks at threshold 20, and score each against its best match.

### Decks with no unseen cards but no exact match

Real season 39 League decks with 0 unseen copies whose maindeck repeats no training deck. "Off by N" is how many maindeck cards would have to change to turn the deck into its closest training deck: 60 minus the copies they share, same card and quantity.

- **Expect:**

  | Deck | Label | Off by | Closest training deck | Score to it | Best-scoring match | Guess at 20 |
  |---|---|---|---|---|---|---|
  | 269539 | Mono Green Stompy | **4** | 269464 (season 38, Mono Green Stompy) | 73 | the same deck, at 73 | Mono Green Stompy, exact |
  | 269503 | Selesnya Heroic | **12** | 269180 (season 38, Selesnya Heroic) | 49 | the same deck, at 49 | Selesnya Heroic, exact |
  | 270398 | Orzhov Midrange | **20** | 264080 (season 37, Orzhov Blink) | 11 | 246062 (season 33, Mono White Humans), at **29** | **Mono White Humans: wrong branch** |

- **The differences:**
  - **269539:** 4 Swarm Shambler in place of 269464's 4 Pawpatch Recruit.
  - **269503:** against 269180, it has 4 Cartouche of Solidarity, 4 Ethereal Armor and 2 Oppressive Rays in place of 4 Meltstrider's Resolve, 4 Spider Umbra and 2 Solid Footing. It also has 2 Forest and 8 Plains, where 269180 has 4 and 6.
  - **270398:** it shares most of its basics with Mono White Humans deck 246062, but its rare cards (Grand Abolisher, Shambling Vent, Vindicate and others) don't line up with any one training deck.
- **Expect, deck 270398:** the training deck closest by cards isn't the best-scoring one. The weighted score rewards whichever deck shares the rarest lines, here a Mono White Humans deck. So it guesses Mono White Humans (Aggro › White Weenie) for an Orzhov Midrange deck (Midrange), which scores hF 0.
- **Why it matters:** even with no new cards, the score falls fast as a deck drifts from its nearest list: 73 at 4 cards off, 49 at 12, 11 at 20. Beyond that, the best match can be a different strategy that happens to share rare cards.
- **Check:** predict these three decks at threshold 20, and score each against its closest training deck.

### League decks skip unreviewed matches, and Gatherling decks don't (a rule-level check)

Every one of scheme 2's 202,385 training decks is reviewed, so this never changes a pick in the real data. It's still the site's rule, so it's checked with four small decks: 60-card season 30 lists of 4 Shock and 56 Mountain, with these differences:
- **The query:** 2 Shock, 4 Burst Lightning, 54 Mountain.
- **Its identical twin:** an unreviewed Red Deck Wins training deck.
- **Two reviewed training decks,** one labelled Red Deck Wins and one Burn.

- **Expect:**
  - **As a League deck:** the unreviewed twin scores 100 but is skipped, so the guess comes from the best reviewed match.
  - **As a Gatherling deck:** the guess comes from the twin.
- **One difference from the site:** the site also searches unlabelled decks, so a Gatherling deck whose top match is unlabelled gets no guess there. Our training decks are all labelled, so it takes the next. The real-data check counts how often this happens.
- **Check:** predict the query with each source.

### Sharing only a basic land isn't a match (a rule-level check)

On real decks, a shared basic land line weighs a few points against totals in the thousands, so it never reaches a threshold. It's still the site's rule, so it's checked with small decks: a query of 4 Essence Scatter, 4 Negate and 52 Mountain, and a training deck of 4 Shock, 4 Burst Lightning and 52 Mountain. They share only "52 Mountain".

- **Expect:** the training deck isn't a candidate, even at a threshold of 1, because the two share no non-basic card.
- **Check:** predict the query at threshold 1.

### The tuned threshold maximises hF on the validation decks

- **Expect:**
  - **The tuned model** sweeps every whole-number threshold from 1 to 100 on scheme 2's 2,249 VALIDATION decks, scoring each with micro hF, and keeps the best. On a tie, it keeps the threshold nearest the site's 20.
  - **The fixed model** keeps 20, with no tuning, but still records the curve for the report.
  - **Both states** keep the curve and the chosen threshold, under the documented convention.
  - **On the small rule-level decks,** where every guess made is correct, thresholds tie at the best hF, and the one nearest 20 is chosen.
- **Check:**
  - fit both models on scheme 2 and read their states
  - unit-test the tie rule on the small decks

### Scores match the site's own function

- **Expect:** for every pair of decks above, the baseline's score equals the site's `similarity_score` given the same weights, × 100 and rounded. For example, deck 269508 against 262588 scores 0.79, giving 79.
- **Check:** compare with `decksite.data.deck.similarity_score`, on the rule-level decks without a database, and on the real decks above in the real-data check.

### A fitted baseline loads back and guesses the same

- **Expect:** the state holds the card weights, the threshold and the curve, never the decks. Rebuilt from its state and the same training decks, the model guesses identically.
- **Check:** save and load a fitted model, and predict again.

### On real decks, the baseline agrees with the site (skipped by default)

Run only when `PD_LOCAL_DATA=1`, against the full local dump.

- **Expect:**
  - **The real decks above:** the scores, guesses and best matches in this section.
  - **200 sampled real decks,** each scored against the whole site with the site's own `_playability` weights:
    - the scores, the 20% cut-off and the candidate filter equal `calculate_similar_decks` exactly
    - the ranking agrees except where tied scores are ordered by the site's active date and finish rather than deck id, and the test reports how often that changes the pick
  - **It also reports** how often a Gatherling deck's top site match is unlabelled.
- **Why it matters:** it proves the reimplementation is today's guesser, and it can be re-run whenever we doubt it.
- **Check:** `PD_LOCAL_DATA=1 pytest` on this test.
