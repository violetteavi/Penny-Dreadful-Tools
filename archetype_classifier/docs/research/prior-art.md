# Prior art: archetype classification, parent fallback and unseen cards

Research for issue #3. Compiled 2026-09-28. Findings only: this document does not recommend an approach, and no experiments were run.
Terms follow [CONTEXT.md](../../CONTEXT.md) (archetype tree, parent fallback, unseen card, guess, label).

## Summary

- **MTG sites do not publish their methods.** MTGGoldfish, MTGTop8 and Untapped.gg document nothing about how decks get an archetype. What you can see on the sites is still useful. MTGTop8 uses a two-level tree (Aggro / Control / Combo, then named archetypes) with "Other - Aggro/Control/Combo" buckets, which work like a parent fallback. 17lands classifies draft decks only by colour pair, and clusters decks within a pair for exploration.
- **The best-documented open MTG classifier is rules-first, like ours.** Badaro's MTGOArchetypeParser (MIT, used for MTGO metagame reports) works in three steps. First it applies hand-written include/exclude conditions. Then it tries "variants" of an archetype, and if no variant matches it returns the base archetype, which is a one-level parent fallback. Finally, "generic" archetypes (lists of common cards) catch decks that no rule matches, with a similarity floor of 0.1.
- **Probabilistic bag-of-cards classifiers are the usual statistical baseline.** Tierney (2018) used a Multinomial-Dirichlet model on 8,249 MTGGoldfish Modern decks and got about 80% correct, noting that it was over-confident. The MTGO_Tools project (2026) uses multinomial naive Bayes with an "Unknown" cutoff at posterior 0.8. For Hearthstone, the published work clusters decks (k-means, DBSCAN, fuzzy multisets) and compares the clusters with expert labels. HSReplay labels decks from per-archetype "core" and "popular" cards.
- **Hierarchical classification has standard names for what we want.** Silla & Freitas (2011) call it "non-mandatory leaf-node prediction". The usual top-down method stops when a node's confidence falls below a threshold. Its known failure is the "blocking problem": an early wrong stop can't be recovered. Since Ramaswamy et al. (2015), the principled version has been to add up probabilities over each subtree and pick the deepest node whose subtree probability clears a threshold (> 1/2 is Bayes-optimal for tree-distance loss). Deng et al. (2012) and Goren et al. (2024) turn that threshold into a guaranteed target accuracy. All of these work post hoc on any calibrated flat classifier.
- **The literature scores hierarchical predictions in three ways.** (a) Set-based hierarchical precision, recall and F (Kiritchenko et al.), which compare the ancestor sets of the prediction and of the label. A correct but shallower prediction gets full precision and partial recall. (b) Pair-based costs such as tree distance or lowest-common-ancestor (LCA) height. (c) Operating-point curves, which trade specificity against correctness (Valmadre 2022; Goren et al. 2024's hierarchical risk-coverage). Valmadre found top-down classifiers were beaten by a flat softmax across the whole operating range.
- **Unseen cards are the MTG version of cold-start items.** A model that represents a card only by its identity (one-hot, card2vec) can do nothing with an unseen card. Representing cards by content lets the same model score unseen cards: rules-text embeddings, structured features (colour, cost, types, keywords) and, where available, usage statistics. Bertram et al. (2024) measured this directly. Random card vectors gave 23.8% on unseen sets (about chance) against 31–43% for content-based representations, while every representation scored about 68% on seen cards. DropoutNet (2017) trains for cold start by randomly hiding the identity part of the input.
- **MTG card-text embeddings exist, and the recent ones use small off-the-shelf encoders, frozen.** Examples: Sentence-BERT (Bertram 2024), `BAAI/bge-small-en-v1.5` with the card's own name masked (DraftFM, 2026), EmbeddingGemma (Rigaux & Kashima, 2026) and `gte-modernbert-base` (minimaxir dataset). Rigaux & Kashima report that text embeddings alone did not carry a model to a new set without usage data, but a few days of new-set data helped a lot.
- **Many CPU-friendly encoders exist.** They range from 7.6M parameters (static `potion-base-8M`, MIT) through 22–33M (all-MiniLM-L6-v2, bge-small, e5-small, arctic-embed-xs/s, granite-30m; Apache-2.0 or MIT) to 137M–600M (nomic v1.5, EmbeddingGemma-300m under the Gemma licence, Qwen3-Embedding-0.6B). Penny Dreadful's full card pool is only tens of thousands of cards, so embedding every card once per set is a batch job at any of these sizes.
- **Could not verify:** how MTGGoldfish, MTGTop8 and Untapped.gg assign archetypes (not published), and the internals of 17lands' Archetype Explorer clustering. Several web summaries attribute a naive-Bayes classifier to MTGGoldfish. That is wrong: the method belongs to a third-party tool (MTGO_Tools) that uses MTGGoldfish data.

---

## 1. Existing MTG (and CCG) archetype classifiers

### Commercial sites

| Site | What is visible | Method documented? |
|---|---|---|
| **MTGGoldfish** | Metagame pages list archetypes with share, key cards and colours. Metagame articles say archetypes below about 5% share are folded into an "Other" slice for display ([The Metagame #1](https://www.mtggoldfish.com/articles/the-metagame-1), [#2](https://www.mtggoldfish.com/articles/the-metagame-2)). | **No.** The [metagame page](https://www.mtggoldfish.com/metagame/modern/full) has no methodology text, and no Aggro/Control/Combo grouping. |
| **MTGTop8** | The [format page](https://www.mtgtop8.com/format?f=MO) groups archetypes under **AGGRO / CONTROL / COMBO** with percentages, and has catch-all buckets "Other - Aggro", "Other - Control", "Other - Combo", plus a "Rogue Corner". This is a two-level tree with a parent fallback bucket per top-level strategy. | **No.** Assignment criteria are not published. |
| **17lands** | Limited only. Decks are classified by **colour**: a colour counts as a main colour with 4+ cards of it and as a splash with 3 or fewer, and a 2026 update added rules for hybrid cards, ability splashes and non-land sources ([blog, 2026-06-05](https://blog.17lands.com/posts/deck-color-classification/)). The [Archetype Explorer](https://www.17lands.com/archetype_explorer) (formerly Archetypist by Pekka Pulli and Sierkovitz, [repo](https://github.com/pekkapulli/draft-archetype-tool)) plots and clusters decks within each of the ten two-colour pairs by card similarity and local win rate. | Colour rules yes. Clustering internals not documented. The repo README gives no algorithm. |
| **Untapped.gg** | MTG Arena archetype pages and tier lists ([meta](https://mtga.untapped.gg/constructed/standard/meta)). Untapped is made by the HearthSim team. | **No.** No public description found. |

No site publishes a confidence score per deck. The ways they absorb uncertainty are "Other" buckets (MTGGoldfish display, MTGTop8 per strategy), colour-only fallback names, and a rogue section.

### Open-source MTG classifiers

- **Badaro / MTGOArchetypeParser + MTGOFormatData** (MIT; format data updated for each set, last push 2026-09-07). Source: [ArchetypeAnalyzer.cs](https://github.com/Badaro/MTGOArchetypeParser/blob/master/MTGOArchetypeParser/Data/ArchetypeAnalyzer.cs), [format data README](https://github.com/Badaro/MTGOFormatData).
  - Archetypes are conjunctions of conditions: `InMainboard`, `TwoOrMoreInMainboard`, `DoesNotContain`, and so on, plus colour.
  - **Variants**: once a deck matches an archetype, each variant's extra conditions are tested. If no variant matches, the result is the base archetype. This is a one-level parent fallback built into the code (`if (!isVariant) results.Add(... Variant = null ...)`).
  - **Generic archetypes ("fallbacks"/"piles")**: if no specific archetype matches, the deck goes to the generic archetype with the most `CommonCards` copies. Similarity is copies matched divided by deck size, and results are kept only if it exceeds `minSimiliarity = 0.1`.
  - Multiple matches are reported as a conflict, or resolved with `PreferSimpler`. There is no probability.
  - New cards: the maintainers edit the rules and colour tables each set. Card colours come from MTGJSON with manual overrides.
- **MTGO_Tools, PR #1039** (2026-09-17, [link](https://github.com/Pedrogush/MTGO_Tools/pull/1039)). A classifier for opponents' decks in a client tool, trained on 2,708 decks labelled by MTGGoldfish/MTGO:
  - archetype profiles are mean card copies, with sideboard copies weighted 0.5;
  - near-duplicate labels are merged agglomeratively when IDF-weighted cosine ≥ 0.85;
  - classification is multinomial naive Bayes over distinct card names, with smoothing 0.1 and priors equal to deck share;
  - **posterior < 0.8 → "Unknown"**.
  - Reported (their numbers, not verified): at 8 cards seen, 78.4% top-1, 15.6% Unknown and 93.0% precision.
- **Tierney, "The Genetics of Magic"** (blog + [code](https://github.com/g-tierney/magic_deck_classification_multi_dir), 2018-05-17, [post](https://g-tierney.github.io/post/magic_classification/)).
  - Each archetype is a Dirichlet-Multinomial over cards, by analogy with alleles in sub-populations.
  - Data: MTGGoldfish records of SCG Modern events, 8,249 decks, 516 archetypes and 1,772 cards.
  - About **80% of held-out decks classified correctly**. Accuracy was higher for frequent archetypes and for archetypes that share few cards with others.
  - The author notes the posteriors are "too confident".
  - The Dirichlet pseudo-counts keep unseen card combinations from getting zero probability, but a new archetype needs labelled examples.
- **firemind/tf-archetype-nn** ([repo](https://github.com/firemind/tf-archetype-nn), 2016–2017, no licence). A TensorFlow MLP/softmax experiment on archetype labels. It has no documentation.
- **LDA on decklists** (H. D. Hlynsson, Towards Data Science, [link](https://medium.com/data-science/finding-magic-the-gathering-archetypes-with-latent-dirichlet-allocation-729112d324a6)). Decks are treated as documents and cards as words, and the topics come out as archetypes. The page returned 403, so its details are **unverified**.

### Hearthstone (closest well-studied analogue)

- **HSReplay's own labels** come from per-archetype "core" cards (probability ≈ 1) and "popular" cards. HSReplay "assigned [labels] automatically based on the core- and popular cards" of the whole deck. Source: Eger & Sauma Chacón, *Deck Archetype Prediction in Hearthstone*, FDG 2020 ([pdf](https://slothlab.info/assets/pdf/eger2020fdg.pdf)). HSReplay's own documentation of this was not found.
- **García-Sánchez et al.**, *Data Mining of Deck Archetypes in Hearthstone*, 2020 ([CEUR pdf](https://ceur-ws.org/Vol-2719/paper14.pdf)). K-means and agglomerative clustering on more than 500k Hearthpwn decks. The authors note that new expansions change the meta.
- **Dockhorn & Kruse**, *Predicting Cards Using a Fuzzy Multiset Clustering of Decks*, IJCIS 13(1) 2020 ([link](https://www.atlantis-press.com/journals/ijcis/125943384/view)). Centroids average card membership. Validated against HSReplay expert labels (v-measure up to 0.949). The model "assume[s] a static meta-game".

---

## 2. Classifying over a hierarchy with a fallback

### Vocabulary and standard methods

From Silla & Freitas, *A survey of hierarchical classification across different application domains*, DMKD 22 (2011) ([pdf](https://www.cs.kent.ac.uk/people/staff/aaf/pub_papers.dir/DMKD-J-2010-Silla.pdf)):

- **Flat**: ignore the tree and predict leaves only.
- **Local classifier per node (LCN)**: one binary classifier per node.
- **Local classifier per parent node (LCPN)**: one multi-class classifier per parent, choosing among its children, run top-down.
- **Local classifier per level (LCL)**.
- **Global ("big-bang")**: one model aware of the whole tree.
- **Mandatory leaf-node prediction (MLNP)** vs **non-mandatory leaf-node prediction (NMLNP)**. NMLNP "allows the most specific class predicted … to be a class at any node (i.e. internal or leaf node)". It was introduced by Sun & Lim (2001). They call the NMLNP setting a "category tree" and the mandatory-leaf setting a "virtual category tree". A tree with 37% of labels at parent archetypes is an NMLNP problem.
- **Stopping rule**: "use a threshold at each class node, and if the confidence … is lower than this threshold, the classification stops". Thresholds can be set automatically (Ceci & Malerba 2007).
- **Blocking problem** (Sun et al. 2004): a top-down stop or mistake high in the tree cannot be undone lower down. The proposed mitigations are threshold reduction, restricted voting and extended multiplicative thresholds.

### Probability-based "deepest confident node" rules

Several papers share one idea. Take (calibrated) leaf probabilities. (The cited papers assume ground truth at leaves. When ground truth can sit at an internal node, as with our parent-archetype labels, one construction is an extra leaf under that node meaning "this node, no child". That construction is not taken from these papers.) Sum them over each subtree to get a node's probability. Then pick a node that trades specificity against confidence.

- **Ramaswamy, Tewari & Agarwal**, *Convex Calibrated Surrogates for Hierarchical Classification*, ICML 2015 ([PMLR](http://proceedings.mlr.press/v37/ramaswamy15.html)). Under **tree-distance loss**, the Bayes-optimal prediction is "the deepest node … such that the total conditional probability of the subtree rooted at the node is greater than 1/2". They reduce the problem to multiclass classification with a **reject option** (the OvA-Cascade algorithm).
- **Deng, Krause, Berg & Fei-Fei**, *Hedging Your Bets: Optimizing Accuracy-Specificity Trade-offs*, CVPR 2012 ([anthology](https://mlanthology.org/cvpr/2012/deng2012cvpr-hedging/)). **DARTS** wraps any flat classifier's posteriors. It maximises "information gain" (specificity) subject to a target overall accuracy, finding the trade-off with a Lagrange multiplier and binary search. Correctness here means the prediction is the true class or one of its ancestors.
- **Goren, Galil & El-Yaniv**, *Hierarchical Selective Classification*, NeurIPS 2024 ([arXiv 2405.11533](https://arxiv.org/abs/2405.11533)).
  - Defines hierarchical risk (the prediction is not an ancestor-or-self of the true label). Defines hierarchical coverage as 1 − H(v)/H(root), where H is the entropy of the leaves under v, so the root has coverage 0 and leaves 1.
  - Their "Climbing" rule starts at the most likely leaf and climbs "until reaching an ancestor with confidence above the threshold". Node confidence is the sum of its leaf descendants' probabilities after temperature scaling.
  - The threshold is fitted once on a calibration set to guarantee a target accuracy with high probability. The method is post hoc: "does not require any retraining".
- **Selective classification / reject option (flat)**: Chow, *On optimum recognition error and reject tradeoff*, IEEE Trans. IT 1970, and Geifman & El-Yaniv, *Selective Classification for Deep Neural Networks*, NeurIPS 2017 ([arXiv 1705.08500](https://arxiv.org/abs/1705.08500)), which introduced risk-coverage curves and a guaranteed-risk threshold. A parent fallback is a "partial reject": the model abstains only on the part of the tree below the chosen node.
- **Conformal prediction on hierarchies**. These methods return a node or small set of nodes, with a guarantee that the true label is covered:
  - Mortier et al., *Conformal Prediction in Hierarchical Classification with Constrained Representation Complexity* (arXiv [2501.19038](https://arxiv.org/abs/2501.19038), 2025, revised 2026). One variant restricts the prediction set to a single internal node.
  - den Hengst et al., *Hierarchical Conformal Classification* (arXiv [2508.13288](https://arxiv.org/abs/2508.13288), 2025). Prediction sets can mix levels.
- **Calibration** is what makes a threshold meaningful. Guo et al., *On Calibration of Modern Neural Networks*, ICML 2017 ([arXiv 1706.04599](https://arxiv.org/abs/1706.04599)), covers temperature scaling. Platt scaling and isotonic regression are the classical alternatives. Tierney's over-confident naive-Bayes-like posteriors (§1) are the known failure mode for bag-of-cards models.

### Evidence on which approach works

- **Valmadre**, *Hierarchical classification at multiple operating points*, NeurIPS 2022 ([arXiv 2210.10929](https://arxiv.org/abs/2210.10929), [code](https://github.com/jvlmdr/hiercls)). Builds operating curves for any method that scores every node. Finding: "top-down classifiers are dominated by a naive flat softmax classifier across the entire operating range". A soft structured-hinge loss beat the flat baseline.
- **Wu, Tygert & LeCun**, *A hierarchical loss and its problems when classifying non-hierarchically*, PLOS ONE 2019 ([arXiv 1709.01062](https://arxiv.org/abs/1709.01062)). An ultrametric hierarchical loss. Plain cross-entropy training lowered it "nearly as much" as optimising it directly, so they suggest using it for evaluation.
- **Bertinetto et al.**, *Making Better Mistakes*, CVPR 2020 ([arXiv 1912.09393](https://arxiv.org/abs/1912.09393)). Measures mistake severity by the height of the **lowest common ancestor (LCA)**. Hierarchy-aware training (hierarchical cross-entropy, soft labels) made mistakes less severe at a small cost in top-1 accuracy.

### Scoring predictions against the tree

- **Hierarchical precision/recall/F (set-based)**. Kiritchenko et al. (tech report 2005; Canadian AI 2006), as recommended by Silla & Freitas. Augment the prediction and the label each with all of their ancestors (P̂ᵢ, T̂ᵢ):
  - hP = Σ|P̂ᵢ∩T̂ᵢ| / Σ|P̂ᵢ|
  - hR = Σ|P̂ᵢ∩T̂ᵢ| / Σ|T̂ᵢ|
  - hF = 2·hP·hR / (hP+hR)

  A correct parent fallback (predicting a true ancestor) gets hP = 1 and hR < 1. A wrong leaf on the right branch gets partial credit for the shared ancestors. The `hiclass` library implements these metrics.
- **Pair-based costs**: tree distance (edges between prediction and label, as in Ramaswamy 2015), LCA height (Bertinetto 2020) and ultrametric loss (Wu et al. 2019). **Kosmopoulos et al.**, *Evaluation measures for hierarchical classification: a unified view and novel approaches*, DMKD 29 (2015) ([arXiv 1306.6802](https://arxiv.org/abs/1306.6802)), sorts measures into pair-based and set-based families. It proposes LCA-restricted set-based versions so that deep hierarchies do not over-reward shared high-level ancestors.
- **Curves rather than single numbers**: specificity-correctness curves (Valmadre 2022), hierarchical risk-coverage curves (Goren et al. 2024), and accuracy vs information gain (Deng et al. 2012).

### Tooling

**HiClass** (Miranda, Köhnecke & Renard, JMLR 24(29) 2023, [paper](https://jmlr.org/papers/v24/21-1518.html), [repo](https://github.com/scikit-learn-contrib/hiclass), BSD-3-Clause, latest release v5.0.3 2025-02-12):

- scikit-learn-compatible LCN, LCPN and LCL classifiers;
- hierarchical P/R/F;
- calibration: Platt, isotonic, beta and Venn-Abers, with calibration-error metrics;
- probability combiners along the path: multiply, arithmetic mean, geometric mean.

The current `LocalClassifierPerParentNode.predict` has a `# TODO: Add threshold to stop prediction halfway`, so stopping at a parent is not built in.

---

## 3. Unseen items (features never seen in training)

For an archetype classifier, an unseen card is an unseen *input feature* (an unseen item in a set), not an unseen class. The relevant literature is cold-start recommendation and generalised card representations.

- **Identity-only representations cannot generalise.** A one-hot or learned per-card vector for an unseen card is empty or random. Bertram, Fürnkranz & Müller, *Learning With Generalised Card Representations for "Magic: The Gathering"*, IEEE CoG 2024 ([arXiv 2407.05879](https://arxiv.org/abs/2407.05879)), predicted 17lands draft picks trained only on NEO. Top-1 accuracy was:

  | Representation | NEO (seen) | Unseen sets |
  |---|---|---|
  | Random vectors | 67.9% | 23.8% (≈ chance, 22%) |
  | Image autoencoder | 68.1% | 31.1% |
  | Features: numeric/categorical + Sentence-BERT embedding of full card text | 67.8% | 33.6% |
  | Meta: 16 usage statistics | 64.7% | 42.1% |
  | Features + Meta + Image | 68.0% | 42.9% |

  In their words, representation "has little effect … among known cards" but matters for unseen cards. Trained on all other sets, the model predicted 55% of human choices on a held-out set. Fine-tuning on a few days of new-set data improved it quickly. Usage statistics "are only available when a set has seen sufficient … play".
- **Content-only card models built for day zero.** Ward, *DraftFM: A Foundation Model for Day-Zero Drafting* (arXiv [2608.19568](https://arxiv.org/abs/2608.19568), 2026-08-20).
  - Each card is a frozen 775-dim vector: a 384-dim `BAAI/bge-small-en-v1.5` embedding of type line + rules text, plus 391 structured dimensions (mana, colour, types, 128 creature-subtype slots, 166 keyword slots, P/T/loyalty, rarity, layout, rules-text shape).
  - The card's **own name is replaced** before embedding "so that a known proper noun cannot act as a hidden card identifier". Reminder text is **kept** because it "may be the only definition available for a new mechanic".
  - The model has "no card identities, set identities, or usage statistics … so an unseen card is scored by the same machinery as a familiar one".
  - Evaluated on three expansions withheld from training entirely. Top-1 agreement (how often the model's highest-ranked card is the card the human actually picked) was 50.8%, 60.4% and 56.7%, one figure per held-out expansion; the abstract does not say which figure belongs to which set. Uniform chance at the opening pick is about 7% ([abstract](https://arxiv.org/abs/2608.19568)). These are draft-pick numbers and are not comparable to archetype-classification accuracy.
- **Cold-start recommenders** (the same problem outside MTG):
  - **DropoutNet** (Volkovs, Yu & Poutanen, NeurIPS 2017, [paper](https://proceedings.neurips.cc/paper/2017/hash/dbd22ba3bd0df8f385bdac3e9f8be207-Abstract.html), [code](https://github.com/layer6ai-labs/DropoutNet)) feeds both an item's preference/ID vector and its content features. During training it randomly drops the preference input so the network learns to rely on content, which is the situation of a cold (unseen) item.
  - **Meta-Prod2Vec** (Vasile et al. 2016, [arXiv 1607.07326](https://arxiv.org/abs/1607.07326)) adds side information (such as category) to item2vec-style embeddings for cold-start items.
  - **UniSRec** (Hou et al., KDD 2022, [arXiv 2206.05941](https://arxiv.org/abs/2206.05941)) replaces item IDs with encodings of item description text so that models transfer to new items and domains.
  - **Hybrid ID + content card vectors in MTG**: [`nsaroiu/mtg-deck-completion`](https://huggingface.co/nsaroiu/mtg-deck-completion) (MIT) sums a learned per-card vector, a small MLP over structured features and an oracle-text sentence embedding, so "a rarely-seen card starts from a meaningful representation". The sentence model is not named.
- **Out-of-vocabulary tokens in text** are the same problem in NLP. fastText (Bojanowski et al. 2017, [arXiv 1607.04606](https://arxiv.org/abs/1607.04606)) builds a vector for an unseen word from its sub-parts (character n-grams). Content embeddings do the same job for cards.
- **Set / bag-of-items models**:
  - *Deep Sets* (Zaheer et al., NeurIPS 2017, [arXiv 1703.06114](https://arxiv.org/abs/1703.06114)): any permutation-invariant function of a set can be written ρ(Σφ(x)). With φ applied to per-card content vectors, a deck's representation is defined whether or not its cards were seen.
  - Set Transformer (Lee et al., ICML 2019) adds attention between elements.
  - Manamorphosis ([repo](https://github.com/JakeBoggs/Manamorphosis)) treats a 60-card deck as an unordered set of Doc2Vec card vectors, with no positional embeddings.
- **Bag-of-cards count models** (naive Bayes, Dirichlet-Multinomial) handle unseen cards by ignoring them or giving them the smoothing pseudo-count. The deck is then classified from its seen cards only (Tierney 2018; MTGO_Tools 2026).
- **Human-curated functional tags** are a structured alternative to text embeddings. **Scryfall Tagger** "oracle tags" describe a card's role (removal, ramp, draw and so on). They are queryable as `otag:`/`function:` and published as daily bulk data ([search syntax](https://scryfall.com/docs/syntax), [Tagger tags](https://scryfall.com/docs/tagger-tags)). The tags are community-maintained, change over time, and are tracked by UUID. New cards are tagged only after release, and how fast new-set coverage arrives is **unverified**. The [API tags page](https://scryfall.com/docs/api/tags) returned 403 and was not read.

---

## 4. Card-text embeddings for MTG

### Existing MTG work

| Work | Date | What is embedded | Model | Notes |
|---|---|---|---|---|
| [afreefaw/MTG-card2vec](https://github.com/afreefaw/MTG-card2vec) | ~2023 | Card **co-occurrence** in decklists, not text | word2vec (gensim), 100-dim | Uses 17lands and scraped decks. Identity-based, so an unseen card gets no vector. No licence stated. |
| Bertram et al., CoG 2024 ([arXiv 2407.05879](https://arxiv.org/abs/2407.05879)) | 2024-07 | Full card text + numeric/categorical features | Sentence-BERT (Reimers & Gurevych 2019). Exact checkpoint not named in the text read. | See §3 for seen vs unseen results. |
| [JakeBoggs/Manamorphosis](https://github.com/JakeBoggs/Manamorphosis) | undated | Mana cost, type, P/T, rules text | Doc2Vec, 128-dim | Used in a deck-completion diffusion model trained on about 47k MTGTop8 decks. No licence stated. |
| [minimaxir/mtg-embeddings](https://huggingface.co/datasets/minimaxir/mtg-embeddings) (dataset) | cards through Aetherdrift* | Name, cost, type, rules text, P/T/loyalty, rarity, set. The card's name inside its text is replaced by `~`. | `Alibaba-NLP/gte-modernbert-base` (149M, Apache-2.0) | MIT. Includes UMAP 2-D coordinates. *The card says "Aetherdrift (2024-02-14)", but Aetherdrift released in February 2025, so the date on the card looks wrong. |
| Rigaux & Kashima, *Predicting Drafted Deck Strength* ([arXiv 2607.04782](https://arxiv.org/abs/2607.04782)) | 2026-07 | Full oracle string: name, costs, rarity, types, P/T/loyalty, keywords, effects; both faces. | EmbeddingGemma, frozen | The model "struggles to generalize to new sets, without having access to the meta features". Fine-tuning on four days of new-set data helped substantially. |
| Ward, *DraftFM* ([arXiv 2608.19568](https://arxiv.org/abs/2608.19568)) | 2026-08 | Type line + rules text, own name masked, reminder text kept; plus 391 structured features | `BAAI/bge-small-en-v1.5`, frozen, 384-dim, L2-normalised | Designed for unseen cards. See §3. |
| Bertram, *UrzaGPT* ([arXiv 2508.08382](https://arxiv.org/abs/2508.08382)) | 2025-08 | Draft state as text to an LLM | LoRA-tuned LLMs | Per-decision LLM calls, so outside the "no per-deck model calls" constraint. GPT-4o zero-shot reached 43%. |
| Zilio, Prates & Lamb ([arXiv 1810.03744](https://arxiv.org/abs/1810.03744)) | 2018-10 | Card text and images | RNN and CNN | Classifies card attributes from text and image. Not an embedding for deck tasks. |

Common practices across the recent work:

- embed a normalised oracle string (types + rules text, sometimes cost/P/T);
- mask the card's own name;
- keep reminder text;
- concatenate both faces of multi-faced cards;
- keep the encoder **frozen** and add structured features beside it.

### Off-the-shelf text-embedding models small enough for offline CPU use

Parameter counts, licences and dates are taken from the Hugging Face model API and model cards (queried 2026-09-28).

- "Created" is the Hugging Face repo creation date. The `sentence-transformers/*` repos show 2022-03-02, a hub migration date; all-MiniLM-L6-v2 itself dates from 2021.
- Dimensions come from each model's config (hidden size).
- None of these models is trained on MTG text.

| Model | Params | Dim | Max tokens | Licence | Created (HF) |
|---|---|---|---|---|---|
| [minishlab/potion-base-8M](https://huggingface.co/minishlab/potion-base-8M) (Model2Vec **static**, no transformer at inference) | 7.6M | 256 | n/a | MIT | 2024-10-29 |
| [sentence-transformers/static-retrieval-mrl-en-v1](https://huggingface.co/sentence-transformers/static-retrieval-mrl-en-v1) (**static**) | not reported | 1024 (Matryoshka truncatable) | n/a | Apache-2.0 | 2024-10-24 |
| [Snowflake/snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs) | 22.6M | 384 | 512 | Apache-2.0 (in README; no HF licence tag) | 2024-04-12 |
| [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | 22.7M | 384 | 512 (trained on 256; card says longer input is truncated) | Apache-2.0 | 2021 (repo 2022-03-02) |
| [mixedbread-ai/mxbai-embed-xsmall-v1](https://huggingface.co/mixedbread-ai/mxbai-embed-xsmall-v1) | 24.1M | 384 | 4096 | Apache-2.0 | 2024-09-13 |
| [ibm-granite/granite-embedding-30m-english](https://huggingface.co/ibm-granite/granite-embedding-30m-english) | 30.3M | 384 | 512 | Apache-2.0 | 2024-12-04 |
| [jinaai/jina-embeddings-v2-small-en](https://huggingface.co/jinaai/jina-embeddings-v2-small-en) | 32.7M | 512 | 8192 | Apache-2.0 | 2023-09-27 |
| [Snowflake/snowflake-arctic-embed-s](https://huggingface.co/Snowflake/snowflake-arctic-embed-s) | 33.2M | 384 | 512 | Apache-2.0 | 2024-04-12 |
| [BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) (used by DraftFM) | 33.4M | 384 | 512 | MIT | 2023-09-12 |
| [intfloat/e5-small-v2](https://huggingface.co/intfloat/e5-small-v2) | 33.4M | 384 | 512 | MIT | 2023-05-19 |
| [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) | 109.5M | 768 | 512 | Apache-2.0 | 2021 (repo 2022-03-02) |
| [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5) | 109.5M | 768 | 512 | MIT | 2023-09-11 |
| [nomic-ai/nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) | 136.7M | 768 (Matryoshka) | 2048 (config) | Apache-2.0 | 2024-02-10 |
| [Alibaba-NLP/gte-modernbert-base](https://huggingface.co/Alibaba-NLP/gte-modernbert-base) (used by minimaxir) | 149.0M | 768 | 8192 | Apache-2.0 | 2025-01-20 |
| [google/embeddinggemma-300m](https://huggingface.co/google/embeddinggemma-300m) (used by Rigaux & Kashima) | 302.9M (Google: "308M") | 768, Matryoshka to 512/256/128 | 2K | **Gemma licence** (custom terms; gated download) | 2025-07-17, announced Sep 2025 ([docs](https://ai.google.dev/gemma/docs/embeddinggemma)) |
| [Qwen/Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 595.8M | up to 1024 | 32K | Apache-2.0 | 2025-06-03 |

Notes:

- The static models are claimed to be 100–400× faster than all-mpnet-base-v2 on CPU, at about 87% of its retrieval quality ([static-retrieval-mrl-en-v1 card](https://huggingface.co/sentence-transformers/static-retrieval-mrl-en-v1)). That is a retrieval benchmark, not MTG.
- Google says EmbeddingGemma can run in under 200 MB of RAM with quantisation.
- MTEB-style benchmark scores are general-domain retrieval and similarity. No benchmark found measures how well these models separate MTG rules text by function, so their relative quality on card text is **unknown**.

## Could not verify / open gaps

- The archetype-assignment methods of MTGGoldfish, MTGTop8 and Untapped.gg. None is published. The naive-Bayes description circulating in search summaries belongs to MTGO_Tools, not MTGGoldfish.
- The 17lands Archetype Explorer's embedding and clustering algorithm (the README is silent; the source was not read).
- The HSReplay/HearthSim archetype classifier's source (the `HearthSim/hsarchetypes` repo returned 404). Its core/popular-card mechanism is known only via Eger & Sauma Chacón (2020).
- The exact Sentence-BERT checkpoint in Bertram et al. (2024), and the sentence model in `nsaroiu/mtg-deck-completion`.
- Hlynsson's LDA article (403) and the Scryfall API tags page (403).
- Reported accuracy numbers from MTGO_Tools, DraftFM and Rigaux & Kashima are the authors' own and were not reproduced.
