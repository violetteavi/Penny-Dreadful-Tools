# Run 7: embedding nearest deck v2

| | |
|---|---|
| Run | 7 |
| Made | 2026-10-12 18:49:20 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | 6648e7be9d63f0411c24e75cec9838f02a6cb2fa |
| Model | 7: embedding nearest deck v2, parameters {"embedding": "potion__masked__average__w1-0-0-0__fit1-38__emb1-39"}, seed 0 |
| Snapshot | 1 |
| Scheme | 1 (default) |
| Trained on | train (162878 decks) |
| Tuned on |  (0 decks) |
| Metrics version | 2 |
| Rows version | 3 |
| PRs | #52, #53 |

## Results

| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |
|---|---|---|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.94 [0.93, 0.95] | 0.94 [0.93, 0.95] | 0.95 [0.94, 0.95] | 0.91 | 1.00 | 0.92 (311 archetypes) |  |
| held-out, unseen cards | 230 | 198 | 0.71 [0.64, 0.77] | 0.69 [0.62, 0.76] | 0.72 [0.65, 0.79] | 0.59 | 1.00 | — |  |
| validation | 2249 | 1195 | 0.75 [0.71, 0.79] | 0.76 [0.72, 0.80] | 0.73 [0.69, 0.77] | 0.58 | 1.00 | 0.69 (60 archetypes) |  |
| validation, no unseen cards | 736 | 362 | 0.87 [0.83, 0.90] | 0.89 [0.85, 0.92] | 0.85 [0.81, 0.89] | 0.73 | 1.00 | 0.86 (13 archetypes) |  |
| validation, unseen cards | 1513 | 833 | 0.68 [0.63, 0.73] | 0.69 [0.64, 0.74] | 0.67 [0.61, 0.72] | 0.50 | 1.00 | 0.60 (39 archetypes) |  |
| validation, new maindeck | 2229 | 1182 | 0.75 [0.70, 0.78] | 0.76 [0.72, 0.80] | 0.73 [0.69, 0.77] | 0.57 | 1.00 | 0.69 (60 archetypes) |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — |  |
| validation, existing archetypes | 1966 | 1114 | 0.75 [0.69, 0.79] | 0.74 [0.69, 0.78] | 0.75 [0.69, 0.80] | 0.66 | 1.00 | 0.69 (57 archetypes) |  |
| validation, new archetypes | 283 | 84 | 0.76 [0.71, 0.80] | 0.92 [0.86, 0.96] | 0.65 [0.60, 0.69] | 0.00 | 1.00 | 0.68 (3 archetypes) |  |

## Candidates

| Row | Decks | Maindecks | Top 1 | Top 5 | MRR | Notes |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.91 [0.90, 0.92] | 0.98 [0.97, 0.98] | 0.94 [0.94, 0.95] |  |
| held-out, unseen cards | 230 | 198 | 0.59 [0.52, 0.67] | 0.81 [0.75, 0.87] | 0.70 [0.64, 0.76] |  |
| validation | 2249 | 1195 | 0.58 [0.52, 0.63] | 0.77 [0.72, 0.81] | 0.66 [0.61, 0.71] |  |
| validation, no unseen cards | 736 | 362 | 0.73 [0.63, 0.82] | 0.85 [0.74, 0.93] | 0.78 [0.69, 0.87] |  |
| validation, unseen cards | 1513 | 833 | 0.50 [0.43, 0.57] | 0.73 [0.67, 0.79] | 0.60 [0.54, 0.66] |  |
| validation, new maindeck | 2229 | 1182 | 0.57 [0.51, 0.63] | 0.77 [0.72, 0.81] | 0.66 [0.60, 0.71] |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |  |
| validation, existing archetypes | 1966 | 1114 | 0.66 [0.59, 0.71] | 0.88 [0.86, 0.90] | 0.75 [0.70, 0.79] |  |
| validation, new archetypes | 283 | 84 | 0.00 [0.00, 0.01] | 0.00 [0.00, 0.01] | 0.02 [0.01, 0.03] |  |

## Validation curve

No validation curve: this model has no threshold to tune.

### Top confusions: held-out

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Jund | Jund Jokulhaups Control | off | 47 | [186682](https://pennydreadfulmagic.com/decks/186682/), [186737](https://pennydreadfulmagic.com/decks/186737/), [186744](https://pennydreadfulmagic.com/decks/186744/) |
| Anvil Colossus | Metalwork Colossus | on | 36 | [251405](https://pennydreadfulmagic.com/decks/251405/), [251416](https://pennydreadfulmagic.com/decks/251416/), [251488](https://pennydreadfulmagic.com/decks/251488/) |
| WUBR Jokulhaups Control | Grixis Jokulhaups Control | off | 20 | [193709](https://pennydreadfulmagic.com/decks/193709/), [193740](https://pennydreadfulmagic.com/decks/193740/), [193744](https://pennydreadfulmagic.com/decks/193744/) |
| Izzet Spells | Izzet Tempo | off | 17 | [67635](https://pennydreadfulmagic.com/decks/67635/), [81523](https://pennydreadfulmagic.com/decks/81523/), [84765](https://pennydreadfulmagic.com/decks/84765/) |
| Rakdos Reanimator | Worldgorger Dragon | off | 13 | [110061](https://pennydreadfulmagic.com/decks/110061/), [144460](https://pennydreadfulmagic.com/decks/144460/), [144505](https://pennydreadfulmagic.com/decks/144505/) |
| Mono Blue Tempo | Mono Blue Aggro | off | 11 | [117733](https://pennydreadfulmagic.com/decks/117733/), [117917](https://pennydreadfulmagic.com/decks/117917/), [117995](https://pennydreadfulmagic.com/decks/117995/) |
| Gruul Post | Greenpost | off | 10 | [110038](https://pennydreadfulmagic.com/decks/110038/), [110109](https://pennydreadfulmagic.com/decks/110109/), [110325](https://pennydreadfulmagic.com/decks/110325/) |
| Soulflayer | Dimir Reanimator | off | 10 | [189014](https://pennydreadfulmagic.com/decks/189014/), [189060](https://pennydreadfulmagic.com/decks/189060/), [189070](https://pennydreadfulmagic.com/decks/189070/) |
| Dimir Control | Zur's Weirding | off | 9 | [110706](https://pennydreadfulmagic.com/decks/110706/), [110729](https://pennydreadfulmagic.com/decks/110729/), [145903](https://pennydreadfulmagic.com/decks/145903/) |
| Pox | Fake-Rack | off | 9 | [148264](https://pennydreadfulmagic.com/decks/148264/), [160765](https://pennydreadfulmagic.com/decks/160765/), [191805](https://pennydreadfulmagic.com/decks/191805/) |

### Top confusions: validation

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Solemnity Aristocrats | Orzhov Aristocrats | on | 109 | [270547](https://pennydreadfulmagic.com/decks/270547/), [270553](https://pennydreadfulmagic.com/decks/270553/), [270592](https://pennydreadfulmagic.com/decks/270592/) |
| Izzet Madcap | Izzet Control | on | 106 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Equipment Aggro | Red Deck Wins | off | 67 | [269637](https://pennydreadfulmagic.com/decks/269637/), [269689](https://pennydreadfulmagic.com/decks/269689/), [269705](https://pennydreadfulmagic.com/decks/269705/) |
| Valakut Ramp | Ramp | on | 39 | [269511](https://pennydreadfulmagic.com/decks/269511/), [269558](https://pennydreadfulmagic.com/decks/269558/), [269626](https://pennydreadfulmagic.com/decks/269626/) |
| Enchantments Matter | Zur the Enchanter | off | 17 | [270249](https://pennydreadfulmagic.com/decks/270249/), [270348](https://pennydreadfulmagic.com/decks/270348/), [270640](https://pennydreadfulmagic.com/decks/270640/) |
| Applejacks | Lumbertwin | off | 15 | [269782](https://pennydreadfulmagic.com/decks/269782/), [270161](https://pennydreadfulmagic.com/decks/270161/), [270240](https://pennydreadfulmagic.com/decks/270240/) |
| Izzet Tempo | Izzet Control | off | 13 | [271613](https://pennydreadfulmagic.com/decks/271613/), [271640](https://pennydreadfulmagic.com/decks/271640/), [271643](https://pennydreadfulmagic.com/decks/271643/) |
| Graveyard Value | Orzhov Aristocrats | off | 12 | [269581](https://pennydreadfulmagic.com/decks/269581/), [270059](https://pennydreadfulmagic.com/decks/270059/), [270072](https://pennydreadfulmagic.com/decks/270072/) |
| Polymorph | Azorius Control | off | 12 | [270508](https://pennydreadfulmagic.com/decks/270508/), [270581](https://pennydreadfulmagic.com/decks/270581/), [270684](https://pennydreadfulmagic.com/decks/270684/) |
| Dimir Tempo | Dimir Control | off | 10 | [269611](https://pennydreadfulmagic.com/decks/269611/), [269613](https://pennydreadfulmagic.com/decks/269613/), [269623](https://pennydreadfulmagic.com/decks/269623/) |

## Compared with run 9

Run 7 minus run 9, on the decks both runs guessed, with paired intervals.

| Row | Decks compared | Left out | hF | hP | hR | Exact match |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0 | 0.02 [0.01, 0.03] | 0.02 [0.00, 0.02] | 0.02 [0.01, 0.03] | 0.03 [0.02, 0.04] |
| held-out, unseen cards | 230 | 0 | 0.01 [-0.06, 0.09] | -0.08 [-0.15, 0.00] | 0.09 [0.00, 0.17] | 0.06 [-0.02, 0.14] |
| validation | 2249 | 0 | 0.23 [0.18, 0.30] | 0.11 [0.04, 0.19] | 0.30 [0.25, 0.36] | 0.21 [0.15, 0.27] |
| validation, no unseen cards | 736 | 0 | 0.24 [0.13, 0.35] | 0.24 [0.12, 0.36] | 0.24 [0.13, 0.35] | 0.18 [0.09, 0.28] |
| validation, unseen cards | 1513 | 0 | 0.24 [0.18, 0.31] | 0.04 [-0.03, 0.12] | 0.34 [0.28, 0.40] | 0.22 [0.16, 0.30] |
| validation, new maindeck | 2229 | 0 | 0.23 [0.17, 0.30] | 0.12 [0.04, 0.19] | 0.31 [0.25, 0.37] | 0.21 [0.15, 0.28] |
| validation, repeated maindeck | 20 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0 | 0.16 [0.11, 0.22] | 0.03 [-0.03, 0.09] | 0.25 [0.20, 0.32] | 0.24 [0.17, 0.31] |
| validation, new archetypes | 283 | 0 | 0.64 [0.50, 0.73] | 0.72 [0.53, 0.85] | 0.56 [0.45, 0.63] | 0.00 [0.00, 0.01] |

### Candidates compared

| Row | Decks compared | Top 1 | Top 5 | MRR |
|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0.03 [0.02, 0.03] | 0.02 [0.01, 0.02] | 0.02 [0.02, 0.03] |
| held-out, unseen cards | 230 | 0.03 [-0.06, 0.10] | 0.03 [-0.02, 0.09] | 0.03 [-0.02, 0.09] |
| validation | 2249 | 0.12 [0.08, 0.17] | 0.10 [0.05, 0.17] | 0.10 [0.07, 0.14] |
| validation, no unseen cards | 736 | 0.17 [0.09, 0.28] | 0.07 [0.04, 0.11] | 0.11 [0.06, 0.17] |
| validation, unseen cards | 1513 | 0.10 [0.06, 0.14] | 0.12 [0.04, 0.20] | 0.10 [0.07, 0.14] |
| validation, new maindeck | 2229 | 0.12 [0.08, 0.17] | 0.10 [0.05, 0.17] | 0.10 [0.07, 0.14] |
| validation, repeated maindeck | 20 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1966 | 0.14 [0.09, 0.19] | 0.14 [0.09, 0.21] | 0.13 [0.10, 0.17] |
| validation, new archetypes | 283 | 0.00 [-0.01, 0.01] | -0.15 [-0.32, -0.03] | -0.10 [-0.12, -0.07] |
