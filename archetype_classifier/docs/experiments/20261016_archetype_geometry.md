# Archetype geometry

#64 (Archetype geometry: typical lists, defining cards and analogies in the deck-vector space). PRs: #65. Nothing is tuned. Full tables and figure data are next to the results PDF.

## Provenance

| | run 17 | run 14 |
|---|---|---|
| run | `17` | `14` |
| model | `17` | `14` |
| name | `embedding nearest deck` | `embedding nearest deck` |
| version | `4` | `4` |
| params | `{'copies': 'sqrt', 'embedding': 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39', 'weights': 'idf'}` | `{'embedding': 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39'}` |
| snapshot | `1` | `1` |
| scheme | `3` | `3` |
| identity hash | `010e60c099c37adc004a5889a061d2ab67e1a7e2` | `cc3c7702f71ec408825e027e80beee6d2c587b05` |
| embedding hash | `3168bf8be50e24653c59ec118af99cbd99235ea96a1ea5d4580f8028062bda5a` | `3168bf8be50e24653c59ec118af99cbd99235ea96a1ea5d4580f8028062bda5a` |
| card weights hash | `2a2377a012a1d7001fd424156cca9d367a8e7db0` | `None` |
| training decks | `162869` | `162869` |
| training fingerprint | `94024d074aaaf87c6796e491e6c26aaf3c8320b8` | `94024d074aaaf87c6796e491e6c26aaf3c8320b8` |
| training rows | `84085` | `84085` |

## Overview

| | run 17 | run 14 |
|---|---|---|
| Archetypes with a centroid | 485 | 485 |
| Below the floor (rows) | 58 (284) | 58 (284) |
| Median cohesion | 0.956 | 0.971 |
| Rows nearer another centroid | 0.382 | 0.377 |
| Spearman: overlap vs season 39 Top 1 (archetypes with 10+ decks) | -0.51 (p = 0.000, 56 archetypes) | -0.52 (p = 0.000, 56 archetypes) |
| Parent-labelled rows: between / one child / elsewhere | 1200/3307/10023 | 1396/3504/9630 |
| Strategy analogies: count | 132 | 132 |
| Pair analogies: count | 296 | 296 |
| Strategy analogies: median offset cosine (median percentile) | 0.770 (0.998) | 0.769 (0.998) |
| Pair analogies: median offset cosine (median percentile) | 0.133 (0.631) | 0.071 (0.550) |
| Strategy analogies: share ranked 1 by 3CosAdd / 3CosMul / only-b | 0.61/0.58/0.04 | 0.67/0.65/0.08 |
| Pair analogies: share ranked 1 by 3CosAdd / 3CosMul / only-b | 0.22/0.20/0.23 | 0.21/0.20/0.27 |
| Strategy analogies: share where the offset beats only-b (3CosMul rank < only-b rank) | 0.87 | 0.85 |
| Pair analogies: share where the offset beats only-b (3CosMul rank < only-b rank) | 0.33 | 0.32 |

## Curated archetypes (run 17)

| Archetype | Rows | Cohesion | Typical list | Nearest centroid | Overlap | Season 39 Top 1 | Cohesion, run 14 |
|---|---|---|---|---|---|---|---|
| Orzhov Control | 464 | 0.9578 | [268891](https://pennydreadfulmagic.com/decks/268891/) | Combo Post 0.9483 | 0.26 | 0.92 (24) | 0.9775 |
| Orzhov Midrange | 914 | 0.9339 | [209765](https://pennydreadfulmagic.com/decks/209765/) | Orzhov Blink 0.9833 | 0.57 | 0.71 (24) | 0.9608 |
| Mono Black Midrange | 719 | 0.9458 | [166845](https://pennydreadfulmagic.com/decks/166845/) | Mono Black Devotion 0.986 | 0.65 | 0.50 (6) | 0.9753 |
| Mono Black Control | 263 | 0.9407 | [118281](https://pennydreadfulmagic.com/decks/118281/) | Demonic Rising 0.9536 | 0.25 | 0.60 (5) | 0.9709 |
| Izzet Control | 379 | 0.9557 | [260323](https://pennydreadfulmagic.com/decks/260323/) | Dynavolt Tower 0.9795 | 0.41 | 1.00 (20) | 0.9762 |
| Izzet Twin | 174 | 0.9794 | [240007](https://pennydreadfulmagic.com/decks/240007/) | Izzet Control 0.9725 | 0.04 | 0.14 (21) | 0.9883 |
| Applejacks | 138 | 0.9219 | [169194](https://pennydreadfulmagic.com/decks/169194/) | Gruul Midrange 0.9831 | 0.59 | 0.06 (17) | 0.9594 |
| Lumbertwin | 50 | 0.9887 | [267350](https://pennydreadfulmagic.com/decks/267350/) | Applejacks 0.9528 | 0.02 | 0.17 (6) | 0.9953 |
| Izzet Tempo | 1186 | 0.9647 | [171705](https://pennydreadfulmagic.com/decks/171705/) | Izzet Dreadnought 0.9784 | 0.35 | 0.26 (19) | 0.9782 |
| Polymorph | 253 | 0.9068 | [184979](https://pennydreadfulmagic.com/decks/184979/) | Combo-Control 0.975 | 0.79 | 0.06 (16) | 0.9413 |
| Actual Twin | 17 | 0.8920 | [266822](https://pennydreadfulmagic.com/decks/266822/) | Midrange 0.9652 | 0.94 | 0.00 (13) | 0.9244 |
| Temur Ascendancy | 52 | 0.9247 | [130091](https://pennydreadfulmagic.com/decks/130091/) | Gruul Midrange 0.9568 | 0.29 | 0.07 (15) | 0.9505 |
| Dimir Midrange | 542 | 0.9336 | [116671](https://pennydreadfulmagic.com/decks/116671/) | Dimir Tempo 0.9628 | 0.54 | 0.43 (23) | 0.9640 |
| Equipment Aggro | 192 | 0.9382 | [235932](https://pennydreadfulmagic.com/decks/235932/) | Boros Aggro 0.9498 | 0.23 | 0.94 (94) | 0.9572 |
| Red Deck Wins | 2182 | 0.9655 | [243455](https://pennydreadfulmagic.com/decks/243455/) | Mono Red Swarm 0.9727 | 0.23 | 1.00 (70) | 0.9790 |
| Azorius Control | 2225 | 0.9673 | [207174](https://pennydreadfulmagic.com/decks/207174/) | Azorius Cloudpost Control 0.9756 | 0.25 | 0.93 (73) | 0.9817 |
| Esper Control | 1032 | 0.9606 | [175823](https://pennydreadfulmagic.com/decks/175823/) | Combo-Control 0.9728 | 0.34 | 1.00 (16) | 0.9743 |
| Dimir Control | 1063 | 0.9576 | [225246](https://pennydreadfulmagic.com/decks/225246/) | Zur's Weirding 0.9908 | 0.48 | – | 0.9753 |
| Burn | 817 | 0.9211 | [82697](https://pennydreadfulmagic.com/decks/82697/) | Devastating Dreams 0.9519 | 0.46 | 0.75 (4) | 0.9496 |
| White Weenie | 567 | 0.9547 | [151949](https://pennydreadfulmagic.com/decks/151949/) | Mono White Humans 0.9898 | 0.39 | – | 0.9699 |
| Aristocrats | 107 | 0.9077 | [156009](https://pennydreadfulmagic.com/decks/156009/) | Aggro 0.9774 | 0.79 | 0.00 (2) | 0.9374 |
| Mono Black Aristocrats | 275 | 0.9593 | [120242](https://pennydreadfulmagic.com/decks/120242/) | Heartless Summoning Combo 0.968 | 0.33 | 0.50 (6) | 0.9731 |
| Orzhov Aristocrats | 295 | 0.9486 | [126648](https://pennydreadfulmagic.com/decks/126648/) | Mardu Aristocrats 0.9715 | 0.30 | – | 0.9654 |
| Golgari Aristocrats | 135 | 0.9420 | [117074](https://pennydreadfulmagic.com/decks/117074/) | Abzan Aristocrats 0.9654 | 0.46 | – | 0.9613 |
| Abzan Aristocrats | 81 | 0.9430 | [139345](https://pennydreadfulmagic.com/decks/139345/) | Golgari Aristocrats 0.9654 | 0.46 | 0.00 (2) | 0.9576 |
| Mardu Aristocrats | 37 | 0.9404 | [212904](https://pennydreadfulmagic.com/decks/212904/) | Orzhov Aristocrats 0.9715 | 0.46 | – | 0.9590 |
| Rakdos Aristocrats | 463 | 0.9664 | [241565](https://pennydreadfulmagic.com/decks/241565/) | Rakdos Aggro 0.971 | 0.18 | 1.00 (1) | 0.9770 |
| Squirrel Aristocrats | 68 | 0.9585 | [262674](https://pennydreadfulmagic.com/decks/262674/) | Varolz Dreadnought 0.9699 | 0.34 | 0.06 (17) | 0.9704 |

## Defining cards and pushes (run 17)

Top 5 by z (log-odds in brackets) against all other rows and against siblings; the largest centroid pushes against siblings, and the most negative.

**Orzhov Control**

- All rows: Abstruse Appropriation 45.9 (6.13), Kaya, Ghost Assassin 44.4 (4.72), Kaya's Guile 43.9 (5.09), Phyrexian Arena 43.5 (4.47), Shambling Vent 41.4 (4.25)
- Siblings: Kaya, Ghost Assassin 38.3 (4.37), Shambling Vent 36.9 (4.04), Caves of Koilos 34.6 (3.61), Fetid Heath 34.3 (3.72), Isolated Chapel 33.8 (3.58)
- Pushes: Kaya, Ghost Assassin 0.0400, Vindicate 0.0290, Abstruse Appropriation 0.0257, Kaya's Guile 0.0244, Phyrexian Arena 0.0175 (of 0.4151; most negative: Braids, Cabal Minion -0.0010, Decree of Justice -0.0011, Doom Foretold -0.0012)

**Orzhov Midrange**

- All rows: Tidehollow Sculler 60.7 (4.43), Wasteland Strangler 53.8 (4.46), Shambling Vent 53.4 (3.72), Vindicate 51.0 (4.16), Isolated Chapel 49.5 (3.47)
- Siblings: Tidehollow Sculler 41.9 (3.24), Vindicate 39.5 (3.32), Shambling Vent 38.9 (2.88), Isolated Chapel 36.8 (2.69), Wasteland Strangler 35.6 (3.15)
- Pushes: Tidehollow Sculler 0.0394, Vindicate 0.0362, Wasteland Strangler 0.0189, Kunoros, Hound of Athreos 0.0154, Kambal, Consul of Allocation 0.0113 (of 0.3132; most negative: Caves of Koilos -0.0013, Hero of Precinct One -0.0013, Gatekeeper of Malakir -0.0021)

**Mono Black Midrange**

- All rows: Gatekeeper of Malakir 50.6 (4.00), Hypnotic Specter 45.7 (3.86), Lashwrithe 40.6 (5.21), Dark Ritual 39.8 (3.30), Demigod of Revenge 37.8 (3.96)
- Siblings: Gatekeeper of Malakir 40.8 (3.85), Dark Ritual 40.7 (3.61), Hypnotic Specter 32.2 (2.99), Sign in Blood 29.9 (2.74), Vampire Nighthawk 28.1 (2.79)
- Pushes: Gatekeeper of Malakir 0.0383, Vampire Nighthawk 0.0288, Sign in Blood 0.0286, Hypnotic Specter 0.0219, Dark Ritual 0.0209 (of 0.5125; most negative: Vindicate -0.0035, Lashwrithe -0.0054, Swamp -0.0214)

**Mono Black Control**

- All rows: Mutilate 42.9 (6.09), Corrupt 35.1 (6.88), Cabal Stronghold 33.6 (4.91), Sign in Blood 29.8 (3.72), Underworld Connections 25.8 (3.91)
- Siblings: Mutilate 30.9 (5.56), Sign in Blood 27.9 (3.75), Cabal Stronghold 24.0 (5.32), Dark Ritual 20.3 (2.59), Underworld Connections 20.2 (3.37)
- Pushes: Mutilate 0.0349, Sign in Blood 0.0170, Corrupt 0.0137, Underworld Connections 0.0107, Korlash, Heir to Blackblade 0.0106 (of 0.5549; most negative: Snow-Covered Swamp -0.0027, Cabal Stronghold -0.0083, Swamp -0.0167)

**Izzet Control**

- All rows: Invert Polarity 37.4 (4.74), Ill-Timed Explosion 33.0 (4.35), Sulfur Falls 32.3 (3.36), Electrolyze 30.6 (3.54), Shivan Reef 30.6 (3.21)
- Siblings: Shivan Reef 31.0 (3.71), Sulfur Falls 30.3 (3.40), Burst Lightning 27.8 (3.04), Invert Polarity 27.0 (4.14), Wandering Fumarole 26.7 (3.47)
- Pushes: Invert Polarity 0.0247, Electrolyze 0.0185, Ill-Timed Explosion 0.0153, Burst Lightning 0.0133, Aether Spike 0.0093 (of 0.3804; most negative: Mystical Teachings -0.0010, Pillage -0.0016, Stone Rain -0.0017)

**Izzet Twin**

- All rows: Cascade Bluffs 32.1 (6.67), Pestermite 31.3 (8.94), Deduce 30.6 (4.79), Invert Polarity 29.7 (4.92), Roaring Furnace // Steaming Sauna 28.9 (5.53)
- Siblings: Sulfur Falls 10.2 (3.96), Shivan Reef 9.6 (3.05), Mana Leak 9.5 (2.99), Memory Lapse 9.3 (4.69), Cascade Bluffs 9.2 (2.82)
- Pushes: Pestermite 0.0378, Memory Lapse 0.0367, Scrapshooter 0.0323, Bristlebud Farmer 0.0300, Hyrax Tower Scout 0.0267 (of 0.6023; most negative: Forest -0.0072, Copperline Gorge -0.0079, Karplusan Forest -0.0095)

**Applejacks**

- All rows: Titania, Protector of Argoth 30.6 (5.84), Sheltered Thicket 20.5 (3.59), Quartzwood Crasher 19.8 (6.02), Game Trail 19.5 (3.59), Flare of Cultivation 19.5 (4.74)
- Siblings: Titania, Protector of Argoth 15.8 (4.71), Sheltered Thicket 15.2 (3.15), Game Trail 14.5 (4.40), Glorybringer 12.8 (3.54), Burst Lightning 11.4 (2.94)
- Pushes: Orcish Lumberjack 0.0762, Fanatic of Xenagos 0.0136, Generator Servant 0.0134, Cloudpost 0.0134, Glimmerpost 0.0127 (of 0.4285; most negative: Rofellos, Llanowar Emissary -0.0068, Game Trail -0.0070, Mountain -0.0073)

**Lumbertwin**

- All rows: Trumpeting Carnosaur 25.0 (8.20), Tranquil Frillback 24.0 (7.24), Hyrax Tower Scout 23.0 (9.32), Scrapshooter 22.6 (8.73), Monoist Sentry 20.8 (7.15)
- Siblings: Combat Celebrant 8.3 (7.26), Copperline Gorge 7.9 (7.96), Karplusan Forest 7.0 (8.68), Bristlebud Farmer 7.0 (7.93), Fanatic of Rhonas 7.0 (8.66)
- Pushes: Bristlebud Farmer 0.0632, Scrapshooter 0.0630, Hyrax Tower Scout 0.0514, Combat Celebrant 0.0417, Fanatic of Rhonas 0.0386 (of 0.7629; most negative: Thran Portal -0.0110, Copperline Gorge -0.0123, Karplusan Forest -0.0146)

**Izzet Tempo**

- All rows: Sprite Dragon 76.4 (6.02), Delver of Secrets 66.8 (4.30), Wandering Fumarole 52.2 (3.59), Chain Lightning 45.2 (2.73), Burst Lightning 45.1 (2.75)
- Siblings: Sprite Dragon 41.4 (4.44), Burst Lightning 36.5 (3.13), Chain Lightning 36.1 (3.49), Mountain 34.7 (3.39), Delver of Secrets 26.2 (1.86)
- Pushes: Burst Lightning 0.0312, Chain Lightning 0.0276, Sprite Dragon 0.0238, Spikefield Hazard 0.0144, Mountain 0.0108 (of 0.2751; most negative: Tolarian Terror -0.0030, Desperate Ravings -0.0039, Treasure Cruise -0.0068)

**Polymorph**

- All rows: Shape Anew 31.4 (6.87), Hard Evidence 30.9 (4.61), Polymorph 26.9 (9.63), Darksteel Colossus 26.5 (4.16), Transmogrify 21.0 (7.73)
- Siblings: Hard Evidence 23.2 (5.03), Shape Anew 18.3 (6.31), Darksteel Colossus 17.7 (2.88), Lose Focus 15.9 (2.66), Mana Leak 13.8 (1.93)
- Pushes: Polymorph 0.0438, Shape Anew 0.0175, Hard Evidence 0.0128, Raise the Alarm 0.0109, Intangible Virtue 0.0095 (of 0.2936; most negative: Jeskai Ascendancy -0.0022, Turnabout -0.0041, Frantic Search -0.0062)

**Actual Twin**

- All rows: Summon: G.F. Ifrit 12.9 (8.52), Combat Celebrant 12.5 (6.36), Mordor on the March 12.5 (9.47), Infernal Plunge 11.7 (5.86), Charming Scoundrel 11.5 (5.79)
- Siblings: Charming Scoundrel 10.9 (6.80), Restoration Angel 10.6 (4.97), Pestermite 10.2 (6.19), Combat Celebrant 10.1 (7.65), Summon: G.F. Ifrit 9.5 (7.40)
- Pushes: Kiki-Jiki, Mirror Breaker 0.0382, Restoration Angel 0.0226, Pestermite 0.0114, Combat Celebrant 0.0113, Nest Invader 0.0112 (of 0.3258; most negative: Simian Spirit Guide -0.0034, Ripples of Undeath -0.0043, Smiting Helix -0.0047)

**Temur Ascendancy**

- All rows: Savage Knuckleblade 22.0 (7.55), Crater's Claws 21.1 (7.47), Woodland Wanderer 20.9 (6.71), Saproling Burst 19.4 (5.87), Frontier Bivouac 16.7 (4.57)
- Siblings: Frontier Bivouac 18.8 (5.65), Woodland Wanderer 16.5 (5.68), Flametongue Kavu 14.0 (4.23), Crater's Claws 13.9 (7.41), Saproling Burst 13.9 (7.41)
- Pushes: Temur Ascendancy 0.0875, Woodland Wanderer 0.0297, Savage Knuckleblade 0.0261, Saproling Burst 0.0241, Crater's Claws 0.0137 (of 0.5216; most negative: Silverquill Silencer -0.0017, Tectonic Giant -0.0017, Swamp -0.0018)

**Dimir Midrange**

- All rows: Thief of Sanity 42.0 (4.59), Temple of Deceit 32.6 (3.20), Drowned Catacomb 32.2 (2.80), Hostage Taker 28.7 (3.30), Jorubai Murk Lurker 26.5 (5.28)
- Siblings: Drowned Catacomb 37.7 (3.74), Temple of Deceit 30.1 (4.34), Thief of Sanity 30.0 (4.28), Mana Leak 25.5 (2.78), Choked Estuary 25.3 (4.07)
- Pushes: Thief of Sanity 0.0277, Hostage Taker 0.0117, Thought Erasure 0.0117, Master of Death 0.0104, Memory Lapse 0.0086 (of 0.3810; most negative: Asylum Visitor -0.0009, Nevermaker -0.0009, Sign in Blood -0.0018)

**Equipment Aggro**

- All rows: Kemba, Kha Enduring 30.2 (6.80), Stone Haven Outfitter 30.1 (7.70), Goblin Gaveleer 29.9 (6.10), Kor Duelist 29.5 (7.58), Fervent Champion 29.4 (4.83)
- Siblings: Mountain 12.9 (2.74), Clifftop Retreat 10.1 (3.29), Battlefield Forge 9.6 (2.09), Sword of Fire and Ice 6.0 (3.19), Champion of the Flame 5.6 (3.41)
- Pushes: Ethereal Armor 0.0140, Hateful Eidolon 0.0123, Dead Weight 0.0121, Mire's Grasp 0.0119, Akiri, Fearless Voyager 0.0111 (of 0.4891; most negative: Illuminator Virtuoso -0.0010, Knight of Grace -0.0013, Favored Hoplite -0.0015)

**Red Deck Wins**

- All rows: Stromkirk Noble 90.3 (5.44), Incinerate 90.0 (4.76), Barbarian Ring 83.8 (4.34), Earthshaker Khenra 72.0 (6.07), Kumano Faces Kakkazan 67.3 (4.62)
- Siblings: Burst Lightning 62.5 (4.25), Incinerate 61.9 (4.57), Stromkirk Noble 58.1 (4.76), Barbarian Ring 56.0 (3.74), Chain Lightning 55.8 (2.99)
- Pushes: Incinerate 0.0434, Burst Lightning 0.0335, Stromkirk Noble 0.0235, Chain Lightning 0.0218, Ash Zealot 0.0211 (of 0.4917; most negative: Drannith Stinger -0.0032, Spark Spray -0.0032, Lightning Rift -0.0036)

**Azorius Control**

- All rows: Dream Trawler 79.2 (4.01), Glacial Fortress 77.9 (3.84), Azorius Charm 77.5 (4.48), Condemn 77.4 (3.65), Wrath of God 72.6 (3.54)
- Siblings: Glacial Fortress 55.9 (3.11), Dream Trawler 49.6 (3.17), Azorius Charm 46.6 (3.42), Condemn 43.5 (2.22), Oust 40.8 (2.26)
- Pushes: Azorius Charm 0.0223, Glacial Fortress 0.0118, Fact or Fiction 0.0111, Dream Trawler 0.0108, Lose Focus 0.0097 (of 0.3091; most negative: Mountain -0.0018, Drowned Catacomb -0.0019, Swamp -0.0037)

**Esper Control**

- All rows: Esper Charm 64.0 (6.50), Arcane Sanctum 58.2 (4.30), Lochmere Serpent 49.5 (3.45), Glacial Fortress 48.6 (3.17), Drowned Catacomb 46.2 (2.97)
- Siblings: Arcane Sanctum 39.5 (3.87), Drowned Catacomb 35.3 (2.43), Esper Charm 32.9 (6.36), Lochmere Serpent 31.7 (2.39), Glacial Fortress 30.2 (2.04)
- Pushes: Esper Charm 0.0322, Arcane Sanctum 0.0148, Drowned Catacomb 0.0146, Glacial Fortress 0.0135, Psychic Strike 0.0119 (of 0.1997; most negative: Cloudpost -0.0025, Mountain -0.0035, Forest -0.0036)

**Dimir Control**

- All rows: Lochmere Serpent 54.3 (3.68), Drowned Catacomb 50.6 (3.30), Nephalia Drownyard 47.6 (3.86), Forbid 45.8 (2.90), Temple of Deceit 42.9 (3.20)
- Siblings: Drowned Catacomb 40.2 (2.81), Lochmere Serpent 35.9 (2.67), Temple of Deceit 32.7 (3.31), Nephalia Drownyard 31.2 (2.99), Fetid Pools 30.6 (2.50)
- Pushes: Forbid 0.0105, Master of Death 0.0102, Lochmere Serpent 0.0102, Drown in the Loch 0.0078, Tainted Indulgence 0.0071 (of 0.3136; most negative: Braids, Cabal Minion -0.0009, Damn -0.0010, Esper Charm -0.0013)

**Burn**

- All rows: Tyrant's Choice 53.9 (5.74), Bump in the Night 52.4 (5.32), Ghitu Lavarunner 49.5 (4.57), Barbarian Ring 48.7 (3.59), Shard Volley 46.9 (5.22)
- Siblings: Chain Lightning 36.9 (3.72), Burst Lightning 33.6 (3.23), Barbarian Ring 25.7 (4.72), Mountain 22.7 (2.09), Incinerate 21.9 (5.26)
- Pushes: Incinerate 0.0216, Chain Lightning 0.0195, Burst Lightning 0.0172, Flame Rift 0.0170, Shard Volley 0.0149 (of 0.4326; most negative: Ponder -0.0015, Chancellor of the Dross -0.0018, Goblin Bombardment -0.0064)

**White Weenie**

- All rows: Honor of the Pure 53.0 (4.96), Benalish Marshal 50.7 (4.81), Brave the Elements 49.7 (4.44), Dryad Militant 46.6 (4.09), Precinct Captain 42.7 (4.75)
- Siblings: Honor of the Pure 39.9 (3.91), Brave the Elements 37.0 (3.55), Dryad Militant 37.0 (3.52), Benalish Marshal 35.8 (3.63), Precinct Captain 28.9 (4.57)
- Pushes: Benalish Marshal 0.0356, Honor of the Pure 0.0283, Precinct Captain 0.0223, Brave the Elements 0.0153, Dryad Militant 0.0121 (of 0.4847; most negative: Tempered Steel -0.0023, Drannith Healer -0.0028, Plains -0.0100)

**Aristocrats**

- All rows: Melira, Sylvok Outcast 26.8 (5.57), Goblin Bombardment 25.1 (4.92), Safehold Elite 23.6 (5.34), Viscera Seer 19.2 (4.04), Murderous Redcap 18.7 (4.09)
- Siblings: Goblin Bombardment 17.1 (3.70), Melira, Sylvok Outcast 15.3 (5.20), Viscera Seer 13.3 (5.20), Birds of Paradise 11.6 (2.45), Safehold Elite 11.4 (5.66)
- Pushes: Melira, Sylvok Outcast 0.0158, Safehold Elite 0.0140, Slip Out the Back 0.0099, Gitaxian Probe 0.0083, Viscera Seer 0.0079 (of 0.3403; most negative: Hushwing Gryff -0.0038, Island -0.0052, Goblin Bombardment -0.0085)

**Mono Black Aristocrats**

- All rows: Ayara, First of Locthwain 40.6 (6.54), Blood Artist 38.1 (5.09), Cauldron Familiar 34.6 (4.48), Witch's Oven 34.4 (4.45), Grim Haruspex 32.8 (4.47)
- Siblings: Ayara, First of Locthwain 15.3 (3.77), Dark Ritual 13.0 (2.09), Barren Moor 11.7 (3.03), Undead Augur 9.9 (2.70), Gatekeeper of Malakir 9.7 (2.30)
- Pushes: Ayara, First of Locthwain 0.0292, Undead Augur 0.0144, Bastion of Remembrance 0.0123, Grim Haruspex 0.0105, Goblin Bombardment 0.0100 (of 0.3057; most negative: Judith, the Scourge Diva -0.0074, Barren Moor -0.0102, Swamp -0.0155)

**Orzhov Aristocrats**

- All rows: Cruel Celebrant 43.3 (7.03), Viscera Seer 37.3 (4.65), Rally the Ancestors 37.2 (5.29), Bloodthrone Vampire 36.8 (4.81), Doomed Traveler 36.8 (4.79)
- Siblings: Plains 19.1 (4.30), Cruel Celebrant 17.3 (3.82), Temple of Silence 16.5 (3.85), Isolated Chapel 16.5 (3.22), Doomed Traveler 13.4 (2.30)
- Pushes: Cruel Celebrant 0.0351, Rally the Ancestors 0.0160, Goblin Bombardment 0.0118, Anafenza, Kin-Tree Spirit 0.0102, Doomed Traveler 0.0096 (of 0.2720; most negative: Scoured Barrens -0.0020, Caves of Koilos -0.0022, Temple of Silence -0.0036)

**Golgari Aristocrats**

- All rows: Melira, Sylvok Outcast 32.4 (6.04), Viscera Seer 29.4 (5.24), Bloodthrone Vampire 27.2 (4.89), Zulaport Cutthroat 25.4 (4.77), Grim Haruspex 25.1 (4.58)
- Siblings: Melira, Sylvok Outcast 15.0 (3.97), Temple of Malady 14.1 (3.15), Woodland Cemetery 12.8 (2.70), Forest 12.4 (2.85), Murderous Redcap 11.3 (2.46)
- Pushes: Melira, Sylvok Outcast 0.0411, Goblin Bombardment 0.0123, Catacomb Sifter 0.0118, Viscera Seer 0.0085, Blisterpod 0.0079 (of 0.2240; most negative: Savvy Hunter -0.0025, Llanowar Wastes -0.0025, Chatterfang, Squirrel General -0.0033)

**Abzan Aristocrats**

- All rows: Rally the Ancestors 21.8 (5.16), Abzan Ascendancy 20.1 (6.58), Viscera Seer 20.0 (4.51), Sandsteppe Citadel 19.0 (4.28), Melira, Sylvok Outcast 19.0 (4.88)
- Siblings: Sandsteppe Citadel 12.3 (4.51), Sunpetal Grove 11.6 (4.10), Birds of Paradise 10.1 (2.41), Satyr Wayfinder 9.2 (2.92), Forest 9.1 (3.64)
- Pushes: Rally the Ancestors 0.0191, Sandsteppe Citadel 0.0132, Judith, the Scourge Diva 0.0111, Return to the Ranks 0.0107, Goblin Bombardment 0.0097 (of 0.2753; most negative: Dragonskull Summit -0.0051, Foreboding Ruins -0.0052, Swamp -0.0083)

**Mardu Aristocrats**

- All rows: Butcher of the Horde 17.6 (7.27), Cartel Aristocrat 16.2 (5.83), Judith, the Scourge Diva 15.0 (4.90), Doomed Traveler 14.0 (4.66), Tragic Slip 13.7 (5.15)
- Siblings: Battlefield Forge 10.0 (3.49), Nomad Outpost 9.7 (4.45), Secluded Courtyard 7.3 (3.90), Caves of Koilos 7.2 (2.38), Thraben Inspector 6.9 (2.47)
- Pushes: Butcher of the Horde 0.0240, Nomad Outpost 0.0119, Cartel Aristocrat 0.0098, Gather the Townsfolk 0.0076, Battlefield Forge 0.0075 (of 0.2047; most negative: Foreboding Ruins -0.0035, Xathrid Necromancer -0.0050, Swamp -0.0061)

**Rakdos Aristocrats**

- All rows: Judith, the Scourge Diva 54.9 (6.47), Goblin Bombardment 53.4 (5.70), Dreadhorde Butcher 48.5 (5.07), Bloodsoaked Champion 47.5 (4.94), Vraan, Executioner Thane 43.4 (5.97)
- Siblings: Mountain 22.1 (4.10), Dragonskull Summit 21.4 (4.32), Goblin Bombardment 20.9 (3.16), Judith, the Scourge Diva 20.2 (3.75), Graven Cairns 17.1 (4.89)
- Pushes: Goblin Bombardment 0.0320, Judith, the Scourge Diva 0.0311, Dreadhorde Butcher 0.0287, Bloodsoaked Champion 0.0168, Dread Wanderer 0.0110 (of 0.2969; most negative: Kami of False Hope -0.0019, Cauldron Familiar -0.0027, Viscera Seer -0.0043)

**Squirrel Aristocrats**

- All rows: Infestation Sage 26.0 (7.07), Vengeful Bloodwitch 25.8 (7.70), Spymaster's Vault 23.7 (5.84), Flare of Malice 22.5 (5.99), Argoth, Sanctum of Nature 22.1 (5.61)
- Siblings: Twilight Mire 15.1 (6.00), Vengeful Bloodwitch 12.4 (3.80), Spymaster's Vault 12.4 (3.40), Infestation Sage 11.8 (3.36), Chthonian Nightmare 11.0 (5.82)
- Pushes: Chatterfang, Squirrel General 0.0679, Llanowar Wastes 0.0318, Twilight Mire 0.0310, Hogaak, Arisen Necropolis 0.0242, Argoth, Sanctum of Nature 0.0204 (of 0.4075; most negative: Chthonian Nightmare -0.0105, Infestation Sage -0.0108, Vengeful Bloodwitch -0.0146)

## Named analogies

| Analogy | run 17: 3CosAdd / 3CosMul / only-b, offset (percentile) | run 14: 3CosAdd / 3CosMul / only-b, offset (percentile) |
|---|---|---|
| Orzhov Midrange : Orzhov Control :: Mono Black Midrange : Mono Black Control | 1 / 1 / 8, 0.865 (1.0) | 1 / 1 / 5, 0.810 (1.0) |
| Applejacks : Lumbertwin :: Izzet Control : Izzet Twin | 1 / 1 / 3, 0.374 (0.857) | 1 / 1 / 3, 0.231 (0.74) |
| Izzet Control : Izzet Twin :: Applejacks : Lumbertwin | 1 / 1 / 4, 0.374 (0.857) | 2 / 1 / 3, 0.231 (0.74) |

## Parent-labelled rows

| Parent | run 17: between / one child / elsewhere | run 14: between / one child / elsewhere |
|---|---|---|
| Red Deck Wins (2182 rows) | 23/511/1648 | 48/623/1511 |
| Midrange (1322 rows) | 82/204/1036 | 65/212/1045 |
| Affinity (1046 rows) | 1/163/882 | 2/233/811 |
| Combo (922 rows) | 90/205/627 | 92/190/640 |
| Mono Blue Tempo (731 rows) | 2/132/597 | 0/262/469 |
| Ramp (721 rows) | 94/265/362 | 149/238/334 |
| Mono Black Midrange (719 rows) | 281/145/293 | 280/134/305 |
| Dimir Tempo (714 rows) | 2/97/615 | 7/73/634 |
| White Weenie (567 rows) | 97/319/151 | 102/325/140 |
| Blink (561 rows) | 5/114/442 | 1/103/457 |
| Aggro-Control (477 rows) | 75/135/267 | 82/186/209 |
| Rofellos Ramp (342 rows) | 0/3/339 | 0/8/334 |
| Sultai Midrange (321 rows) | 1/7/313 | 0/12/309 |
| Storm (306 rows) | 33/137/136 | 68/117/121 |
| Aggro (294 rows) | 35/96/163 | 40/91/163 |
