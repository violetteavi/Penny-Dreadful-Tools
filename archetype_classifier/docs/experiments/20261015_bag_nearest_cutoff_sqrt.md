# Run 16: bag of cards nearest deck v1

| | |
|---|---|
| Run | 16 |
| Made | 2026-10-15 18:29:19 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | 80e7402112ef2a8d2da96fd51766745b18e17e68 |
| Model | 16: bag of cards nearest deck v1, parameters {"copies": "sqrt"}, seed 0 |
| Snapshot | 1 |
| Scheme | 3 (default, labels at season 39) |
| Label cutoff | 2025-10-03 07:00 UTC (1759474800) |
| Trained on | train (162869 decks) |
| Tuned on |  (0 decks) |
| Metrics version | 2 |
| Rows version | 4 |
| PRs | #61 |

## Results

| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |
|---|---|---|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.95 [0.95, 0.96] | 0.95 [0.94, 0.95] | 0.95 [0.95, 0.96] | 0.92 | 1.00 | 0.93 (311 archetypes) |  |
| held-out, unseen cards | 230 | 198 | 0.80 [0.74, 0.84] | 0.78 [0.72, 0.83] | 0.82 [0.76, 0.86] | 0.69 | 1.00 | — |  |
| held-out, label changed after its season | 2212 | 1097 | 0.94 [0.93, 0.96] | 0.94 [0.93, 0.96] | 0.94 [0.93, 0.96] | 0.90 | 1.00 | 0.92 (45 archetypes) |  |
| validation | 2249 | 1195 | 0.71 [0.66, 0.76] | 0.74 [0.70, 0.78] | 0.69 [0.63, 0.74] | 0.60 | 1.00 | 0.71 (60 archetypes) |  |
| validation, no unseen cards | 736 | 362 | 0.79 [0.68, 0.87] | 0.85 [0.78, 0.90] | 0.74 [0.61, 0.85] | 0.74 | 1.00 | 0.77 (13 archetypes) |  |
| validation, unseen cards | 1513 | 833 | 0.67 [0.62, 0.73] | 0.69 [0.64, 0.74] | 0.66 [0.61, 0.72] | 0.53 | 1.00 | 0.63 (39 archetypes) |  |
| validation, new maindeck | 2229 | 1182 | 0.71 [0.66, 0.76] | 0.74 [0.70, 0.78] | 0.69 [0.63, 0.75] | 0.59 | 1.00 | 0.70 (60 archetypes) |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — |  |
| validation, existing archetypes | 1956 | 1106 | 0.77 [0.73, 0.81] | 0.77 [0.73, 0.81] | 0.78 [0.73, 0.82] | 0.69 | 1.00 | 0.73 (57 archetypes) |  |
| validation, new archetypes | 293 | 92 | 0.34 [0.21, 0.49] | 0.50 [0.32, 0.66] | 0.26 [0.15, 0.40] | 0.00 | 1.00 | 0.29 (3 archetypes) |  |
| validation, label changed after its season | 80 | 15 | 0.39 [0.23, 0.53] | 0.48 [0.24, 0.57] | 0.34 [0.21, 0.49] | 0.04 | 1.00 | 0.42 (1 archetypes) |  |

## Candidates

| Row | Decks | Maindecks | Top 1 | Top 5 | MRR | Notes |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 9210 | 0.92 [0.92, 0.93] | 0.98 [0.98, 0.98] | 0.95 [0.94, 0.95] |  |
| held-out, unseen cards | 230 | 198 | 0.69 [0.61, 0.75] | 0.87 [0.81, 0.92] | 0.76 [0.70, 0.82] |  |
| held-out, label changed after its season | 2212 | 1097 | 0.90 [0.88, 0.92] | 0.97 [0.95, 0.98] | 0.93 [0.91, 0.95] |  |
| validation | 2249 | 1195 | 0.60 [0.53, 0.65] | 0.79 [0.74, 0.83] | 0.68 [0.62, 0.73] |  |
| validation, no unseen cards | 736 | 362 | 0.74 [0.63, 0.82] | 0.85 [0.75, 0.93] | 0.79 [0.69, 0.87] |  |
| validation, unseen cards | 1513 | 833 | 0.53 [0.46, 0.60] | 0.76 [0.70, 0.81] | 0.62 [0.56, 0.68] |  |
| validation, new maindeck | 2229 | 1182 | 0.59 [0.53, 0.65] | 0.79 [0.73, 0.83] | 0.68 [0.62, 0.73] |  |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |  |
| validation, existing archetypes | 1956 | 1106 | 0.69 [0.62, 0.74] | 0.91 [0.88, 0.93] | 0.78 [0.73, 0.82] |  |
| validation, new archetypes | 293 | 92 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |  |
| validation, label changed after its season | 80 | 15 | 0.04 [0.00, 0.33] | 0.85 [0.12, 0.96] | 0.24 [0.10, 0.38] |  |

## Validation curve

No validation curve: this model has no threshold to tune.

### Top confusions: held-out

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Izzet Spells | Izzet Tempo | off | 24 | [81523](https://pennydreadfulmagic.com/decks/81523/), [82204](https://pennydreadfulmagic.com/decks/82204/), [84765](https://pennydreadfulmagic.com/decks/84765/) |
| WUBR Jokulhaups Control | Grixis Jokulhaups Control | off | 20 | [193709](https://pennydreadfulmagic.com/decks/193709/), [193740](https://pennydreadfulmagic.com/decks/193740/), [193744](https://pennydreadfulmagic.com/decks/193744/) |
| Rakdos Reanimator | Worldgorger Dragon | off | 13 | [110061](https://pennydreadfulmagic.com/decks/110061/), [144460](https://pennydreadfulmagic.com/decks/144460/), [144505](https://pennydreadfulmagic.com/decks/144505/) |
| Mono Blue Tempo | Mono Blue Aggro | off | 13 | [117725](https://pennydreadfulmagic.com/decks/117725/), [117733](https://pennydreadfulmagic.com/decks/117733/), [117917](https://pennydreadfulmagic.com/decks/117917/) |
| Soulflayer | Dimir Reanimator | off | 10 | [189014](https://pennydreadfulmagic.com/decks/189014/), [189060](https://pennydreadfulmagic.com/decks/189060/), [189070](https://pennydreadfulmagic.com/decks/189070/) |
| Dimir Control | Zur's Weirding | off | 9 | [110706](https://pennydreadfulmagic.com/decks/110706/), [110729](https://pennydreadfulmagic.com/decks/110729/), [145903](https://pennydreadfulmagic.com/decks/145903/) |
| Pox | Fake-Rack | off | 9 | [148264](https://pennydreadfulmagic.com/decks/148264/), [160765](https://pennydreadfulmagic.com/decks/160765/), [191805](https://pennydreadfulmagic.com/decks/191805/) |
| Midrange | Esper Control | off | 8 | [165101](https://pennydreadfulmagic.com/decks/165101/), [165449](https://pennydreadfulmagic.com/decks/165449/), [165524](https://pennydreadfulmagic.com/decks/165524/) |
| Tokens | Mono White Tokens | on | 7 | [68916](https://pennydreadfulmagic.com/decks/68916/), [68969](https://pennydreadfulmagic.com/decks/68969/), [69036](https://pennydreadfulmagic.com/decks/69036/) |
| Elves | Mono Green Stompy | off | 7 | [99904](https://pennydreadfulmagic.com/decks/99904/), [99935](https://pennydreadfulmagic.com/decks/99935/), [100176](https://pennydreadfulmagic.com/decks/100176/) |

### Top confusions: validation

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Solemnity Aristocrats | Combo-Control | off | 110 | [270547](https://pennydreadfulmagic.com/decks/270547/), [270553](https://pennydreadfulmagic.com/decks/270553/), [270592](https://pennydreadfulmagic.com/decks/270592/) |
| Izzet Madcap | Izzet Control | on | 105 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Equipment Aggro | Red Deck Wins | off | 66 | [269637](https://pennydreadfulmagic.com/decks/269637/), [269689](https://pennydreadfulmagic.com/decks/269689/), [269705](https://pennydreadfulmagic.com/decks/269705/) |
| Enchantments Matter | Enchantress | off | 38 | [269995](https://pennydreadfulmagic.com/decks/269995/), [270040](https://pennydreadfulmagic.com/decks/270040/), [270079](https://pennydreadfulmagic.com/decks/270079/) |
| Valakut Ramp | Naya Midrange | off | 22 | [269931](https://pennydreadfulmagic.com/decks/269931/), [269998](https://pennydreadfulmagic.com/decks/269998/), [270007](https://pennydreadfulmagic.com/decks/270007/) |
| Orzhov Midrange | Orzhov Control | off | 17 | [270398](https://pennydreadfulmagic.com/decks/270398/), [270421](https://pennydreadfulmagic.com/decks/270421/), [270451](https://pennydreadfulmagic.com/decks/270451/) |
| Azorius Tempo | Mono Blue Librarians | off | 15 | [271701](https://pennydreadfulmagic.com/decks/271701/), [271722](https://pennydreadfulmagic.com/decks/271722/), [271734](https://pennydreadfulmagic.com/decks/271734/) |
| Izzet Control | Izzet Spells | off | 13 | [269481](https://pennydreadfulmagic.com/decks/269481/), [269622](https://pennydreadfulmagic.com/decks/269622/), [269624](https://pennydreadfulmagic.com/decks/269624/) |
| Applejacks | Lumbertwin | off | 13 | [269782](https://pennydreadfulmagic.com/decks/269782/), [270161](https://pennydreadfulmagic.com/decks/270161/), [270240](https://pennydreadfulmagic.com/decks/270240/) |
| Legends Aggro | White Weenie | off | 10 | [269774](https://pennydreadfulmagic.com/decks/269774/), [269804](https://pennydreadfulmagic.com/decks/269804/), [269808](https://pennydreadfulmagic.com/decks/269808/) |

## Compared with run 10

Run 16 minus run 10, on the decks both runs guessed, with paired intervals.

| Row | Decks compared | Left out | hF | hP | hR | Exact match |
|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| held-out, unseen cards | 230 | 0 | 0.00 [-0.01, 0.00] | 0.00 [-0.01, 0.00] | 0.00 [-0.01, 0.00] | 0.00 [-0.01, 0.00] |
| held-out, label changed after its season | 2212 | 0 | -0.01 [-0.01, 0.00] | -0.01 [-0.01, 0.00] | -0.01 [-0.01, 0.00] | -0.01 [-0.02, -0.01] |
| validation | 2249 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [-0.01, 0.00] |
| validation, no unseen cards | 736 | 0 | 0.00 [-0.01, 0.00] | 0.00 [0.00, 0.00] | 0.00 [-0.01, 0.00] | -0.01 [-0.02, 0.00] |
| validation, unseen cards | 1513 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [-0.01, 0.00] |
| validation, new maindeck | 2229 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [-0.01, 0.00] |
| validation, repeated maindeck | 20 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1956 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, new archetypes | 293 | 0 | -0.02 [-0.04, -0.01] | -0.02 [-0.04, 0.00] | -0.02 [-0.03, 0.00] | -0.04 [-0.08, -0.01] |
| validation, label changed after its season | 80 | 0 | -0.02 [-0.21, 0.00] | -0.03 [-0.22, 0.00] | -0.02 [-0.21, 0.00] | -0.03 [-0.21, 0.00] |

### Candidates compared

| Row | Decks compared | Top 1 | Top 5 | MRR |
|---|---|---|---|---|
| held-out, no unseen cards | 17694 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| held-out, unseen cards | 230 | 0.00 [-0.01, 0.00] | 0.00 [-0.01, 0.00] | 0.00 [-0.01, 0.00] |
| held-out, label changed after its season | 2212 | -0.01 [-0.02, -0.01] | -0.01 [-0.02, -0.01] | -0.01 [-0.02, -0.01] |
| validation | 2249 | 0.00 [-0.01, 0.00] | -0.02 [-0.05, -0.01] | -0.02 [-0.03, -0.01] |
| validation, no unseen cards | 736 | -0.01 [-0.02, 0.00] | -0.01 [-0.02, 0.00] | -0.03 [-0.04, -0.01] |
| validation, unseen cards | 1513 | 0.00 [-0.01, 0.00] | -0.03 [-0.07, -0.01] | -0.02 [-0.03, -0.01] |
| validation, new maindeck | 2229 | 0.00 [-0.01, 0.00] | -0.02 [-0.05, -0.01] | -0.02 [-0.03, -0.01] |
| validation, repeated maindeck | 20 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| validation, existing archetypes | 1956 | 0.00 [0.00, 0.00] | 0.00 [-0.01, 0.00] | 0.00 [0.00, 0.00] |
| validation, new archetypes | 293 | -0.04 [-0.08, -0.01] | -0.15 [-0.32, -0.04] | -0.15 [-0.19, -0.12] |
| validation, label changed after its season | 80 | -0.03 [-0.21, 0.00] | -0.03 [-0.21, 0.00] | -0.02 [-0.21, 0.00] |
