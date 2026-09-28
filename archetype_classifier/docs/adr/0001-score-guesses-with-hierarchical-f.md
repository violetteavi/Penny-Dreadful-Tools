---
status: accepted
---

# Score guesses with hierarchical F (β = 1), reporting precision and recall beside it

Guesses are scored against the archetype tree with the hierarchical precision (hP), recall (hR) and F-measure of Kiritchenko, Matwin & Famili (2005, §3.3, "Functional Annotation of Genes Using Hierarchical Text Categorization"): expand the guess and the label to the archetype plus its ancestors (not the root), micro-average over decks, and combine as hF_β = (β² + 1)·hP·hR / (β²·hP + hR). We use β = 1, as the paper did, with hP and hR always reported alongside, rather than tree distance, lowest-shared-ancestor height or a tuned β. Tree distance and ancestor height can't tell a too-specific guess from a parent fallback. A β below 1 would build the Tentative "too-specific guesses are penalised" scenario into the headline number, but that scenario isn't settled, and a stronger penalty risks rewarding guesses that retreat to top-level archetypes. For now, the too-specific penalty shows up only as lower hP.

## Considered options

- **β = 0.8.** This keeps every scenario true in the headline number (parent fallback 0.837 > too-specific 0.766 > wrong child 0.667 > top-level fallback 0.562, for Prisoner / Red Deck Wins examples). It's the documented alternative if the too-specific scenario becomes firm. Below about β = 0.58, a top-level fallback would outscore a wrong child on the right branch, which contradicts a Confirmed scenario.

## Consequences

- Changing the metric or β later means re-scoring every earlier result, including the baseline, before comparing.
- Each model's headline is reported at the parent-fallback threshold that maximises micro hF on the validation season, fixed before the test seasons are scored. A curve of hP against hR over all thresholds goes with it.
- The full reporting plan (results table rows, macro averaging, exact-match rate, depth difference) is recorded in the resolution of [How should predictions be scored against the archetype tree?](https://github.com/violetteavi/Penny-Dreadful-Tools/issues/5).
