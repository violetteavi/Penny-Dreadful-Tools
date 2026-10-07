# Card encoders: pros and cons

Ticket #7. The exploratory work is preserved on the branch `card-encoder` and the tag [`card-encoder-exploration`](https://github.com/violetteavi/Penny-Dreadful-Tools/tree/card-encoder-exploration): the experiment script [`experiments/card_encoders.py`](https://github.com/violetteavi/Penny-Dreadful-Tools/blob/card-encoder-exploration/archetype_classifier/experiments/card_encoders.py) and the results of every stage, [`docs/experiments/2026100{5,6}_card_encoders_stage*.json`](https://github.com/violetteavi/Penny-Dreadful-Tools/tree/card-encoder-exploration/archetype_classifier/docs/experiments). The cleaned-up code (`card_embeddings/`) keeps potion-base-8M, the base and masked text formats, the card numbers, and exact and average thirds.

The reports, with each one's results file beside it under the same name, are in the OneDrive folder and `archetype_classifier/reports/`:
- `20261005_Card_Embeddings_Architecture` (design)
- `20261005_Card_Encoders_Stage_1` (encoders)
- `20261005_Card_Encoders_Stage_2` (text formats)
- `20261005_Card_Encoders_Stage_2b`, `_2c` (structured vectors)
- `20261006_Card_Encoders_Stage_2d`, `_2e` (exact and average thirds)

## What was tested

How to represent a card so that cards that play alike are close together, including cards no deck has played yet. The deck classifier (#35) will build on whatever is chosen here.

| | |
|---|---|
| Ever-legal cards | Every card ever legal in Penny Dreadful: **25,331**, keyed by the site's names. One legal name, "With Great Power...", was renamed on Scryfall and is skipped with a warning. |
| Judged by | Neighbour lists (each card's 10 nearest among all ever-legal cards) read by the user, and ranks on checks the user chose. Seized from Slumber's reprints and Swift Response, Shock ↔ Burst Lightning, Shivan Fire / Roil Eruption, the vanilla Beasts, Lightning Strike ↔ Searing Spear / Open Fire / Explosive Welcome, Kalonian Tusker ↔ Werewolf Pack Leader / Jibbirik Omnivore, Eater of Virtue ↔ Bonesplitter, Leaf Gilder ↔ Llanowar Elves. |
| Not yet judged by | Any deck-level measure. That is #36 (cards) and #35 (decks). |

**Stages:**
1. **Encoders:** five frozen text encoders on the base format (type line and Scryfall rules text).
2. **Text formats:** base, JSON, JSON with masking, cost and stats in the text, inline labels; on potion and bge-base.
3. **2b and 2c:** the text plus a standardised structured vector of the card's numbers, weighted by α. 2b used the base text and 2c the masked text.
4. **2d and 2e:** the text plus the card's numbers with **mana value, colour and stats each a third**. Exact thirds (2d) compares the groups separately; average thirds (2e) uses one scaled vector.

## Results

### Encoders (stage 1)

| Encoder | Parameters | Dimensions | 24,870 older cards | New set (461 cards) | User's reading |
|---|---|---|---|---|---|
| **potion-base-8M** (static) | 7.6M | 256 | **3 s** | 0.1 s | **among the best** |
| all-MiniLM-L6-v2 | ~22M | 384 | 205 s | 5.7 s | |
| bge-small-en-v1.5 | 33.4M | 384 | 405 s | 12.5 s | |
| **bge-base-en-v1.5** | 109.5M | 768 | 1,482 s | 37.5 s | **among the best** |
| gte-modernbert-base | ~149M | 768 | ~4 h (574 ms per card) | — | dropped: too slow on CPU |

- **Adding a set never re-embeds older cards.** Embedding cards in a different batch moves any vector by at most 1.3e-7; the agreed tolerance is 1e-5.
- **No card runs past any encoder's token limit** in the base format.

### Text formats (stage 2)

Shock ↔ Burst Lightning ranks:

| Format | potion | bge-base |
|---|---|---|
| base | #47 / #77 | #184 / #406 |
| stats (cost and stats in the text) | **#18 / #55** | #212 / #233 |
| labels | #39 / #55 | #878 / #180 |
| json | #451 / #83 | #2368 / #3107 |

- **JSON hurts both encoders.** The braces and field names are the same in every card, so they pull every card towards every other.
- **Masking the card's own name** (`~`) is what makes Lightning Strike and Searing Spear identical: rank #22 becomes 1.000.
- **We chose not to write cost and stats into the text.** The numbers are handled separately.

### Numbers (stages 2b to 2e), potion, masked text

| Check | Masked text alone | Exact thirds @ 0.5 | Average thirds @ 0.5 |
|---|---|---|---|
| Searing Spear / Open Fire for Lightning Strike | #2 / #1 (tied) | **#1 / #2** | **#1** / #7 (Shock #2) |
| Explosive Welcome for Lightning Strike (should fall) | #65 | #203 | **#7663** |
| Jibbirik Omnivore / Werewolf Pack Leader for Kalonian Tusker | #10 / #2158 | #1 / #21 | **#1 / #10** |
| Shivan Fire / Roil Eruption for Burst Lightning | #1 / #2 | #1 / #4 | #1 / #3 |
| Shock ↔ Burst Lightning | #204 / #159 | #47 / #24 | **#41 / #22** |
| Leaf Gilder for Llanowar Elves | #4 | #11 | **#5** |
| Swift Response for Seized from Slumber | #16 | **#21** | #5845 |
| Bonesplitter for Eater of Virtue | #1113 | **#72** | #108 |

An unweighted standardised vector (2b, 2c) let rare yes/no columns dominate: mana value made up only 5–8% of it. Splitting the numbers into thirds fixed that.

## Pros

- **Potion is fast enough to change our minds cheaply.** It embeds every ever-legal card in about 3 seconds and a new set in a tenth of a second. That makes it practical to re-embed on every rotation, or every time the text format changes, and it matches bge-base on the user's reading of the lists.
- **New cards land next to what they do.** Unseen cards sit near the cards they resemble, and adding a set leaves every existing vector unchanged (checked to 1.3e-7). That's the property the similarity baseline lacked (#6).
- **Masking makes functional reprints identical** even when the text names the card (Lightning Strike / Searing Spear); reprints that don't name themselves were already identical (Seized from Slumber's group, the elves).
- **The numbers now count.** With mana value, colour and stats each a third of the structured similarity, cost differences that the text misses show up:
  - Explosive Welcome falls away from Lightning Strike.
  - Fireball no longer looks like Shock.
  - Searing Spear rises above Open Fire.
  - Bonesplitter rises from #1113 to #72–108.
- **Everything structural is frozen and versioned:** model revisions are pinned, `TEXT_VERSION` is recorded, and the standardisation and centring statistics are fitted once. A new set can be added without moving anything already embedded.
- **The pieces are tested and reusable:** each module of `card_embeddings/` is at 100% branch coverage, with checks on real cards. Neighbour search works from any similarity, and a command-line tool shows any card's neighbours.

## Cons

- **The evidence so far is a handful of cards read by eye.** About ten checks and the user's reading of 20–40 lists. Nothing yet measures whether these similarities help classify decks. #36 (cards) and #35 (decks) have to confirm it.
- **Exact against average thirds is still open:**
  - **Average thirds** reads better on several checks (Shock ↔ Burst Lightning, Werewolf Pack Leader, Leaf Gilder, Explosive Welcome). But Swift Response collapses to #5845, because a single cosine punishes the 2-against-5 mana value gap too hard and can't apply "compare only when the flags match".
  - **Exact thirds** applies the rules directly, but is softer on mana value.
- **α is a dial set by eye.** The text's cosine spans only about 0.56–0.89 across a card's top 10, while the numbers span 0–1. So α doesn't mean "share of the decision", and the best value (about 0.4–0.6) was chosen by reading lists.
- **Ties remain where text and numbers both agree.** Eater of Virtue's numbers match every colourless 1-mana artifact without stats. Every land scores 1 against every other land on the numbers. Only the text separates them.
- **Masking costs Shock ↔ Burst Lightning in the text alone** (#47 / #77 with base text, #204 / #159 masked), because names had been doing some of the work. The numbers win most of it back.
- **Back faces only count through the text.** Front faces only, with split cards summed, is the rules' answer, not necessarily the best one (#40).
- **Defense is missing:** the cards import drops it (#38).

## What #35 should build on

1. **potion-base-8M on the masked text format,** embedded once per set and merged in.
2. **The card's numbers alongside it,** each group a third: exact thirds or average thirds, at α around 0.5. Choosing between them, and tuning the group weights, is best done against a deck-level measure rather than more card lists.
3. **#36 first:** whether the structured numbers help, measured on cards, and whether produced mana, keywords or subtypes should join them.
4. **#41 first too:** extract the representation builder and the card checks from the archived experiment script into tested library code, so #35 loads the card representation instead of rebuilding it.

## Caveats

- **The ranks are over all 25,331 ever-legal cards,** across every season. They're stricter than a single season's legal cards, which the command-line tool's `--season` shows.
- **The checks were chosen to probe known weaknesses,** so they aren't a random sample of cards.
- **The test seasons (40–42) were never used.** Nothing here touched deck labels.
