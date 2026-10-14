# Run 12: embedding nearest deck v3

| | |
|---|---|
| Run | 12 |
| Made | 2026-10-14 16:55:23 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | d935e59cb189cc52a65c2aaabed8bbce562da31e |
| Model | 12: embedding nearest deck v3, parameters {"copies": "linear", "embedding": "potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39", "weights": "idf"}, seed 0 |
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
| held-out, no unseen cards | 17694 | 9210 | 0.94 [0.94, 0.95] | 0.94 [0.94, 0.95] | 0.95 [0.94, 0.95] | 0.91 | 1.00 | 0.92 (311 archetypes) |  |
| held-out, unseen cards | 230 | 198 | 0.75 [0.69, 0.81] | 0.73 [0.67, 0.79] | 0.77 [0.71, 0.83] | 0.64 | 1.00 | — |  |
| validation | 2249 | 1195 | 0.74 [0.70, 0.78] | 0.75 [0.71, 0.79] | 0.73 [0.69, 0.77] | 0.59 | 1.00 | 0.69 (60 archetypes) |  |
| validation, no unseen cards | 736 | 362 | 0.88 [0.84, 0.91] | 0.90 [0.86, 0.93] | 0.86 [0.82, 0.90] | 0.74 | 1.00 | 0.90 (13 archetypes) |  |
| validation, unseen cards | 1513 | 833 | 0.66 [0.60, 0.72] | 0.67 [0.61, 0.73] | 0.65 [0.59, 0.71] | 0.51 | 1.00 | 0.59 (39 archetypes) |  |
| validation, new maindeck | 2229 | 1182 | 0.74 [0.69, 0.78] | 0.75 [0.71, 0.79] | 0.73 [0.68, 0.77] | 0.58 | 1.00 | 0.69 (60 archetypes) |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — |  |
| validation, existing archetypes | 1966 | 1114 | 0.76 [0.71, 0.80] | 0.75 [0.71, 0.80] | 0.77 [0.72, 0.81] | 0.67 | 1.00 | 0.70 (57 archetypes) |  |
| validation, new archetypes | 283 | 84 | 0.62 [0.46, 0.75] | 0.75 [0.56, 0.89] | 0.53 [0.39, 0.64] | 0.00 | 1.00 | 0.55 (3 archetypes) |  |

## Candidates

| Row | Decks | Maindecks | Top 1 | Top 5 | MRR | Notes |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.91 [0.90, 0.92] | 0.98 [0.97, 0.98] | 0.94 [0.94, 0.95] |  |
| held-out, unseen cards | 230 | 198 | 0.64 [0.56, 0.71] | 0.80 [0.74, 0.85] | 0.72 [0.66, 0.78] |  |
| validation | 2249 | 1195 | 0.59 [0.53, 0.64] | 0.76 [0.72, 0.81] | 0.67 [0.62, 0.71] |  |
| validation, no unseen cards | 736 | 362 | 0.74 [0.64, 0.83] | 0.85 [0.75, 0.94] | 0.79 [0.69, 0.87] |  |
| validation, unseen cards | 1513 | 833 | 0.51 [0.44, 0.58] | 0.72 [0.66, 0.77] | 0.61 [0.55, 0.67] |  |
| validation, new maindeck | 2229 | 1182 | 0.58 [0.52, 0.64] | 0.76 [0.71, 0.81] | 0.67 [0.61, 0.71] |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |  |
| validation, existing archetypes | 1966 | 1114 | 0.67 [0.62, 0.72] | 0.87 [0.85, 0.89] | 0.76 [0.72, 0.80] |  |
| validation, new archetypes | 283 | 84 | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] | 0.02 [0.01, 0.03] |  |

## Validation curve

No validation curve: this model has no threshold to tune.

### Top confusions: held-out

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Anvil Colossus | Metalwork Colossus | on | 36 | [251405](https://pennydreadfulmagic.com/decks/251405/), [251416](https://pennydreadfulmagic.com/decks/251416/), [251488](https://pennydreadfulmagic.com/decks/251488/) |
| WUBR Jokulhaups Control | Grixis Jokulhaups Control | off | 20 | [193709](https://pennydreadfulmagic.com/decks/193709/), [193740](https://pennydreadfulmagic.com/decks/193740/), [193744](https://pennydreadfulmagic.com/decks/193744/) |
| Rakdos Reanimator | Worldgorger Dragon | off | 13 | [110061](https://pennydreadfulmagic.com/decks/110061/), [144460](https://pennydreadfulmagic.com/decks/144460/), [144505](https://pennydreadfulmagic.com/decks/144505/) |
| Izzet Spells | Izzet Tempo | off | 12 | [81279](https://pennydreadfulmagic.com/decks/81279/), [84765](https://pennydreadfulmagic.com/decks/84765/), [86312](https://pennydreadfulmagic.com/decks/86312/) |
| Mono Green Stompy | Rofellos Ramp | off | 11 | [100811](https://pennydreadfulmagic.com/decks/100811/), [100836](https://pennydreadfulmagic.com/decks/100836/), [100955](https://pennydreadfulmagic.com/decks/100955/) |
| Mono Blue Tempo | Mono Blue Aggro | off | 11 | [117733](https://pennydreadfulmagic.com/decks/117733/), [117917](https://pennydreadfulmagic.com/decks/117917/), [117995](https://pennydreadfulmagic.com/decks/117995/) |
| Gruul Post | Greenpost | off | 10 | [102881](https://pennydreadfulmagic.com/decks/102881/), [110038](https://pennydreadfulmagic.com/decks/110038/), [110109](https://pennydreadfulmagic.com/decks/110109/) |
| Dimir Control | Zur's Weirding | off | 10 | [109444](https://pennydreadfulmagic.com/decks/109444/), [110706](https://pennydreadfulmagic.com/decks/110706/), [110729](https://pennydreadfulmagic.com/decks/110729/) |
| Soulflayer | Dimir Reanimator | off | 10 | [189014](https://pennydreadfulmagic.com/decks/189014/), [189060](https://pennydreadfulmagic.com/decks/189060/), [189070](https://pennydreadfulmagic.com/decks/189070/) |
| Midrange | Ramp | off | 9 | [100033](https://pennydreadfulmagic.com/decks/100033/), [148904](https://pennydreadfulmagic.com/decks/148904/), [172841](https://pennydreadfulmagic.com/decks/172841/) |

### Top confusions: validation

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Solemnity Aristocrats | Orzhov Aristocrats | on | 97 | [270547](https://pennydreadfulmagic.com/decks/270547/), [270553](https://pennydreadfulmagic.com/decks/270553/), [270592](https://pennydreadfulmagic.com/decks/270592/) |
| Izzet Madcap | Izzet Control | on | 75 | [269653](https://pennydreadfulmagic.com/decks/269653/), [269792](https://pennydreadfulmagic.com/decks/269792/), [269796](https://pennydreadfulmagic.com/decks/269796/) |
| Valakut Ramp | Ramp | on | 27 | [269579](https://pennydreadfulmagic.com/decks/269579/), [269598](https://pennydreadfulmagic.com/decks/269598/), [269626](https://pennydreadfulmagic.com/decks/269626/) |
| Enchantments Matter | Enchantress | off | 25 | [269995](https://pennydreadfulmagic.com/decks/269995/), [270040](https://pennydreadfulmagic.com/decks/270040/), [270079](https://pennydreadfulmagic.com/decks/270079/) |
| Izzet Madcap | Taking Turns | off | 23 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Simic Flash | Bant Control | off | 16 | [269602](https://pennydreadfulmagic.com/decks/269602/), [269638](https://pennydreadfulmagic.com/decks/269638/), [269646](https://pennydreadfulmagic.com/decks/269646/) |
| Valakut Ramp | Fires of Invention | off | 15 | [269526](https://pennydreadfulmagic.com/decks/269526/), [269704](https://pennydreadfulmagic.com/decks/269704/), [269931](https://pennydreadfulmagic.com/decks/269931/) |
| Graveyard Value | Dimir Midrange | off | 15 | [270059](https://pennydreadfulmagic.com/decks/270059/), [270072](https://pennydreadfulmagic.com/decks/270072/), [270074](https://pennydreadfulmagic.com/decks/270074/) |
| Applejacks | Jokulhaups Combo | off | 13 | [269782](https://pennydreadfulmagic.com/decks/269782/), [270161](https://pennydreadfulmagic.com/decks/270161/), [270240](https://pennydreadfulmagic.com/decks/270240/) |
| Solemnity Aristocrats | Orzhov Midrange | off | 13 | [271049](https://pennydreadfulmagic.com/decks/271049/), [271585](https://pennydreadfulmagic.com/decks/271585/), [271598](https://pennydreadfulmagic.com/decks/271598/) |

## Compared with run 8

Run 12 minus run 8, on the decks both runs guessed, with paired intervals.

| Row | Decks compared | Left out | hF | hP | hR | Exact match |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0 | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] |
| held-out, unseen cards | 230 | 0 | 0.00 [-0.02, 0.03] | 0.00 [-0.03, 0.02] | 0.01 [-0.02, 0.03] | 0.00 [-0.03, 0.03] |
| validation | 2249 | 0 | 0.02 [-0.02, 0.07] | 0.02 [-0.02, 0.06] | 0.02 [-0.03, 0.07] | 0.01 [-0.03, 0.06] |
| validation, no unseen cards | 736 | 0 | 0.06 [0.01, 0.14] | 0.06 [0.01, 0.14] | 0.06 [0.01, 0.14] | 0.00 [-0.03, 0.02] |
| validation, unseen cards | 1513 | 0 | -0.01 [-0.07, 0.06] | -0.01 [-0.06, 0.06] | -0.01 [-0.07, 0.07] | 0.01 [-0.04, 0.10] |
| validation, new maindeck | 2229 | 0 | 0.02 [-0.03, 0.06] | 0.02 [-0.02, 0.06] | 0.02 [-0.03, 0.07] | 0.01 [-0.03, 0.07] |
| validation, repeated maindeck | 20 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0 | 0.01 [-0.03, 0.06] | 0.01 [-0.02, 0.05] | 0.01 [-0.03, 0.07] | 0.01 [-0.04, 0.08] |
| validation, new archetypes | 283 | 0 | 0.08 [-0.12, 0.27] | 0.10 [-0.14, 0.33] | 0.06 [-0.11, 0.23] | 0.00 [0.00, 0.00] |

### Candidates compared

| Row | Decks compared | Top 1 | Top 5 | MRR |
|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| held-out, unseen cards | 230 | 0.00 [-0.03, 0.03] | -0.04 [-0.09, 0.00] | -0.01 [-0.03, 0.01] |
| validation | 2249 | 0.01 [-0.03, 0.06] | -0.02 [-0.03, 0.00] | 0.00 [-0.02, 0.03] |
| validation, no unseen cards | 736 | 0.00 [-0.03, 0.02] | 0.00 [-0.01, 0.01] | 0.00 [-0.02, 0.01] |
| validation, unseen cards | 1513 | 0.01 [-0.04, 0.10] | -0.02 [-0.04, 0.00] | 0.00 [-0.04, 0.04] |
| validation, new maindeck | 2229 | 0.01 [-0.03, 0.07] | -0.02 [-0.03, 0.00] | 0.00 [-0.03, 0.03] |
| validation, repeated maindeck | 20 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0.01 [-0.04, 0.08] | -0.02 [-0.03, 0.00] | 0.00 [-0.03, 0.03] |
| validation, new archetypes | 283 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.01] |
