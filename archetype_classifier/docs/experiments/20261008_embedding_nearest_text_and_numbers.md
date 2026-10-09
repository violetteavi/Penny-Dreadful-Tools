# Run 5: embedding nearest deck v1

| | |
|---|---|
| Run | 5 |
| Made | 2026-10-08 16:30:53 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | c17521a19578881fc7ee396e6c5ae78f487e3e44 |
| Model | 5: embedding nearest deck v1, parameters {"embedding": "potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39"}, seed 0 |
| Snapshot | 1 |
| Scheme | 1 (default) |
| Trained on | train (162878 decks) |
| Tuned on |  (0 decks) |
| Metrics version | 1 |
| Rows version | 2 |
| PRs | #48 |

## Results

| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |
|---|---|---|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.94 [0.93, 0.95] | 0.94 [0.93, 0.95] | 0.94 [0.94, 0.95] | 0.91 | 1.00 | 0.92 (311 archetypes) |  |
| held-out, unseen cards | 230 | 198 | 0.75 [0.68, 0.81] | 0.73 [0.67, 0.79] | 0.76 [0.70, 0.83] | 0.64 | 1.00 | — |  |
| validation | 2249 | 1195 | 0.72 [0.68, 0.77] | 0.74 [0.69, 0.78] | 0.71 [0.66, 0.76] | 0.58 | 1.00 | 0.71 (60 archetypes) |  |
| validation, no unseen cards | 736 | 362 | 0.82 [0.73, 0.89] | 0.84 [0.76, 0.90] | 0.80 [0.71, 0.88] | 0.74 | 1.00 | 0.86 (13 archetypes) |  |
| validation, unseen cards | 1513 | 833 | 0.67 [0.62, 0.72] | 0.68 [0.63, 0.73] | 0.66 [0.61, 0.71] | 0.50 | 1.00 | 0.62 (39 archetypes) |  |
| validation, new maindeck | 2229 | 1182 | 0.72 [0.68, 0.77] | 0.73 [0.69, 0.78] | 0.71 [0.66, 0.76] | 0.58 | 1.00 | 0.71 (60 archetypes) |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — |  |

## Validation curve

No validation curve: this model has no threshold to tune.

### Top confusions: held-out

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Jund | Jund Jokulhaups Control | off | 48 | [178161](https://pennydreadfulmagic.com/decks/178161/), [186682](https://pennydreadfulmagic.com/decks/186682/), [186737](https://pennydreadfulmagic.com/decks/186737/) |
| Anvil Colossus | Metalwork Colossus | on | 36 | [251405](https://pennydreadfulmagic.com/decks/251405/), [251416](https://pennydreadfulmagic.com/decks/251416/), [251488](https://pennydreadfulmagic.com/decks/251488/) |
| WUBR Jokulhaups Control | Grixis Jokulhaups Control | off | 20 | [193709](https://pennydreadfulmagic.com/decks/193709/), [193740](https://pennydreadfulmagic.com/decks/193740/), [193744](https://pennydreadfulmagic.com/decks/193744/) |
| Rakdos Reanimator | Worldgorger Dragon | off | 13 | [110061](https://pennydreadfulmagic.com/decks/110061/), [144460](https://pennydreadfulmagic.com/decks/144460/), [144505](https://pennydreadfulmagic.com/decks/144505/) |
| Midrange | Ramp | off | 11 | [100033](https://pennydreadfulmagic.com/decks/100033/), [148904](https://pennydreadfulmagic.com/decks/148904/), [172841](https://pennydreadfulmagic.com/decks/172841/) |
| Gruul Post | Greenpost | off | 11 | [102881](https://pennydreadfulmagic.com/decks/102881/), [110038](https://pennydreadfulmagic.com/decks/110038/), [110109](https://pennydreadfulmagic.com/decks/110109/) |
| Dimir Control | Zur's Weirding | off | 11 | [110706](https://pennydreadfulmagic.com/decks/110706/), [110729](https://pennydreadfulmagic.com/decks/110729/), [114673](https://pennydreadfulmagic.com/decks/114673/) |
| Mono Blue Tempo | Mono Blue Aggro | off | 11 | [117733](https://pennydreadfulmagic.com/decks/117733/), [117917](https://pennydreadfulmagic.com/decks/117917/), [117995](https://pennydreadfulmagic.com/decks/117995/) |
| Soulflayer | Dimir Reanimator | off | 10 | [189014](https://pennydreadfulmagic.com/decks/189014/), [189060](https://pennydreadfulmagic.com/decks/189060/), [189070](https://pennydreadfulmagic.com/decks/189070/) |
| Izzet Spells | Izzet Tempo | off | 9 | [84765](https://pennydreadfulmagic.com/decks/84765/), [86312](https://pennydreadfulmagic.com/decks/86312/), [86525](https://pennydreadfulmagic.com/decks/86525/) |

### Top confusions: validation

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Izzet Madcap | Izzet Control | on | 98 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Equipment Aggro | Red Deck Wins | off | 66 | [269637](https://pennydreadfulmagic.com/decks/269637/), [269689](https://pennydreadfulmagic.com/decks/269689/), [269705](https://pennydreadfulmagic.com/decks/269705/) |
| Solemnity Aristocrats | Orzhov Aristocrats | on | 62 | [270547](https://pennydreadfulmagic.com/decks/270547/), [270553](https://pennydreadfulmagic.com/decks/270553/), [270592](https://pennydreadfulmagic.com/decks/270592/) |
| Enchantments Matter | Enchantress | off | 32 | [269995](https://pennydreadfulmagic.com/decks/269995/), [270040](https://pennydreadfulmagic.com/decks/270040/), [270079](https://pennydreadfulmagic.com/decks/270079/) |
| Solemnity Aristocrats | Orzhov Vampires | off | 29 | [270739](https://pennydreadfulmagic.com/decks/270739/), [271235](https://pennydreadfulmagic.com/decks/271235/), [271324](https://pennydreadfulmagic.com/decks/271324/) |
| Valakut Ramp | Summer Bloom Ramp | off | 27 | [269838](https://pennydreadfulmagic.com/decks/269838/), [269931](https://pennydreadfulmagic.com/decks/269931/), [269949](https://pennydreadfulmagic.com/decks/269949/) |
| Solemnity Aristocrats | Orzhov Midrange | off | 21 | [270794](https://pennydreadfulmagic.com/decks/270794/), [271049](https://pennydreadfulmagic.com/decks/271049/), [271373](https://pennydreadfulmagic.com/decks/271373/) |
| Simic Flash | Simic Nadu | off | 19 | [269602](https://pennydreadfulmagic.com/decks/269602/), [269638](https://pennydreadfulmagic.com/decks/269638/), [269646](https://pennydreadfulmagic.com/decks/269646/) |
| Applejacks | Lumbertwin | off | 15 | [269782](https://pennydreadfulmagic.com/decks/269782/), [270161](https://pennydreadfulmagic.com/decks/270161/), [270240](https://pennydreadfulmagic.com/decks/270240/) |
| Izzet Tempo | Izzet Control | off | 14 | [271613](https://pennydreadfulmagic.com/decks/271613/), [271640](https://pennydreadfulmagic.com/decks/271640/), [271643](https://pennydreadfulmagic.com/decks/271643/) |

## Compared with run 4

Run 5 minus run 4, on the decks both runs guessed, with paired intervals.

| Row | Decks compared | Left out | hF | hP | hR | Exact match |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0 | 0.02 [0.01, 0.02] | 0.01 [0.00, 0.02] | 0.02 [0.01, 0.02] | 0.03 [0.02, 0.03] |
| held-out, unseen cards | 230 | 0 | 0.06 [0.01, 0.11] | 0.03 [-0.03, 0.08] | 0.09 [0.03, 0.14] | 0.09 [0.03, 0.15] |
| validation | 2249 | 0 | 0.16 [0.11, 0.21] | 0.13 [0.07, 0.18] | 0.19 [0.15, 0.24] | 0.14 [0.10, 0.19] |
| validation, no unseen cards | 736 | 0 | 0.18 [0.08, 0.29] | 0.19 [0.09, 0.30] | 0.18 [0.08, 0.28] | 0.18 [0.09, 0.29] |
| validation, unseen cards | 1513 | 0 | 0.15 [0.11, 0.20] | 0.10 [0.04, 0.15] | 0.20 [0.15, 0.24] | 0.12 [0.07, 0.16] |
| validation, new maindeck | 2229 | 0 | 0.16 [0.11, 0.22] | 0.13 [0.07, 0.19] | 0.19 [0.15, 0.24] | 0.14 [0.10, 0.19] |
| validation, repeated maindeck | 20 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
