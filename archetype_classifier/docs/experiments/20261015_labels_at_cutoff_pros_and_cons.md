# Labels at a cutoff: pros and cons

Ticket #59, PR #61. Runs 14–17 re-run runs 8–11 with training labels as they stood when season 39 began. The full reports are [20261015_embedding_nearest_cutoff_text_and_numbers.md](20261015_embedding_nearest_cutoff_text_and_numbers.md) (run 14), [20261015_cutoff_similarity_fixed20.md](20261015_cutoff_similarity_fixed20.md) (run 15), [20261015_bag_nearest_cutoff_sqrt.md](20261015_bag_nearest_cutoff_sqrt.md) (run 16) and [20261015_embedding_nearest_cutoff_idf_sqrt.md](20261015_embedding_nearest_cutoff_idf_sqrt.md) (run 17). The design is `20261015_Labels_At_Cutoff_Architecture.pdf`, and the results write-up is `20261015_Labels_At_Cutoff_Results.pdf`.

## What was tested

Only the training labels changed. Snapshot 1 now holds every deck's label history (466,235 entries). Two new schemes copy schemes 1 and 2 and add a **label cutoff** at season 39's start (2025-10-03 07:00 UTC). A training deck with a label decision after the cutoff trains on its label as it stood then: a person's label if there was one, else an automatic one. Every scored deck keeps today's label.

| | |
|---|---|
| Data | snapshot 1; scheme 3 "default, labels at season 39" (runs 14, 16, 17) and scheme 4 "similarity baseline, labels at season 39" (run 15) |
| Labels changed | 222 training-season decks decided after the cutoff: 203 with a different label then, 8 with the same label, 9 with no label then (left out of training), 2 out of scope either way (Tapped Out decks) |
| Training | 162,869 decks (162,878 before); scheme 4: 202,376 (202,385 before) |
| Scored | the same 17,924 held-out and 2,249 season 39 decks, with the same labels as runs 8–11 (checked) |
| Pairs | run 8 → 14 (nearest deck, the control), 9 → 15 (the site's guesser at 20), 10 → 16 (bag of cards), 11 → 17 (IDF-weighted average) |

**Existing and new archetypes are now counted from the cutoff labels.** Ten season 39 decks move from "existing" to "new": 9 LifeScam decks (all LifeScam's training labels came from the Lifegain Midrange → LifeScam relabel after the cutoff) and 1 Flare Deck Wins deck. Season 39 has 1,956 decks of existing archetypes (1,966 before) and 293 of new ones (283 before). Izzet Madcap (109 decks) and Solemnity Aristocrats (112) were already new; with the cutoff they have no training decks at all. Through the Breach has no season 39 decks.

## Results

**Each model against itself.** Only 12–17 of the 2,249 season 39 guesses change per model. Differences are the re-run minus the original, with 95% paired bootstrap intervals over maindecks.

| Season 39 | Run 8 → 14 | Run 9 → 15 | Run 10 → 16 | Run 11 → 17 |
|---|---|---|---|---|
| Existing archetypes (1,956), Top 1 | 0.660 → 0.661 | 0.516 → 0.519 | 0.685 → 0.685 | 0.688 → 0.688 |
| Existing archetypes, Top 5 | 0.891 → 0.890 | 0.740 → 0.736 | 0.909 → 0.906 | 0.879 → 0.879 |
| New archetypes (293), Top 5 | 0.038 → **0** | 0.181 → **0** | 0.150 → **0** | 0.038 → **0** |
| Izzet Madcap in the top 5 (of 109) | 0 → 0 | 39 → **0** | 33 → **0** | 0 → 0 |
| All season 39, Top 5 minus the original | −0.006 [−0.010, −0.002] | **−0.027 [−0.051, −0.011]** | **−0.022 [−0.048, −0.007]** | −0.005 [−0.009, −0.001] |

- **Existing archetypes don't move.** Every Top 1, Top 5 and MRR difference there is within ±0.004. The leak didn't flatter any model on archetypes that existed when season 39 began.
- **All the success on new archetypes was the leak.** With labels as they stood, no model ranks a new archetype anywhere in its top 5. The site's guesser and the bag found Izzet Madcap through its rare cards, but only by matching the 3 training decks relabelled Izzet Madcap after the season started. A candidate list can't offer an archetype it has never seen labelled. That's a job for parent fallback (#45) and, later, proposing new archetypes.
- **The models that looked good on new archetypes lose the most overall:** the site's guesser −0.027 Top 5 and the bag −0.022. Both come from new archetypes alone.

**The models against each other, with labels at the cutoff.**

| Season 39, existing archetypes | Run 14 control | Run 15 site's guesser | Run 16 bag | Run 17 IDF average |
|---|---|---|---|---|
| Top 1 | 0.661 | 0.519 | 0.685 | **0.688** |
| Top 5 | 0.890 | 0.736 | **0.906** | 0.879 |
| MRR | 0.764 | 0.620 | **0.780** | 0.771 |
| Micro hF | 0.754 | 0.582 | 0.773 | **0.774** |
| Top 1 minus run 14 | | | +0.025 [−0.006, 0.056] | +0.028 [−0.020, 0.094] |
| MRR minus run 14, without the 71 relabelled decks | | | **+0.026 [0.004, 0.047]** | −0.010 [−0.024, 0.003] |
| Top 1 minus run 15 | | | **+0.166 [0.119, 0.222]** | |

- **The bag's lead over the control holds,** with the same size as before (+0.025 Top 1). Without the decks relabelled after the season, its MRR gain is clear of 0.
- **Every model beats the site's guesser** by 14–17 points of Top 1, as before.

## Decks relabelled after the season (the new row)

80 season 39 decks were relabelled by a person after the season ended (rows v4's "label changed after its season"): 69 moved from Red Deck Wins (or Mono Red Swarm) to Equipment Aggro, 65 of them on 2026-04-08.

| Top 1 on those 80 decks | Original | With the cutoff |
|---|---|---|
| Nearest deck (8 → 14) | 0.06 | 0.04 |
| Site's guesser (9 → 15) | 0.01 | 0.00 |
| Bag (10 → 16) | 0.06 | 0.04 |
| IDF average (11 → 17) | **0.88** | **0.85** |

- **This changes a #50 conclusion.** The #50 write-up set those decks aside, suspecting that run 11's lead rested on labels given later. With training labels as they stood when season 39 began, the IDF average still names Equipment Aggro for 85% of them. Its lead there doesn't come from training on later labels: it agrees with the reviewer's later decision, using only what was known at the time. Scored against today's labels (the decision on #59), that lead is real.
- So on existing archetypes the bag and the IDF average are tied on Top 1 (0.685 against 0.688). The bag is ahead on Top 5 and MRR, and the average is ahead on these 80 decks. That supports the hybrid in #60.

## Time taken

Fit and prediction time, as stored with each model and run (predicting covers all 20,173 held-out and season 39 decks).

| Model | Original: fit / predict | With the cutoff: fit / predict |
|---|---|---|
| Nearest deck (8 → 14) | 3 s / 58 s | 5 s / 163 s |
| Site's guesser at 20 (9 → 15) | 15 s / 390 s | 22 s / 577 s |
| Bag of cards (10 → 16) | 8 s / 491 s | 6 s / 330 s |
| IDF average (11 → 17) | 6 s / 88 s | 8 s / 69 s |

## Pros and cons of training on labels at the cutoff

**Pros**

- **Honest about new archetypes.** Today's labels made the site's guesser and the bag look able to rank new archetypes; they can't. Measuring parent fallback (#45) and the hybrid (#60) against labels as they stood keeps that from repeating.
- **Costs nothing on existing archetypes.** The 203 changed training labels move no headline number.
- **Cheap to keep.** The history is in the snapshot, so any later scheme can take its own cutoff, and #17's live replay can build on it.

**Cons**

- **One cutoff per scheme.** Decks submitted late in season 39 were judged against labels a model trained at the start of the season couldn't have had, but a model retrained during the season could. #17 covers that.
- **Curator moves without history** keep today's label, since nothing records when they happened. None of the 220 training decks decided after the cutoff is one of them: each one's site label is its latest history entry.

## Recommendations

- **Use the cutoff schemes (3 and 4) from now on** for season 39 work, including #60 (Hybrid deck representation: combine the bag of cards with the embedding average) and #45 (Parent fallback on a deck classifier's archetype probabilities). For #55 (First official look at the test seasons (40–42)), make a scheme with the cutoff at season 40's start.
- **Carry the bag (run 16) and the IDF average (run 17) into #60** as equals: they tie on Top 1 and fail on different decks.
- **New archetypes need parent fallback,** not candidates: no nearest-deck model can rank one.
