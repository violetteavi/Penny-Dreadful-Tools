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

## Decks labelled before their archetype existed

A new archetype usually forms mid-season. Until it exists, a reviewer files its decks under an archetype that already exists. These decks are scored against today's label (the new archetype), but the reviewer's **initial label** shows what a careful person said at the time. A deck counts here if its label today is an archetype first used after season 39 began, and a person had labelled it earlier, before that archetype existed, with an archetype that has training decks. Its initial label is the person's latest label before the new archetype's first use.

**119 scored decks qualify:** 93 in season 39 (46 maindecks) and 26 held-out decks.

| Initial label → today's label (season 39 and held-out) | Decks |
|---|---|
| Izzet Control or Izzet Spells → Izzet Madcap | 56 |
| Ramp, Big Red, Laelia Cascade, Fires of Invention or Dimir Control → Valakut Ramp | 32 |
| Gruul Post, Combo, Combo-Control, Temurpost or Applejacks → Through the Breach | 13 |
| Orzhov Aristocrats → Solemnity Aristocrats | 7 |
| Lifegain Midrange → LifeScam | 5 |
| Red Deck Wins → Flare Deck Wins | 3 |
| Midrange or Boros Aggro → Exile Midrange; Gruul Aggro → Lukka Gruul | 3 |

**Season 39's 93 decks, scored against the initial label instead of today's.** With labels at the cutoff, no model ranks today's label in its top 5 (it has no training decks).

| Against the initial label | Run 14 control | Run 15 site's guesser | Run 16 bag | Run 17 IDF average |
|---|---|---|---|---|
| Top 1 | **0.70** | 0.17 | 0.59 | 0.47 |
| Top 5 | **0.95** | 0.31 | 0.90 | **0.95** |
| MRR | **0.79** | 0.24 | 0.73 | 0.65 |
| Guess is an ancestor of today's label | **62** of 93 | 5 | 49 | 40 |

- **The models mostly agree with the reviewer at the time.** The control names the initial label for 70% of these decks, about its rate on existing archetypes (0.66), and has it in the top 5 for 95%. The site's guesser rarely does: it matches rare cards to decks in other branches.
- **Most guesses are the new archetype's parent.** Izzet Madcap sits under Izzet Control and Valakut Ramp under Ramp, so a guess of the initial label is often the right parent. That's the case for parent fallback (#45): the provisional label can be the parent, while the candidates can't offer an archetype they've never seen.
- **The held-out decks show the leak from the other side.** Their 26 decks come from training seasons and were relabelled into new archetypes later. Trained on today's labels, runs 8–11 name the initial label for only 4–15% of them, because their neighbours carry the new labels. Trained on labels at the cutoff, runs 14–17 name it for 81–96%.

## Where the models fail

Top 1 on season 39's existing archetypes (cutoff counts, 1,956 decks), for the control (run 14), the bag (run 16) and the IDF average (run 17). R = right, – = wrong.

| 14 | 16 | 17 | All 1,956 decks | Without the 71 relabelled after the season |
|---|---|---|---|---|
| R | R | R | 1,072 | 1,070 |
| – | – | – | 360 | 358 |
| – | R | – | **134** (bag only) | **134** |
| – | – | R | **118** (average only) | **53** |
| R | – | R | 104 | 104 |
| R | R | – | 82 | 82 |
| – | R | R | 52 | 51 |
| R | – | – | 34 | 33 |

Choosing the best of the three for each deck (an oracle) would reach 0.82 Top 1 and 0.95 Top 5 on all 1,956 decks, and 0.81 and 0.95 without the relabelled ones.

- **Still true: the bag and the average fail in different places.** They disagree at Top 1 on 438 decks (373 without the relabelled ones). An oracle choosing between the three reaches 0.81 Top 1 without the relabelled decks, against 0.71 for the bag alone. The numbers are almost identical to runs 8, 10 and 11 (#50: 134 bag only, 118 average only, oracle 0.82), so the cutoff doesn't change the case for #60.
- **But the average's own wins are mostly one group.** 65 of its 118 solo wins are the Equipment Aggro decks relabelled after the season. Without them, the bag has 134 solo wins and the average 53. A hybrid should lean on the bag and use the average where it's known to help.
- **Where each one wins alone:**
    - **The bag:** decks with unseen cards (114 of its 134 solo wins have at least one) and archetypes defined by a few signature cards: Izzet Tempo (12), Polymorph (8), Actual Twin (7), Artifact Midrange and Izzet Blitzkrieg (5 each). With 13 or more unseen copies its Top 1 is 0.56, against 0.47 for the average and 0.42 for the control.
    - **The average:** besides Equipment Aggro, midrange decks told apart by plan rather than by signature cards: Dimir Midrange and Orzhov Midrange (7 each) and Golgari Wight (5).
    - **The control alone** wins only 34 decks, so it adds little that the other two lack.

## Decks no model ranks in its top 5

On 93 of the 1,956 decks of existing archetypes (4.8%, 78 maindecks), none of runs 14, 16 and 17 has the label in its top 5. Adding the site's guesser (run 15) rescues only 12.

| | Missed decks | All 1,956 decks |
|---|---|---|
| Labelled with an archetype that has children | 57 (61%) | |
| Labelled with a top-level archetype (Combo, Midrange, Aggro…) | 27 (29%) | 106 (5%) |
| Median unseen maindeck copies | 8 | 4 |
| 13 or more unseen copies | 17 (18%) | 172 (9%) |
| Relabelled after the season | 1 | 71 |
| Repeating a training maindeck | 0 | |

- **Mostly broad parent labels.** Combo (14 of its 37 season 39 decks) and Midrange (9 of 37) lead. These are decks a reviewer couldn't place in a leaf, and their nearest training decks carry specific leaf labels, so the broad label ranks low. Ranking by single nearest decks can't say "this deck is generic": that's parent fallback's job (#45).
- **A few young, fast-changing archetypes.** Kinnan Combo misses 15 of its 18 decks: all 27 of its training decks are from season 38, and its lists changed with season 39's cards. Squirrel Aristocrats (training decks from season 36 on) misses 6 of 17.
- **Not noise and not tiny archetypes.** Only 1 was relabelled after the season, none repeats a training maindeck, and the label's median training count is 210 decks.
- **Often near misses.** The best rank any model gives the label has a median of 10, and 48 of the 93 have it in the top 10. About half the models' first candidates are in another top-level branch.

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
- **Carry the bag (run 16) and the IDF average (run 17) into #60,** leaning on the bag. They tie on Top 1 and fail on different decks, but without the decks relabelled after the season the bag has 134 solo wins to the average's 53.
- **New archetypes need parent fallback,** not candidates: no nearest-deck model can rank one.
