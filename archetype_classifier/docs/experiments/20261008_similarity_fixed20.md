# Run 3: similarity v2

| | |
|---|---|
| Run | 3 |
| Made | 2026-10-08 15:12:57 |
| Scope | held_out, validation |
| Decks predicted | 20173 |
| Prediction hash | 505b55d8d03395c8e6fad704d06bdad133a8bf15 |
| Model | 3: similarity v2, parameters {"threshold": 20}, seed 0 |
| Snapshot | 1 |
| Scheme | 2 (similarity baseline) |
| Trained on | train (202385 decks) |
| Tuned on | validation (2249 decks) |
| Metrics version | 1 |
| Rows version | 1 |
| PRs | #34, #47 |

## Results

| Row | Decks | Maindecks | hF | hP | hR | Exact match | Coverage | Macro hF | Notes |
|---|---|---|---|---|---|---|---|---|---|
| held-out, no unseen cards | 17776 | 9281 | 0.92 [0.92, 0.93] | 0.93 [0.92, 0.93] | 0.92 [0.92, 0.93] | 0.88 | 0.99 | 0.90 (311 archetypes) |  |
| held-out, unseen cards | 148 | 127 | 0.66 [0.57, 0.74] | 0.74 [0.65, 0.82] | 0.60 [0.51, 0.69] | 0.51 | 0.77 | — |  |
| validation | 2249 | 1195 | 0.52 [0.45, 0.58] | 0.65 [0.58, 0.72] | 0.43 [0.37, 0.49] | 0.37 | 0.67 | 0.52 (60 archetypes) | tuned on |
| validation, new maindeck | 2229 | 1182 | 0.51 [0.44, 0.58] | 0.65 [0.57, 0.72] | 0.42 [0.36, 0.49] | 0.36 | 0.66 | 0.52 (60 archetypes) | tuned on |
| validation, repeated maindeck | 20 | 13 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | — | tuned on |

## Validation curve

| Threshold | hP | hR | hF |
|---|---|---|---|
| 1 | 0.56 | 0.55 | 0.55 |
| 2 | 0.56 | 0.55 | 0.55 |
| 3 | 0.56 | 0.55 | 0.55 |
| 4 | 0.56 | 0.55 | 0.55 |
| 5 | 0.56 | 0.55 | 0.55 |
| 6 | 0.56 | 0.54 | 0.55 |
| 7 | 0.56 | 0.54 | 0.55 |
| 8 | 0.56 | 0.54 | 0.55 |
| 9 | 0.56 | 0.54 | 0.55 |
| 10 | 0.57 | 0.54 | 0.55 |
| 11 | 0.57 | 0.53 | 0.55 |
| 12 | 0.57 | 0.53 | 0.55 |
| 13 | 0.58 | 0.53 | 0.55 |
| 14 | 0.61 | 0.52 | 0.56 |
| 15 | 0.61 | 0.50 | 0.55 |
| 16 | 0.62 | 0.48 | 0.54 |
| 17 | 0.63 | 0.46 | 0.53 |
| 18 | 0.64 | 0.45 | 0.53 |
| 19 | 0.65 | 0.44 | 0.53 |
| **20 (chosen)** | 0.65 | 0.43 | 0.52 |
| 21 | 0.65 | 0.42 | 0.51 |
| 22 | 0.65 | 0.40 | 0.49 |
| 23 | 0.66 | 0.38 | 0.48 |
| 24 | 0.72 | 0.36 | 0.48 |
| 25 | 0.74 | 0.35 | 0.47 |
| 26 | 0.74 | 0.34 | 0.46 |
| 27 | 0.75 | 0.32 | 0.45 |
| 28 | 0.76 | 0.31 | 0.44 |
| 29 | 0.75 | 0.30 | 0.43 |
| 30 | 0.75 | 0.28 | 0.41 |
| 31 | 0.76 | 0.28 | 0.41 |
| 32 | 0.76 | 0.27 | 0.40 |
| 33 | 0.76 | 0.23 | 0.35 |
| 34 | 0.75 | 0.20 | 0.32 |
| 35 | 0.76 | 0.20 | 0.31 |
| 36 | 0.76 | 0.19 | 0.30 |
| 37 | 0.75 | 0.18 | 0.29 |
| 38 | 0.78 | 0.18 | 0.29 |
| 39 | 0.78 | 0.16 | 0.26 |
| 40 | 0.85 | 0.14 | 0.23 |
| 41 | 0.86 | 0.13 | 0.23 |
| 42 | 0.87 | 0.13 | 0.22 |
| 43 | 0.86 | 0.13 | 0.22 |
| 44 | 0.86 | 0.12 | 0.21 |
| 45 | 0.87 | 0.12 | 0.21 |
| 46 | 0.88 | 0.11 | 0.20 |
| 47 | 0.88 | 0.11 | 0.19 |
| 48 | 0.90 | 0.11 | 0.19 |
| 49 | 0.89 | 0.10 | 0.18 |
| 50 | 0.90 | 0.10 | 0.18 |
| 51 | 0.90 | 0.09 | 0.17 |
| 52 | 0.91 | 0.09 | 0.16 |
| 53 | 0.94 | 0.09 | 0.16 |
| 54 | 0.94 | 0.08 | 0.16 |
| 55 | 0.94 | 0.08 | 0.15 |
| 56 | 0.94 | 0.08 | 0.15 |
| 57 | 0.94 | 0.08 | 0.14 |
| 58 | 0.94 | 0.07 | 0.14 |
| 59 | 0.95 | 0.07 | 0.13 |
| 60 | 0.95 | 0.07 | 0.13 |
| 61 | 0.95 | 0.06 | 0.12 |
| 62 | 0.94 | 0.06 | 0.11 |
| 63 | 0.95 | 0.05 | 0.10 |
| 64 | 0.95 | 0.05 | 0.10 |
| 65 | 0.99 | 0.05 | 0.09 |
| 66 | 0.99 | 0.05 | 0.09 |
| 67 | 0.99 | 0.05 | 0.09 |
| 68 | 0.99 | 0.05 | 0.09 |
| 69 | 0.99 | 0.05 | 0.09 |
| 70 | 0.99 | 0.04 | 0.08 |
| 71 | 0.99 | 0.04 | 0.08 |
| 72 | 0.99 | 0.04 | 0.08 |
| 73 | 1.00 | 0.04 | 0.07 |
| 74 | 1.00 | 0.04 | 0.07 |
| 75 | 1.00 | 0.04 | 0.07 |
| 76 | 1.00 | 0.03 | 0.06 |
| 77 | 1.00 | 0.03 | 0.06 |
| 78 | 1.00 | 0.03 | 0.06 |
| 79 | 1.00 | 0.03 | 0.05 |
| 80 | 1.00 | 0.02 | 0.05 |
| 81 | 1.00 | 0.02 | 0.05 |
| 82 | 1.00 | 0.02 | 0.05 |
| 83 | 1.00 | 0.02 | 0.04 |
| 84 | 1.00 | 0.02 | 0.03 |
| 85 | 1.00 | 0.02 | 0.03 |
| 86 | 1.00 | 0.02 | 0.03 |
| 87 | 1.00 | 0.02 | 0.03 |
| 88 | 1.00 | 0.02 | 0.03 |
| 89 | 1.00 | 0.01 | 0.03 |
| 90 | 1.00 | 0.01 | 0.03 |
| 91 | 1.00 | 0.01 | 0.03 |
| 92 | 1.00 | 0.01 | 0.03 |
| 93 | 1.00 | 0.01 | 0.03 |
| 94 | 1.00 | 0.01 | 0.03 |
| 95 | 1.00 | 0.01 | 0.03 |
| 96 | 1.00 | 0.01 | 0.02 |
| 97 | 1.00 | 0.01 | 0.02 |
| 98 | 1.00 | 0.01 | 0.02 |
| 99 | 1.00 | 0.01 | 0.02 |
| 100 | 1.00 | 0.01 | 0.02 |

### Top confusions: held-out

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Burn | Red Deck Wins | off | 22 | [72369](https://pennydreadfulmagic.com/decks/72369/), [81140](https://pennydreadfulmagic.com/decks/81140/), [112025](https://pennydreadfulmagic.com/decks/112025/) |
| Midrange | no guess | on | 13 | [1415](https://pennydreadfulmagic.com/decks/1415/), [42539](https://pennydreadfulmagic.com/decks/42539/), [76108](https://pennydreadfulmagic.com/decks/76108/) |
| Izzet Spells | Izzet Tempo | off | 13 | [68104](https://pennydreadfulmagic.com/decks/68104/), [81523](https://pennydreadfulmagic.com/decks/81523/), [82204](https://pennydreadfulmagic.com/decks/82204/) |
| Rakdos Reanimator | Worldgorger Dragon | off | 13 | [110061](https://pennydreadfulmagic.com/decks/110061/), [144460](https://pennydreadfulmagic.com/decks/144460/), [144505](https://pennydreadfulmagic.com/decks/144505/) |
| Mono Blue Tempo | Mono Blue Aggro | off | 13 | [117733](https://pennydreadfulmagic.com/decks/117733/), [117917](https://pennydreadfulmagic.com/decks/117917/), [117995](https://pennydreadfulmagic.com/decks/117995/) |
| Izzet Control | Izzet Spells | off | 12 | [116](https://pennydreadfulmagic.com/decks/116/), [67735](https://pennydreadfulmagic.com/decks/67735/), [67761](https://pennydreadfulmagic.com/decks/67761/) |
| Pox | Fake-Rack | off | 11 | [51311](https://pennydreadfulmagic.com/decks/51311/), [51365](https://pennydreadfulmagic.com/decks/51365/), [148264](https://pennydreadfulmagic.com/decks/148264/) |
| Soulflayer | Dimir Reanimator | off | 10 | [189014](https://pennydreadfulmagic.com/decks/189014/), [189060](https://pennydreadfulmagic.com/decks/189060/), [189070](https://pennydreadfulmagic.com/decks/189070/) |
| Dimir Control | Zur's Weirding | off | 9 | [110706](https://pennydreadfulmagic.com/decks/110706/), [110729](https://pennydreadfulmagic.com/decks/110729/), [145903](https://pennydreadfulmagic.com/decks/145903/) |
| Red Deck Wins | Burn | off | 8 | [68667](https://pennydreadfulmagic.com/decks/68667/), [103836](https://pennydreadfulmagic.com/decks/103836/), [126277](https://pennydreadfulmagic.com/decks/126277/) |

### Top confusions: validation

| Label | Guess | Path | Decks | Example decks |
|---|---|---|---|---|
| Solemnity Aristocrats | Orzhov Legends | off | 82 | [270780](https://pennydreadfulmagic.com/decks/270780/), [270800](https://pennydreadfulmagic.com/decks/270800/), [270828](https://pennydreadfulmagic.com/decks/270828/) |
| Equipment Aggro | no guess | on | 80 | [269637](https://pennydreadfulmagic.com/decks/269637/), [269689](https://pennydreadfulmagic.com/decks/269689/), [269705](https://pennydreadfulmagic.com/decks/269705/) |
| Red Deck Wins | no guess | on | 60 | [269478](https://pennydreadfulmagic.com/decks/269478/), [269541](https://pennydreadfulmagic.com/decks/269541/), [269868](https://pennydreadfulmagic.com/decks/269868/) |
| Azorius Control | no guess | on | 51 | [269532](https://pennydreadfulmagic.com/decks/269532/), [269542](https://pennydreadfulmagic.com/decks/269542/), [269569](https://pennydreadfulmagic.com/decks/269569/) |
| Selesnya Heroic | Hexproof | off | 51 | [269872](https://pennydreadfulmagic.com/decks/269872/), [270412](https://pennydreadfulmagic.com/decks/270412/), [270419](https://pennydreadfulmagic.com/decks/270419/) |
| Izzet Madcap | no guess | on | 49 | [269792](https://pennydreadfulmagic.com/decks/269792/), [269818](https://pennydreadfulmagic.com/decks/269818/), [269823](https://pennydreadfulmagic.com/decks/269823/) |
| Valakut Ramp | no guess | on | 43 | [269511](https://pennydreadfulmagic.com/decks/269511/), [269526](https://pennydreadfulmagic.com/decks/269526/), [269558](https://pennydreadfulmagic.com/decks/269558/) |
| Izzet Madcap | Grixis Control | off | 33 | [269591](https://pennydreadfulmagic.com/decks/269591/), [269599](https://pennydreadfulmagic.com/decks/269599/), [269604](https://pennydreadfulmagic.com/decks/269604/) |
| Enchantments Matter | no guess | on | 31 | [270040](https://pennydreadfulmagic.com/decks/270040/), [270134](https://pennydreadfulmagic.com/decks/270134/), [270139](https://pennydreadfulmagic.com/decks/270139/) |
| Azorius Tempo | no guess | on | 31 | [270121](https://pennydreadfulmagic.com/decks/270121/), [270183](https://pennydreadfulmagic.com/decks/270183/), [270220](https://pennydreadfulmagic.com/decks/270220/) |
