# The similarity baseline: pros and cons

Ticket #6, PR #34. Runs 1 and 2 in the experiments database. The full reports are [20261002_similarity_fixed20.md](20261002_similarity_fixed20.md) and [20261002_similarity_tuned.md](20261002_similarity_tuned.md). How the matching is computed is in the note `20261002_Sparse_Deck_Similarity.pdf`.

## What was tested

Today's archetype guesser, reimplemented as the **similarity baseline**:
- **Copying:** a deck copies the label of its most similar training deck.
- **Weights:** shared maindeck lines, same card and quantity, weighted by inverse playability.
- **Threshold:** a match must reach it, or the deck gets no guess.

On 20 sampled real decks, it produced the same scores as the site's own `calculate_similar_decks`.

| | |
|---|---|
| Data | snapshot 1, scheme 2 "similarity baseline" (train {VERIFIED, UNVERIFIED}, eval {VERIFIED}) |
| Training decks | 202,385 (seasons 1–38) |
| Scored | 17,924 held-out decks (seasons 1–38) and 2,249 validation decks (season 39). The test seasons weren't used. |
| Models | **fixed**: the site's threshold, 20 (model 1, run 1). **tuned**: the threshold maximising micro hF on season 39, which is **14** (model 2, run 2). |
| Macro minimum | 10 decks per archetype |

## Results

**Season 39 is the realistic test:** a season the model has never seen, as a new season is in production.

| Season 39 (2,249 decks) | Fixed (20) | Tuned (14) | Tuned minus fixed |
|---|---|---|---|
| Micro hF | 0.52 [0.45, 0.58] | 0.56 [0.50, 0.62] | **+0.04 [0.01, 0.09]** |
| Micro hP | 0.65 | 0.61 | −0.04 |
| Micro hR | 0.43 | 0.52 | +0.09 |
| Exact match | 0.37 | 0.44 | +0.07 |
| Coverage (decks given a guess) | 0.67 | 0.87 | |
| Macro hF (60 archetypes) | 0.52 | 0.57 | |

The tuned model's gain is measured on the season it was tuned on, so it's optimistic. A clean measure needs the test seasons.

**By unseen maindeck copies** (season 39, micro hF, with coverage in brackets):

| Unseen copies | Decks | Fixed (20) | Tuned (14) |
|---|---|---|---|
| 0 | 739 | 0.63 (0.97) | 0.63 (1.00) |
| 1–4 | 556 | 0.45 (0.78) | 0.57 (0.98) |
| 5–12 | 775 | 0.43 (0.39) | 0.46 (0.72) |
| 13+ | 179 | 0.33 (0.23) | 0.55 (0.60) |

**Held-out decks score hF 0.92 with either threshold.** They share seasons, and so a metagame, with the training decks, and 17,776 of 17,924 have no unseen cards. The 148 that do drop to 0.67.

## Pros

- **It is today's guesser.** Its scores, the 20% cut-off and the candidate filter match the site's own function on real decks. So it's a fair bar: anything that beats it beats production.
- **It's fast.** The sparse version scores a deck in about 3 ms, against about 62 s for the site's per-deck loop. A new model can be compared with it in minutes.
- **Every guess cites a deck.** A reviewer can open the matched deck and see why. No other approach we've considered is as easy to check.
- **It's excellent on repeats and familiar decks.**
  - **Repeated maindecks:** all 20 validation decks that repeat a training maindeck score 1.00.
  - **Held-out decks:** they score 0.92, and most decks repeat or closely follow recent lists, since 48% of decks within a season repeat an earlier maindeck.
- **It needs no training** beyond counting playability. It refits in about 15 seconds, so it can follow every new deck.
- **The threshold is a usable certainty knob.** Raising it trades recall for precision along a smooth curve (hP 0.56 → 0.74 as the threshold goes from 1 to 25).

## Cons

- **Unseen cards weigh like the rarest cards.**
  - **The floor:** a card no training deck plays weighs 1,000 (the floor). So does any card with playability below 0.001, which is 79% of legal cards. Each one sits in the deck's own total but can never be shared.
  - **The effect:** a few new cards make a good match look weak. Fixed-threshold coverage falls from 97% of decks with no unseen cards to 23% of decks with 13 or more.
  - **The consequence:** after a rotation, the guesser goes quiet on exactly the decks that need help.
- **One rare shared card can carry a confident wrong guess.** Rarity drives the weight, so a single shared rare line can outweigh the rest of the deck:
  - **Deck 269653,** Izzet Madcap (Control › Izzet Control), matched an Izzet Spells deck (Aggro-Control) at 21%, almost entirely through 4 Make Disappear.
  - **Deck 270398,** Orzhov Midrange, best matched a Mono White Humans deck rather than its closest list by cards.
- **It can't name an archetype that barely existed in training.** It can only copy labels it has seen on similar decks:

  | Season 39 label | Training decks | Season 39 decks | Top confusion (tuned model) |
  |---|---|---|---|
  | Solemnity Aristocrats | 1 | 112 | 83 guessed Orzhov Legends |
  | Izzet Madcap | 3 | 109 | 58 guessed Grixis Control, 27 Cruel Control |

  Equipment Aggro has 417 training decks, but 66 of its 94 season 39 decks got no guess from the tuned model, and 80 from the fixed one: the lists moved on.
- **No parent fallback.** It either copies a label or says nothing. A deck it half-recognises gets the root, never a safe parent such as Control. hF counts that as nothing guessed.
- **A new season is hard even without new cards.** Season 39 decks with no unseen cards reach only hF 0.63, against 0.92 on held-out decks. Metagame drift, not just new cards, separates decks from their old neighbours.
- **The flat curve shows weak matches add little.** Thresholds 1–13 all give hF 0.55. Most decks have either a clear match or none, so tuning mostly decides whether near-misses become guesses.

## What the next model must do

1. **Handle unseen cards by what they do, not by their name.** For example, card-text embeddings (#7) put a new card near similar old ones instead of at the floor.
2. **Fall back to a parent when unsure,** so a half-recognised deck earns partial credit. For example, the tree-aware k-nearest-neighbour vote (#18).
3. **Cope with archetypes that are new or reshaped in the season.** Parent fallback is the first defence. Proposing new archetypes is outside this effort.

## Caveats for every later comparison

- **Use season 39, not the held-out decks.** Held-out decks share their seasons' metagame with the training decks and flatter every model.
- **Tuned numbers on season 39 are optimistic,** because that's where tuning happens. The test seasons are the clean measure, and they're still unused.
- **Intervals resample identical maindecks together,** so they reflect distinct lists, not deck counts.
