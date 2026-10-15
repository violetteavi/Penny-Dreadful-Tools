# Run 13: embedding nearest deck v4

| | |
|---|---|
| Run | 13 |
| Made | 2026-10-14 18:03:59 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | 6b815583f18fb6a6847b122a53b37ba655e06eea |
| Model | 13: embedding nearest deck v4, parameters {"copies": "sqrt", "embedding": "potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39", "unseen_weight": "typical", "weights": "idf"}, seed 0 |
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
| held-out, unseen cards | 230 | 198 | 0.71 [0.65, 0.77] | 0.69 [0.63, 0.75] | 0.73 [0.68, 0.79] | 0.59 | 1.00 | — |  |
| validation | 2249 | 1195 | 0.73 [0.68, 0.77] | 0.74 [0.70, 0.78] | 0.72 [0.67, 0.77] | 0.58 | 1.00 | 0.70 (60 archetypes) |  |
| validation, no unseen cards | 736 | 362 | 0.89 [0.86, 0.92] | 0.91 [0.87, 0.93] | 0.88 [0.84, 0.91] | 0.75 | 1.00 | 0.92 (13 archetypes) |  |
| validation, unseen cards | 1513 | 833 | 0.64 [0.58, 0.69] | 0.65 [0.59, 0.70] | 0.63 [0.57, 0.69] | 0.50 | 1.00 | 0.59 (39 archetypes) |  |
| validation, new maindeck | 2229 | 1182 | 0.73 [0.68, 0.77] | 0.74 [0.69, 0.78] | 0.72 [0.67, 0.76] | 0.58 | 1.00 | 0.70 (60 archetypes) |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — |  |
| validation, existing archetypes | 1966 | 1114 | 0.76 [0.70, 0.80] | 0.75 [0.70, 0.79] | 0.76 [0.71, 0.81] | 0.66 | 1.00 | 0.71 (57 archetypes) |  |
| validation, new archetypes | 283 | 84 | 0.58 [0.41, 0.71] | 0.68 [0.48, 0.82] | 0.51 [0.36, 0.62] | 0.00 | 1.00 | 0.47 (3 archetypes) |  |

## Candidates

| Row | Decks | Maindecks | Top 1 | Top 5 | MRR | Notes |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.91 [0.90, 0.92] | 0.98 [0.97, 0.98] | 0.94 [0.94, 0.94] |  |
| held-out, unseen cards | 230 | 198 | 0.59 [0.51, 0.66] | 0.80 [0.73, 0.87] | 0.69 [0.62, 0.74] |  |
| validation | 2249 | 1195 | 0.58 [0.51, 0.64] | 0.78 [0.73, 0.82] | 0.67 [0.61, 0.72] |  |
| validation, no unseen cards | 736 | 362 | 0.75 [0.66, 0.84] | 0.85 [0.74, 0.93] | 0.80 [0.70, 0.88] |  |
| validation, unseen cards | 1513 | 833 | 0.50 [0.42, 0.56] | 0.74 [0.68, 0.79] | 0.60 [0.54, 0.66] |  |
| validation, new maindeck | 2229 | 1182 | 0.58 [0.51, 0.64] | 0.77 [0.72, 0.82] | 0.66 [0.61, 0.72] |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |  |
| validation, existing archetypes | 1966 | 1114 | 0.66 [0.60, 0.72] | 0.89 [0.86, 0.91] | 0.76 [0.71, 0.80] |  |
| validation, new archetypes | 283 | 84 | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] | 0.02 [0.02, 0.03] |  |

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
| Equipment Aggro | Red Deck Wins | off | 67 | [269637](https://pennydreadfulmagic.com/decks/269637/), [269689](https://pennydreadfulmagic.com/decks/269689/), [269705](https://pennydreadfulmagic.com/decks/269705/) |
| Izzet Madcap | Izzet Control | on | 61 | [269653](https://pennydreadfulmagic.com/decks/269653/), [269792](https://pennydreadfulmagic.com/decks/269792/), [269796](https://pennydreadfulmagic.com/decks/269796/) |
| Izzet Madcap | Polymorph | off | 46 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Valakut Ramp | Fires of Invention | off | 35 | [269526](https://pennydreadfulmagic.com/decks/269526/), [269704](https://pennydreadfulmagic.com/decks/269704/), [269838](https://pennydreadfulmagic.com/decks/269838/) |
| Enchantments Matter | Enchantress | off | 32 | [269927](https://pennydreadfulmagic.com/decks/269927/), [269995](https://pennydreadfulmagic.com/decks/269995/), [270040](https://pennydreadfulmagic.com/decks/270040/) |
| Mono Blue Control | Mono Blue Tempo | off | 21 | [269903](https://pennydreadfulmagic.com/decks/269903/), [271082](https://pennydreadfulmagic.com/decks/271082/), [271084](https://pennydreadfulmagic.com/decks/271084/) |
| Applejacks | Lumbertwin | off | 14 | [269782](https://pennydreadfulmagic.com/decks/269782/), [270161](https://pennydreadfulmagic.com/decks/270161/), [270240](https://pennydreadfulmagic.com/decks/270240/) |
| Polymorph | Azorius Control | off | 13 | [270508](https://pennydreadfulmagic.com/decks/270508/), [270581](https://pennydreadfulmagic.com/decks/270581/), [270684](https://pennydreadfulmagic.com/decks/270684/) |
| Izzet Tempo | Izzet Control | off | 13 | [271613](https://pennydreadfulmagic.com/decks/271613/), [271640](https://pennydreadfulmagic.com/decks/271640/), [271643](https://pennydreadfulmagic.com/decks/271643/) |

## Compared with run 11

Run 13 minus run 11, on the decks both runs guessed, with paired intervals.

| Row | Decks compared | Left out | hF | hP | hR | Exact match |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| held-out, unseen cards | 230 | 0 | 0.02 [-0.01, 0.05] | 0.02 [-0.01, 0.05] | 0.02 [-0.01, 0.05] | 0.02 [-0.01, 0.06] |
| validation | 2249 | 0 | -0.02 [-0.06, 0.01] | -0.02 [-0.06, 0.01] | -0.02 [-0.07, 0.02] | -0.02 [-0.08, 0.02] |
| validation, no unseen cards | 736 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, unseen cards | 1513 | 0 | -0.03 [-0.10, 0.02] | -0.03 [-0.09, 0.01] | -0.03 [-0.11, 0.03] | -0.03 [-0.12, 0.03] |
| validation, new maindeck | 2229 | 0 | -0.02 [-0.07, 0.01] | -0.02 [-0.06, 0.01] | -0.02 [-0.07, 0.02] | -0.02 [-0.08, 0.02] |
| validation, repeated maindeck | 20 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0 | -0.02 [-0.07, 0.02] | -0.02 [-0.06, 0.01] | -0.02 [-0.09, 0.02] | -0.02 [-0.10, 0.03] |
| validation, new archetypes | 283 | 0 | -0.02 [-0.06, 0.00] | -0.04 [-0.10, 0.00] | -0.01 [-0.04, 0.00] | 0.00 [0.00, 0.00] |

### Candidates compared

| Row | Decks compared | Top 1 | Top 5 | MRR |
|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| held-out, unseen cards | 230 | 0.02 [-0.01, 0.06] | 0.01 [0.00, 0.03] | 0.01 [-0.01, 0.03] |
| validation | 2249 | -0.02 [-0.08, 0.02] | 0.01 [-0.01, 0.02] | -0.01 [-0.05, 0.02] |
| validation, no unseen cards | 736 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, unseen cards | 1513 | -0.03 [-0.12, 0.03] | 0.01 [-0.01, 0.03] | -0.02 [-0.08, 0.03] |
| validation, new maindeck | 2229 | -0.02 [-0.08, 0.02] | 0.01 [-0.01, 0.02] | -0.01 [-0.06, 0.02] |
| validation, repeated maindeck | 20 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | -0.02 [-0.10, 0.03] | 0.01 [-0.01, 0.02] | -0.01 [-0.07, 0.02] |
| validation, new archetypes | 283 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
