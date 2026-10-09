# The nearest deck on the combined embedding: pros and cons

Ticket #44, PR #48. Runs 5 and 6 in the experiments database, compared with the similarity baseline's run 4 (#6, re-run under the cards database's legality in #46). The full reports are [20261008_embedding_nearest_text_and_numbers.md](20261008_embedding_nearest_text_and_numbers.md) and [20261008_embedding_nearest_text_only.md](20261008_embedding_nearest_text_only.md). The design is `20261008_Nearest_Deck_Architecture.pdf`.

## What was tested

The baseline's rule, "copy the label of the best match", with each deck read through the combined embedding (#41) instead of its shared cards:
- **Deck vector:** the copy-weighted average of the maindeck cards' combined rows, at unit length. Basic lands count; the sideboard doesn't.
- **Training rows:** one per distinct maindeck and label, so a list submitted many times counts once.
- **Picking:** the training row with the highest cosine similarity. A tie goes to the label with more decks, then to the newest deck.
- **No tree, no threshold:** every deck gets a guess, and nothing is tuned on season 39.

| | |
|---|---|
| Data | snapshot 1, scheme 1 "default" (train {VERIFIED}, eval {VERIFIED}) |
| Training | 162,878 decks (seasons 1–38) in 84,094 training rows; fitting takes 5 s |
| Scored | 17,924 held-out decks (seasons 1–38) and 2,249 validation decks (season 39). The test seasons weren't used. |
| Runs | **text and numbers:** potion on masked text plus the card numbers, average thirds, weights 3/1/1/1 (model 5, run 5). **text only:** weights 1/0/0/0 (model 6, run 6). |
| Embedding | fit seasons 1–38, embedded seasons 1–39, 23,862 cards. No maindeck card in any scored or training deck is missing. |
| Baseline | run 4: the similarity baseline, threshold tuned to 14 on season 39 |
| Macro minimum | 10 decks per archetype |

## Results

**Expected to lose to the baseline; it doesn't.** On season 39 both embeddings beat it clearly, and the baseline was even tuned on that season.

| Season 39 (2,249 decks) | Baseline (tuned) | Text and numbers | Text only |
|---|---|---|---|
| Micro hF | 0.56 [0.50, 0.62] | 0.72 [0.68, 0.77] | **0.75 [0.71, 0.79]** |
| Minus the baseline, paired | | **+0.16 [0.11, 0.21]** | |
| Text only minus text and numbers, paired | | | +0.02 [0.00, 0.06] |
| Exact match | 0.44 | 0.58 | 0.58 |
| Coverage | 0.87 | 1.00 | 1.00 |
| Macro hF (60 archetypes) | 0.57 | 0.71 | 0.69 |

**It's not just from always guessing.** On the 1,958 season 39 decks the baseline does guess, it scores 0.60, against 0.75 (text and numbers) and 0.78 (text only). On the 291 decks the baseline leaves without a guess, the embedding scores 0.54 and 0.49.

**By unseen maindeck copies** (season 39 unless it says held-out; micro hF, with the baseline's coverage in brackets):

| Rows | Decks | Baseline | Text and numbers | Text only |
|---|---|---|---|---|
| No unseen cards | 736 | 0.64 (1.00) | 0.82 | **0.87** |
| 1–3 unseen copies | 248 | 0.55 (0.99) | 0.77 | **0.85** |
| 4–5 | 361 | 0.61 (0.97) | **0.74** | 0.72 |
| 6–8 | 498 | 0.42 (0.71) | 0.63 | **0.66** |
| 9–12 | 225 | 0.49 (0.72) | **0.58** | 0.52 |
| 13+ | 181 | 0.55 (0.61) | 0.57 | 0.57 |
| Any unseen card | 1,513 | 0.52 (0.81) | 0.67 | 0.68 |
| Held-out, no unseen cards | 17,694 | 0.92 (1.00) | 0.94 | 0.94 |
| Held-out, unseen cards | 230 | 0.69 (0.94) | **0.75** | 0.71 |

The gain shrinks as unseen cards pile up. At 13+ unseen copies the three are level, although the baseline only guesses for 61% of those decks.

**Matches come from recent seasons.** The best training row is most often from season 38 (595 decks for text and numbers, 714 for text only), then 37. The best match is close for nearly every deck: the median similarity is 0.98, and the 10th percentile is 0.97.

**The new archetype, Valakut Ramp** (60 decks; it has no training decks, and its parent is Ramp):

| | Most common guesses |
|---|---|
| Baseline | no guess 16, Last Stand Control 11, Ramp 10, Greenpost 4 |
| Text and numbers | Summer Bloom Ramp 27, Ramp 11, Fires of Invention 7, Gruul Midrange 5 |
| Text only | **Ramp 39**, Fires of Invention 10, Field Ramp 3, Control 2 |

Text only lands most of them on their parent, Ramp. Decks labelled Ramp itself exist in training, so the nearest deck finds a parent fallback without being designed for one.

**Top confusions on season 39:**
- **Text and numbers:** Izzet Madcap → Izzet Control 98 (its parent), Equipment Aggro → Red Deck Wins 66 (another branch), Solemnity Aristocrats → Orzhov Aristocrats 62 (its parent).
- **Text only:** Solemnity Aristocrats → Orzhov Aristocrats 109, Izzet Madcap → Izzet Control 106, Equipment Aggro → Red Deck Wins 67, Valakut Ramp → Ramp 39.

## Pros

- **Beats today's guesser on the season that matters,** by 0.16–0.19 micro hF on season 39, untuned against a tuned baseline. It still wins on decks the baseline is confident about.
- **Never silent:** every deck gets a guess. The baseline leaves 13% of season 39 decks, and 39% of the decks with 13+ unseen copies, with none.
- **Unseen cards still mean something:** an unseen card has a vector from its text, so it moves a deck towards decks with similar cards. In the baseline it only adds weight that can never be matched.
- **Many of its mistakes are parents:** Izzet Madcap → Izzet Control and Solemnity Aristocrats → Orzhov Aristocrats are guesses one level up, which score partial credit.
- **Cheap:** fitting takes 5 s and predicting 20,173 decks takes 30–45 s on CPU (the baseline: 157 s), with no training. A new set needs only its cards embedded.
- **Traceable:** each guess names the training deck it copied, its similarity and the runner-up label.

## Cons

- **The card numbers don't help at deck level, overall:** text only is ahead by +0.02 [0.00, 0.06] on season 39. The numbers help on decks with many unseen cards (9–12 copies, held-out decks with unseen cards) and hurt on decks with few. That's a question for #36, which can now be asked at deck level.
- **No parent fallback by design:** it always copies one label, however far the nearest deck is. Valakut Ramp landing on Ramp is luck of the data: Ramp-labelled decks exist. #45 adds the real fallback.
- **The average blurs what's distinctive:** similarities are compressed into a narrow band (median 0.98), so the margin between the right and wrong archetype is often small. Basic lands are part of the average, which pulls decks of one colour together.
- **Popularity is only a tie-break:** a single odd list can win over a well-represented archetype that's slightly further away.
- **The gain fades with many unseen cards:** level with the baseline at 13+ unseen copies.

## What the next model should try

- **Parent fallback (#45):** turn the margin between the best rows' labels into a confidence, and climb the tree when it's small.
- **A better deck representation:** bag-of-words over cards, or a weighting that lets rare, distinctive cards count for more than basics and staples, as the baseline's playability weights do.
- **k nearest rows (#18):** vote among several near rows rather than copying one.
- **#36:** settle the card numbers' weight by deck-level results by unseen copies, now that a deck-level measure exists.

## Caveats

- **The baseline was tuned on season 39 and this model wasn't.** That favours the baseline, so the gap is if anything understated.
- **Season 39 is one season** of 2,249 decks; the intervals are wide. The test seasons (40–42) need an embedding of seasons up to 42 and are looked at rarely.
- **The two runs used different schemes:** the baseline trains on {VERIFIED, UNVERIFIED} (scheme 2), this model on {VERIFIED} (scheme 1). Both score exactly the same decks. Unseen copies are counted against each scheme's own training decks, so the rows by unseen copies above use scheme 1's counts for all three.
