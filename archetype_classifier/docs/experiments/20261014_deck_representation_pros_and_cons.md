# Deck representations: pros and cons

*Revised 2026-10-14, evening: added run 13, unseen cards at a typical weight (spec `20261014_Unseen_Card_Weight_Architecture.pdf`, report [20261014_embedding_nearest_idf_sqrt_typical.md](20261014_embedding_nearest_idf_sqrt_typical.md)).*

Ticket #50, PR #56. Runs 10, 11 and 12 in the experiments database, compared with run 8 (the nearest deck, text and numbers) and run 9 (the site's guesser at 20). The full reports are [20261014_bag_nearest_idf_sqrt.md](20261014_bag_nearest_idf_sqrt.md), [20261014_embedding_nearest_idf_sqrt.md](20261014_embedding_nearest_idf_sqrt.md) and [20261014_embedding_nearest_idf_linear.md](20261014_embedding_nearest_idf_linear.md). The design is `20261014_Deck_Representation_Architecture.pdf`, and the results write-up is `20261014_Deck_Representation_Results.pdf`.

## What was tested

Only the representation changed. Each label is still ranked by its best training row's cosine, with the existing tie rules.
- **Card weight:** a legality-aware, smoothed IDF over scheme 1's TRAIN maindecks: `ln((1 + N_c) / (1 + df_c)) + 1`, where N_c counts the training decks in the seasons where the card is legal. A card never legal in a training season weighs 9.36, as an unplayed card from one average season.
- **(a) Bag of cards** (run 10): a sparse vector of √copies × IDF per card, compared by cosine. Two different cards never match.
- **(b) Weighted embedding average** (runs 11 and 12): the sum of copies(n) × IDF × the card's combined embedding row, at unit length. Run 11 uses √copies, run 12 linear copies.

| | |
|---|---|
| Data | snapshot 1, scheme 1 "default"; the same training and scored decks as run 8 |
| Training | 162,878 decks (seasons 1–38) in 84,094 training rows |
| Scored | 17,924 held-out decks and 2,249 season 39 decks. The test seasons weren't used. |
| Embedding | run 8's: text and numbers, `potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39` |
| Headline | Top 1 on season 39's existing archetypes (at least 5 training decks): 1,966 decks, 1,114 maindecks |

## Results

**Season 39, existing archetypes.** Intervals are 95% paired bootstrap intervals over maindecks.

| | Run 8 (control) | Run 9 (site's guesser) | Run 10 (a) bag | Run 11 (b) IDF √ | Run 12 (b) IDF linear |
|---|---|---|---|---|---|
| Top 1 | 0.66 | 0.52 | 0.69 | **0.69** | 0.67 |
| Top 5 | 0.89 | 0.74 | **0.91** | 0.88 | 0.87 |
| MRR | 0.77 | 0.62 | **0.78** | 0.77 | 0.76 |
| Micro hF | 0.75 | 0.59 | 0.77 | **0.78** | 0.76 |
| Top 1 minus run 8 | | | +0.02 [0.00, 0.06] | +0.03 [−0.02, 0.10] | +0.01 [−0.04, 0.08] |
| Top 5 minus run 8 | | | +0.02 [−0.01, 0.04] | −0.01 [−0.03, 0.00] | **−0.02 [−0.03, −0.01]** |
| Top 1 minus run 9 | | | +0.17 [0.12, 0.22] | +0.17 [0.10, 0.24] | +0.15 [0.08, 0.23] |

- **None is a clear step past run 8.** Run 10 and run 11 each gain 2–3 points of Top 1, and both intervals touch or cross 0. The long-term goal is about 90% Top 1 and 99% Top 5.
- **IDF on its own does little to the average:** run 12 minus run 8 is +0.01 Top 1, and it loses 2 points of Top 5.
- **√copies helps the average:** run 11 minus run 12 is +0.02 Top 1 [0.00, 0.04].
- **All three beat the site's guesser** by 15–17 points of Top 1, as run 8 did.

**New archetypes (283 decks).** The bag recovers the rare-card signal the average loses:

| Archetype (training decks) | Decks | Run 8: top 5 · median rank | Run 9 | Run 10 bag | Run 11 | Run 12 |
|---|---|---|---|---|---|---|
| Izzet Madcap (3) | 109 | 0 · 48 | 39 · 6 | **33 · 6** | 0 · 49 | 0 · 49 |
| Solemnity Aristocrats (1) | 112 | 0 · 97 | 3 · 9 | 0 · **7** | 0 · 53 | 0 · 51 |
| Valakut Ramp (0) | 60 | not listed | not listed | not listed | not listed | not listed |

Top 5 on new archetypes is 0.12 for the bag, against 0.00 for runs 8, 11 and 12 and 0.15 for the site's guesser. But the bag's guesses for those decks land further away in the tree: its micro hF there is 0.33, against 0.55 for run 8 and 0.61 for run 11.

**Unseen cards.** The weighted average gets worse as a deck's unseen cards pile up; the bag gets better.

| Unseen maindeck copies (existing archetypes) | Decks | Run 8 Top 1 | Run 10 bag | Run 11 | Run 12 |
|---|---|---|---|---|---|
| 0 | 652 | 0.84 | 0.84 | **0.85** | 0.83 |
| 1–4 | 459 | 0.69 | **0.72** | 0.71 | 0.68 |
| 5–12 | 683 | 0.53 | 0.55 | 0.58 | **0.59** |
| 13+ | 172 | 0.42 | **0.56** | 0.47 | 0.36 |
| Held-out, unseen cards | 230 | 0.64 | **0.69** | 0.57 | 0.64 |

The cause is the never-legal weight. 97% of season 39's unseen copies are cards never legal in a training season, so they weigh 9.36, about twice the median seen card in season 39 (4.58). In decks with 13 or more unseen copies they carry 41% of the deck's weight under run 12 and 39% under run 11, against 27% unweighted. The bag gives unseen cards no column, so they can't steer it.

**Dilution: "the average picked the wrong list"** (#44's measure: a right-label training list shares more copies with the deck than the list the model copied):

| | Run 8 | Run 10 bag | Run 11 | Run 12 |
|---|---|---|---|---|
| Misses on existing archetypes | 665 | 616 | 611 | 648 |
| of which a right-label list shares more copies | 491 | **224** | 518 | 522 |
| Run 8's 491: right at Top 1 | | **178** | 154 | 126 |
| Run 8's 491: in the top 5 | | **407** | 343 | 333 |

Weighting the average doesn't fix dilution: run 11 has as many of these misses as run 8, only on different decks. The bag halves them.

**The models fail on different decks.** Of the 1,966 decks, all three of runs 8, 10 and 11 are right at Top 1 on 1,079 and all wrong on 359. Run 10 alone is right on 134 and run 11 alone on 118. If any of the three were right, Top 1 would be 0.82; if the label is in any of their top fives, 0.96.

**Confusions.** Run 11 fixes Equipment Aggro → Red Deck Wins (66 decks to 2), Simic Flash → Simic Nadu (19 to 2) and Applejacks → Lumbertwin (15 to 1), but adds Enchantments Matter → Bant Control (27), Izzet Twin → Izzet Control (18), Graveyard Value → Dimir Midrange (16) and Applejacks → Gruul Midrange (13). The bag fixes Izzet Tempo → Izzet Control (14 to 2) and Squirrel Aristocrats → Game Objects (10 to 0), and adds Orzhov Midrange → Orzhov Control (17) and Azorius Tempo → Mono Blue Librarians (15).

**Reference decks** (#57). Every guard is candidate 1 under all three new runs. Of the hard cases:

| Deck | Label | Pass if | Run 8 | Run 9 | Run 10 bag | Run 11 | Run 12 |
|---|---|---|---|---|---|---|---|
| 269484 | Blink | 1 | 2 | 4 | 7 | 2 | 2 |
| 269637 | Equipment Aggro | 1 | 2 | 28 | 4 | **1** (group 65 / 66) | **1** (66 / 66) |
| 271375 | Enchantments Matter | 1 | 5 | 9 | 2 | 4 | 8 |
| 269591 | Izzet Madcap | top 5 | 48 | **4** (group 23 / 24) | 6 | 49 | 49 |
| 269653 | Izzet Madcap | top 5 | 34 | 102 | 18 | 64 | 87 |
| 269940 | Midrange | 1 | 2 | 16 | 22 | 3 | 3 |
| 270398 | Orzhov Midrange | 1 | 2 | 13 | 4 | **1** | 2 |

The deck of only newly legal cards (deck −1) gets no guess from the bag, Midrange from run 11 and Field Ramp from run 12.

**Basic lands** (Q9, no special case). The median share of a season 39 deck's weight carried by basic lands falls from 17% (run 8) to 7% (run 12, IDF) and 5% (run 11, IDF and √). IDF alone turns them down enough.

**Run 13: unseen cards at a typical weight** (tuned on season 39). Run 11 with `unseen_weight=typical`: every card no training maindeck plays weighs 4.96 (the median card weight over training maindeck lines) instead of 9.36.

| Top 1, existing archetypes | Decks | Run 8 | Run 11 | Run 13 | Run 13 − run 11 | Unseen share of weight (11 → 13) |
|---|---|---|---|---|---|---|
| all | 1,966 | 0.66 | **0.69** | 0.66 | −0.03 [−0.10, 0.03] | |
| 0 unseen copies | 652 | 0.84 | 0.85 | 0.85 | 0.00 (identical guesses) | 0% |
| 1–4 | 459 | 0.69 | 0.71 | 0.70 | −0.01 [−0.04, 0.02] | 11% → 6% |
| 5–12 | 683 | 0.53 | **0.58** | 0.49 | −0.09 [−0.25, 0.05] | 25% → 15% |
| 13+ | 172 | 0.42 | 0.47 | **0.55** | **+0.08 [0.01, 0.17]** | 39% → 25% |
| Held-out, unseen cards | 230 | 0.64 | 0.57 | 0.59 | +0.02 [−0.01, 0.06] | |

It fixed the 13+ band as predicted, and left decks with no unseen cards exactly as run 11 had them. But it lost the 5–12 band, mostly Equipment Aggro: in season 39 that archetype is built on new cards (Leyline Axe and Raubahn, Bull of Ala Mhigo). At 9.36 they carry 28% of deck 269637's weight and pull it to Equipment Aggro. At 4.96 they carry 17%, and all 67 Equipment Aggro decks go back to Red Deck Wins. Overall run 13 is back at run 8's level. One weight for every unseen card can't separate a new staple from a new archetype-defining card.

## Pros and cons

### (a) Bag of cards, IDF, √copies (run 10)
- ✅ Best Top 5 (0.91) and MRR (0.78), and Top 1 level with run 11.
- ✅ Finds new archetypes by their rare cards: Izzet Madcap in the top 5 for 33 of 109 decks (the site's guesser: 39), where every average gets 0.
- ✅ Robust to unseen cards, which can't change its ranking: best with 13+ unseen copies (0.56 against 0.42) and on held-out decks with unseen cards.
- ✅ Halves the "average picked the wrong list" misses.
- ❌ Can't read rules text: a deck of only new cards gets no guess.
- ❌ On new archetypes its guess lands further away in the tree (hF 0.33 against 0.55), so a parent fallback (#45) earns less from it.
- ❌ Basic lands make the similarity products nearly dense: predicting took about 8 minutes, and it needed a dense-block rewrite to fit in memory.

### (b) Weighted embedding average, IDF, √copies (run 11)
- ✅ Best Top 1 (0.69) and hF (0.78) on existing archetypes; fixes the largest confusion, Equipment Aggro → Red Deck Wins.
- ✅ Still guesses for decks of new cards, through their rules text.
- ❌ Loses Top 5 against run 8 (−0.01).
- ❌ Doesn't fix dilution, and doesn't help new archetypes at all.
- ❌ Over-weights unseen cards: the never-legal weight (9.36) gives them 39% of a deck's weight at 13+ unseen copies, and Top 1 there drops behind the bag by 9 points.

### (b) Weighted embedding average, IDF, linear copies (run 12)
- ❌ Dominated by run 11: lower Top 1, Top 5 and MRR, and the worst run at 13+ unseen copies (0.36).

### (b) Weighted embedding average, IDF, √copies, unseen cards at the typical weight (run 13; tuned on season 39)
- ✅ The best average with 13+ unseen copies (0.55, level with the bag); undoes most of run 11's new confusions.
- ❌ Loses Equipment Aggro again, whose defining cards are new, and falls back to run 8's level overall (0.66).

## What next

- **The unseen-card weight is a knob, not a fix.** Run 13 moved decks between the 5–12 and 13+ bands with no net gain. Keep run 11 as the weighted average to carry forward. Telling new staples from new defining cards needs evidence about each card, such as a new season's labelled decks on a live feed (#17).
- **A hybrid (c) has room to work.** The bag and the average fail on different decks: an oracle choosing among runs 8, 10 and 11 reaches 0.82 Top 1 and 0.96 Top 5. The bag's rare-card ranking and the average's text are complementary.
- **#55, the first look at the test seasons,** needs a choice of model to carry forward: run 8 as the control, and run 10 or run 11 (or both). Run 13 is tuned on season 39 and adds nothing overall.
