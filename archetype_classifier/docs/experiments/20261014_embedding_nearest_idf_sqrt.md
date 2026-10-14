# Run 11: embedding nearest deck v3

| | |
|---|---|
| Run | 11 |
| Made | 2026-10-14 16:51:03 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | 03d608827eeec95c2f25f437043abc7f9fc77a9c |
| Model | 11: embedding nearest deck v3, parameters {"copies": "sqrt", "embedding": "potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39", "weights": "idf"}, seed 0 |
| Snapshot | 1 |
| Scheme | 1 (default) |
| Trained on | train (162878 decks) |
| Tuned on |  (0 decks) |
| Metrics version | 2 |
| Rows version | 3 |
| PRs | #56 |

## Results

| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |
|---|---|---|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.94 [0.94, 0.95] | 0.94 [0.93, 0.94] | 0.95 [0.94, 0.95] | 0.91 | 1.00 | 0.92 (311 archetypes) |  |
| held-out, unseen cards | 230 | 198 | 0.69 [0.63, 0.75] | 0.67 [0.60, 0.73] | 0.71 [0.65, 0.77] | 0.57 | 1.00 | — |  |
| validation | 2249 | 1195 | 0.75 [0.71, 0.79] | 0.76 [0.72, 0.80] | 0.74 [0.70, 0.78] | 0.60 | 1.00 | 0.71 (60 archetypes) |  |
| validation, no unseen cards | 736 | 362 | 0.89 [0.86, 0.92] | 0.91 [0.87, 0.93] | 0.88 [0.84, 0.91] | 0.75 | 1.00 | 0.92 (13 archetypes) |  |
| validation, unseen cards | 1513 | 833 | 0.67 [0.61, 0.73] | 0.68 [0.62, 0.74] | 0.66 [0.59, 0.72] | 0.53 | 1.00 | 0.60 (39 archetypes) |  |
| validation, new maindeck | 2229 | 1182 | 0.75 [0.70, 0.79] | 0.76 [0.72, 0.80] | 0.74 [0.69, 0.78] | 0.60 | 1.00 | 0.71 (60 archetypes) |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — |  |
| validation, existing archetypes | 1966 | 1114 | 0.77 [0.73, 0.81] | 0.77 [0.73, 0.81] | 0.78 [0.74, 0.82] | 0.69 | 1.00 | 0.72 (57 archetypes) |  |
| validation, new archetypes | 283 | 84 | 0.61 [0.44, 0.73] | 0.72 [0.52, 0.86] | 0.52 [0.38, 0.63] | 0.00 | 1.00 | 0.52 (3 archetypes) |  |

## Candidates

| Row | Decks | Maindecks | Top 1 | Top 5 | MRR | Notes |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.91 [0.90, 0.92] | 0.98 [0.97, 0.98] | 0.94 [0.94, 0.94] |  |
| held-out, unseen cards | 230 | 198 | 0.57 [0.49, 0.65] | 0.79 [0.71, 0.85] | 0.67 [0.61, 0.73] |  |
| validation | 2249 | 1195 | 0.60 [0.54, 0.66] | 0.77 [0.72, 0.81] | 0.68 [0.63, 0.72] |  |
| validation, no unseen cards | 736 | 362 | 0.75 [0.66, 0.84] | 0.85 [0.74, 0.93] | 0.80 [0.70, 0.88] |  |
| validation, unseen cards | 1513 | 833 | 0.53 [0.46, 0.60] | 0.73 [0.67, 0.79] | 0.62 [0.56, 0.68] |  |
| validation, new maindeck | 2229 | 1182 | 0.60 [0.54, 0.65] | 0.77 [0.72, 0.81] | 0.68 [0.62, 0.72] |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |  |
| validation, existing archetypes | 1966 | 1114 | 0.69 [0.64, 0.74] | 0.88 [0.85, 0.90] | 0.77 [0.74, 0.81] |  |
| validation, new archetypes | 283 | 84 | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] | 0.02 [0.01, 0.03] |  |

## Validation curve

No validation curve: this model has no threshold to tune.

### Top confusions: held-out

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Izzet Spells | Izzet Tempo | off | 29 | [81523](https://pennydreadfulmagic.com/decks/81523/), [84765](https://pennydreadfulmagic.com/decks/84765/), [86312](https://pennydreadfulmagic.com/decks/86312/) |
| WUBR Jokulhaups Control | Grixis Jokulhaups Control | off | 20 | [193709](https://pennydreadfulmagic.com/decks/193709/), [193740](https://pennydreadfulmagic.com/decks/193740/), [193744](https://pennydreadfulmagic.com/decks/193744/) |
| Rakdos Reanimator | Worldgorger Dragon | off | 13 | [110061](https://pennydreadfulmagic.com/decks/110061/), [144460](https://pennydreadfulmagic.com/decks/144460/), [144505](https://pennydreadfulmagic.com/decks/144505/) |
| Mardu Midrange | Mardu Control | off | 12 | [72811](https://pennydreadfulmagic.com/decks/72811/), [73154](https://pennydreadfulmagic.com/decks/73154/), [74677](https://pennydreadfulmagic.com/decks/74677/) |
| Pox | Fake-Rack | off | 11 | [51311](https://pennydreadfulmagic.com/decks/51311/), [51365](https://pennydreadfulmagic.com/decks/51365/), [148264](https://pennydreadfulmagic.com/decks/148264/) |
| Mono Blue Tempo | Mono Blue Aggro | off | 11 | [117733](https://pennydreadfulmagic.com/decks/117733/), [117917](https://pennydreadfulmagic.com/decks/117917/), [117995](https://pennydreadfulmagic.com/decks/117995/) |
| Gruul Post | Greenpost | off | 10 | [102881](https://pennydreadfulmagic.com/decks/102881/), [110038](https://pennydreadfulmagic.com/decks/110038/), [110109](https://pennydreadfulmagic.com/decks/110109/) |
| Soulflayer | Dimir Reanimator | off | 10 | [189014](https://pennydreadfulmagic.com/decks/189014/), [189060](https://pennydreadfulmagic.com/decks/189060/), [189070](https://pennydreadfulmagic.com/decks/189070/) |
| Dimir Control | Zur's Weirding | off | 9 | [110706](https://pennydreadfulmagic.com/decks/110706/), [110729](https://pennydreadfulmagic.com/decks/110729/), [145903](https://pennydreadfulmagic.com/decks/145903/) |
| Mono Green Stompy | Elves | off | 8 | [100811](https://pennydreadfulmagic.com/decks/100811/), [100836](https://pennydreadfulmagic.com/decks/100836/), [100955](https://pennydreadfulmagic.com/decks/100955/) |

### Top confusions: validation

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Solemnity Aristocrats | Orzhov Aristocrats | on | 98 | [270547](https://pennydreadfulmagic.com/decks/270547/), [270553](https://pennydreadfulmagic.com/decks/270553/), [270592](https://pennydreadfulmagic.com/decks/270592/) |
| Izzet Madcap | Izzet Control | on | 58 | [269653](https://pennydreadfulmagic.com/decks/269653/), [269792](https://pennydreadfulmagic.com/decks/269792/), [269796](https://pennydreadfulmagic.com/decks/269796/) |
| Valakut Ramp | Ramp | on | 28 | [269579](https://pennydreadfulmagic.com/decks/269579/), [269598](https://pennydreadfulmagic.com/decks/269598/), [269626](https://pennydreadfulmagic.com/decks/269626/) |
| Enchantments Matter | Bant Control | off | 27 | [270040](https://pennydreadfulmagic.com/decks/270040/), [270134](https://pennydreadfulmagic.com/decks/270134/), [270139](https://pennydreadfulmagic.com/decks/270139/) |
| Izzet Madcap | Taking Turns | off | 26 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Izzet Twin | Izzet Control | off | 18 | [269650](https://pennydreadfulmagic.com/decks/269650/), [269655](https://pennydreadfulmagic.com/decks/269655/), [270168](https://pennydreadfulmagic.com/decks/270168/) |
| Graveyard Value | Dimir Midrange | off | 16 | [270059](https://pennydreadfulmagic.com/decks/270059/), [270072](https://pennydreadfulmagic.com/decks/270072/), [270074](https://pennydreadfulmagic.com/decks/270074/) |
| Valakut Ramp | Fires of Invention | off | 15 | [269838](https://pennydreadfulmagic.com/decks/269838/), [269931](https://pennydreadfulmagic.com/decks/269931/), [269970](https://pennydreadfulmagic.com/decks/269970/) |
| Applejacks | Gruul Midrange | off | 13 | [269782](https://pennydreadfulmagic.com/decks/269782/), [270161](https://pennydreadfulmagic.com/decks/270161/), [270240](https://pennydreadfulmagic.com/decks/270240/) |
| Izzet Madcap | Curious Niv-Mizzet | off | 13 | [270173](https://pennydreadfulmagic.com/decks/270173/), [270212](https://pennydreadfulmagic.com/decks/270212/), [270213](https://pennydreadfulmagic.com/decks/270213/) |

## Compared with run 8

Run 11 minus run 8, on the decks both runs guessed, with paired intervals.

| Row | Decks compared | Left out | hF | hP | hR | Exact match |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0 | 0.00 [0.00, 0.01] | 0.00 [-0.01, 0.01] | 0.00 [0.00, 0.01] | 0.00 [-0.01, 0.01] |
| held-out, unseen cards | 230 | 0 | -0.06 [-0.11, 0.00] | -0.06 [-0.11, -0.01] | -0.05 [-0.11, 0.01] | -0.07 [-0.15, 0.01] |
| validation | 2249 | 0 | 0.03 [-0.02, 0.07] | 0.03 [-0.01, 0.07] | 0.03 [-0.02, 0.08] | 0.02 [-0.02, 0.08] |
| validation, no unseen cards | 736 | 0 | 0.07 [0.02, 0.15] | 0.07 [0.01, 0.14] | 0.08 [0.02, 0.15] | 0.01 [-0.01, 0.04] |
| validation, unseen cards | 1513 | 0 | 0.00 [-0.06, 0.07] | 0.00 [-0.05, 0.07] | 0.00 [-0.07, 0.08] | 0.03 [-0.03, 0.11] |
| validation, new maindeck | 2229 | 0 | 0.03 [-0.02, 0.08] | 0.03 [-0.02, 0.07] | 0.03 [-0.03, 0.08] | 0.02 [-0.02, 0.09] |
| validation, repeated maindeck | 20 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0 | 0.02 [-0.02, 0.07] | 0.02 [-0.01, 0.06] | 0.02 [-0.02, 0.08] | 0.03 [-0.02, 0.10] |
| validation, new archetypes | 283 | 0 | 0.06 [-0.14, 0.26] | 0.07 [-0.17, 0.30] | 0.05 [-0.12, 0.23] | 0.00 [0.00, 0.00] |

### Candidates compared

| Row | Decks compared | Top 1 | Top 5 | MRR |
|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0.00 [-0.01, 0.01] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| held-out, unseen cards | 230 | -0.07 [-0.15, 0.01] | -0.04 [-0.11, 0.01] | -0.05 [-0.12, 0.00] |
| validation | 2249 | 0.02 [-0.02, 0.08] | -0.01 [-0.02, 0.00] | 0.01 [-0.02, 0.04] |
| validation, no unseen cards | 736 | 0.01 [-0.01, 0.04] | -0.01 [-0.02, 0.00] | 0.01 [-0.01, 0.02] |
| validation, unseen cards | 1513 | 0.03 [-0.03, 0.11] | -0.01 [-0.03, 0.01] | 0.01 [-0.03, 0.05] |
| validation, new maindeck | 2229 | 0.02 [-0.02, 0.09] | -0.01 [-0.02, 0.00] | 0.01 [-0.02, 0.04] |
| validation, repeated maindeck | 20 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0.03 [-0.02, 0.10] | -0.01 [-0.03, 0.00] | 0.01 [-0.02, 0.04] |
| validation, new archetypes | 283 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] |
