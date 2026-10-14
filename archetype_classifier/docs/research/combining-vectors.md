# Combining vectors into one deck representation

Research for issue #50 (Better deck representation). Compiled 2026-10-13. Findings only: this document does not recommend an approach, and no experiments were run.
Terms follow [CONTEXT.md](../../CONTEXT.md) (card embedding, card numbers, combined embedding, deck vector, training row, candidates, unseen card, playability, similarity).
It builds on [prior-art.md](prior-art.md) and does not repeat it. In particular, Deep Sets, Set Transformer, DropoutNet and content-based card vectors for unseen cards are introduced there (§3).

## The question

Today a deck vector is the copy-weighted mean of its cards' combined embeddings, at unit length, and candidates are ranked by cosine similarity to about 84,000 training rows. Misses are near-ties. The cards that tell archetypes apart are a small part of the deck, and the mean dilutes them among staples and basic lands. The site's rarity-weighted bag-of-cards similarity finds rarely seen archetypes better.

Four questions:

1. How to combine different vectors for one card (text embedding plus card numbers).
2. How to pool a deck's card vectors into one deck vector, beyond the mean.
3. How to combine a sparse bag-of-cards vector with a dense embedding.
4. Whether autoencoders help, compared with supervised metric learning.

## Summary

- **The mean is a match kernel, and match kernels overcount repeats.** The dot product of two mean vectors equals the average similarity over every pair of items, one from each set. Sánchez et al. (2013) call this the "match kernel" and say it "tends to overcount multiple matches and therefore it cannot cope with the burstiness effect" ([IJCV 2013](https://ivi.fnwi.uva.nl/isis/publications/2013/SanchezIJCV2013/SanchezIJCV2013.pdf), §2.4). Computer vision's standard fixes are a signed square root of each dimension and L2 normalisation. The square root "downplays the influence of descriptors which happen frequently" (§2.3). They also list a "sum-max" kernel that matches each item only to its best partner.
- **Frequency weighting before averaging is a strong, cheap baseline.** SIF (Arora, Liang & Ma, ICLR 2017) weights each word by a/(a + p(w)), where p(w) is the word's frequency, then removes the first principal component from all sentence vectors ([abstract](https://mlanthology.org/iclr/2017/arora2017iclr-simple), [official code](https://github.com/PrincetonML/SIF)). The abstract reports 10% to 30% gains on textual similarity. Plain IDF weighting of a mean is not reliably better than no weighting (De Boom et al. 2016).
- **Max, min and power means keep what the mean loses, without training.** Concatenating the min, mean and max (and the cubic mean) of word vectors "considerably closes the gap" to trained sentence encoders (Rücklé et al. 2018). Max pooling picks out a few salient features (Shen et al., ACL 2018). Generalised-mean pooling has one parameter that runs from mean (p = 1) to max (p → ∞), and the parameter can be learned (Radenović et al., TPAMI 2018).
- **Codebook methods (bag of visual words, VLAD, Fisher vectors) turn a set into a long fixed vector.** Each item is assigned to its nearest centre (learned without labels by k-means or a Gaussian mixture), and the set's vector keeps per-centre statistics. VLAD sums each item's difference from its centre. The result is K times longer than one item vector, so staples and key cards land in different blocks instead of one average.
- **Learned pooling needs labels or a training objective.** Attention pooling learns a weight per item with a softmax (Ilse et al., ICML 2018). Set Transformer's attention pooling usually beat plain sum or mean pooling in its own experiments (Lee et al., ICML 2019). NetVLAD makes VLAD trainable end to end (Arandjelović et al., CVPR 2016). The OTKE embedding pools a set through optimal transport to a learned reference, with or without labels (Mialon et al., ICLR 2021).
- **Optimal transport can replace the single vector entirely.** Word Mover's Distance compares two bags item by item and gave very low kNN error on eight document datasets (Kusner et al., ICML 2015). It costs O(p³ log p) per pair. Its cheapest lower bound is the distance between the two weighted means, which is today's deck vector. The tighter relaxed bound is O(p²) and pruned up to 95% of documents. Sinkhorn distances make transport "several orders of magnitude faster" (Cuturi, NeurIPS 2013).
- **Hybrid sparse + dense retrieval usually helps, and a convex combination of normalised scores is the robust choice.** Adding BM25 to dense retrieval gave statistically significant gains on most collections (Ma et al. 2021). Bruch et al. (2023) found a convex combination beat reciprocal rank fusion, whose quality "swings wildly" with its parameter. The choice of linear normalisation mostly shifts the best weight, and the weight can be tuned on under 5% of the training queries. Luan et al. (TACL 2021) argue fixed-length dense vectors have limited capacity for precise matching, which is why sparse signals still help.
- **Autoencoders are a weak fit for nearest-neighbour ranking when labels exist.** In a two-view comparison, "CCA-based approaches tend to outperform unconstrained reconstruction-based approaches" (Wang et al. 2015). For sentence vectors, the best method "depends critically on the intended application", and non-linear decoders may give a space whose geometry cosine does not reflect (Hill et al., NAACL 2016). Semantic hashing's autoencoder codes were slightly worse than TF-IDF at the top of the ranking, and helped as a pre-filter for TF-IDF (Salakhutdinov & Hinton 2009). Bag-of-items VAEs fix the item vocabulary at training time (Liang et al., WWW 2018), so they cannot represent an unseen item.
- **Supervised metric learning targets neighbour quality directly.** NCA "directly maximizes a stochastic variant of the leave-one-out k-nearest neighbors (KNN) score" ([scikit-learn](https://scikit-learn.org/stable/modules/neighbors.html#neighborhood-components-analysis)), but scikit-learn's version stores an n_samples² distance matrix. LDA projects to fewer than (number of classes) dimensions under a shared-covariance Gaussian assumption. Proxy-based losses learn one proxy per class and converged "three times as fast" as triplet losses (Movshovitz-Attias et al., ICCV 2017). Musgrave et al. (ECCV 2020) found that under fair tuning newer metric-learning losses barely beat the 2006 contrastive and triplet losses.
- **Could not verify:** several details from full texts that were blocked (see the last section).

---

## 1. Combining different vectors for one item

### Concatenation and weights (early fusion)

- **Concatenation with per-block weights is a weighted sum of kernels.** The inner product of two concatenated vectors is the sum of the blocks' inner products, each scaled by its weight squared. (This is algebra, not a cited finding.) So per-block normalisation plus weights, as in the combined embedding, is a fixed linear combination of a text similarity and a numbers similarity.
- **Learning the kernel weights rarely changes accuracy much.** Gönen & Alpaydın review multiple kernel learning (MKL) and compare many methods on real datasets ([JMLR 12, 2011](https://jmlr.org/papers/v12/gonen11a.html)). Their abstract says "there may not be large differences in terms of accuracy" between methods, that "using multiple kernels instead of a single one is useful", and that combining kernels "in a nonlinear or data-dependent way seems more promising than linear combination" for simple linear kernels. Whether MKL beat a plain sum of kernels is not stated in the abstract, and the full paper was not read.
- **Early versus late fusion.** Snoek, Worring & Smeulders, *Early versus Late Fusion in Semantic Video Analysis*, ACM Multimedia 2005 ([pdf](https://isis-data.science.uva.nl/cgmsnoek/pub/snoek-earlylate-acm2005.pdf), DOI 10.1145/1101149.1101236). Early fusion joins features before learning; late fusion combines per-view scores. Over 20 concepts in 184 hours of video, late fusion was slightly better for most concepts, but where early fusion won, it won by more. (Taken from the abstract as quoted in search results; the PDF was not read.)

### Learned linear projections

- **Whitening** decorrelates dimensions and can reduce them. Su et al., *Whitening Sentence Representations for Better Semantics and Faster Retrieval* ([arXiv 2103.15316](https://arxiv.org/abs/2103.15316), 2021), report that whitening fixes the "anisotropy problem" of BERT sentence vectors and also reduces their dimension. Unsupervised.
- **Supervised whitening from matching pairs.** Radenović et al. learn a whitening from "the intraclass (matching pairs) covariance matrix", then a rotation from non-matching pairs ([TPAMI 2018, arXiv 1711.02512](https://ar5iv.labs.arxiv.org/html/1711.02512)). The abstract says this "outperforms commonly used PCA whitening".
- **LDA and NCA** (supervised projections) are covered in §4 because they are metric-learning methods.

### CCA and multi-view methods

- **CCA** finds paired projections of two views that are maximally correlated. scikit-learn's CCA "involves the inversion of X_k^T X_k and Y_k^T Y_k" and "can be unstable if the number of features or targets is greater than the number of samples" ([cross-decomposition docs](https://scikit-learn.org/stable/modules/cross_decomposition.html)). Unsupervised (it uses only the pairing).
- **Deep CCA and autoencoder variants.** Wang, Arora, Livescu & Bilmes, *On Deep Multi-View Representation Learning: Objectives and Optimization* ([arXiv 1602.01024](https://arxiv.org/abs/1602.01024); a shorter version is in ICML 2015). Setting: two views at training, one view at test. They compared linear CCA, kernel CCA, deep CCA (DCCA), split and correlated autoencoders, and DCCAE (DCCA plus reconstruction). DCCAE and DCCA were best on most tasks. Their summary: "CCA-based approaches tend to outperform unconstrained reconstruction-based approaches", and "when the inputs are noisy, reconstructing the input faithfully may lead to unwanted degrees of freedom in the features".
- Note for our setting: CCA needs two views that are paired and both informative. Text and card numbers are both views of the same card, so CCA would find the directions they agree on (for example colour words and colour flags), not necessarily the directions that separate archetypes.

### Late fusion of separate similarities

Late fusion of rankings or scores is the subject of §3 (hybrid retrieval). The same tools (convex combination of normalised scores, rank fusion) apply to text-only and numbers-only similarities.

---

## 2. Pooling a set of item vectors into one vector

### The mean and why it dilutes

- **The mean's dot product is the all-pairs match kernel.** For sets X and Y with base kernel k, Sánchez, Perronnin, Mensink & Verbeek define the match kernel K(X,Y) = (1/TU) Σ_t Σ_u k(x_t, y_u). With a linear k, this is the dot product of the two means. They write that summing all pairs "tends to overcount multiple matches and therefore it cannot cope with the burstiness effect" ([IJCV 105, 2013](https://ivi.fnwi.uva.nl/isis/publications/2013/SanchezIJCV2013/SanchezIJCV2013.pdf), §2.4).
- **Burstiness** is an item occurring more often in one set than an independence model predicts. It was first described in text and shown to distort image search scores by Jégou, Douze & Schmid, *On the Burstiness of Visual Elements*, CVPR 2009 ([record](https://mlanthology.org/cvpr/2009/jegou2009cvpr-burstiness)). The full text was blocked, so their exact remedies are taken from Sánchez et al.'s summary.
- **Remedies listed by Sánchez et al.**:
  - signed power normalisation z ← sign(z)|z|^ρ, with ρ = ½ in all their experiments (§2.3). It "downplays the influence of descriptors which happen frequently within a given image (bursty visual features)". It "is also beneficial to the BoV" (bag of visual words);
  - L2 normalisation, so that dot product and Euclidean distance agree;
  - the "sum-max" match kernel of Wallraven et al. (2003), which averages each item's best match in the other set, and the "power" match kernel of Lyu (2005), which raises each pair's similarity to a power ρ (§2.4).
  - In their ablation, power normalisation was the single largest gain, "+8.3" points (§3).

### Frequency-weighted means

- **SIF.** Arora, Liang & Ma, *A Simple but Tough-to-Beat Baseline for Sentence Embeddings*, ICLR 2017 ([abstract](https://mlanthology.org/iclr/2017/arora2017iclr-simple)). A weighted average of word vectors, then removal of a common direction found by PCA/SVD. The official code ([PrincetonML/SIF](https://github.com/PrincetonML/SIF)) weights each word by `a / (a + value/N)`, with default `a = 1e-3`, so frequent words get weights near 0. It then subtracts each sentence vector's projection onto the top singular vector(s) of the matrix of all sentence vectors. Unsupervised: it needs only item frequencies. The abstract reports 10% to 30% gains on textual similarity tasks. (The OpenReview PDF was blocked; formula details come from the official code.)
- **Common-component removal on its own.** Mu & Viswanath, *All-but-the-Top* ([arXiv 1702.01417](https://ar5iv.labs.arxiv.org/html/1702.01417)), subtract the mean vector and the top D principal components (D ≈ d/100) from word vectors. Gains were small but consistent, for example about 4% on semantic textual similarity.
- **IDF-weighted means are not reliably better.** De Boom et al., *Representation learning for very short texts using weighted word embedding aggregation*, Pattern Recognition Letters ([arXiv 1607.00570](https://ar5iv.labs.arxiv.org/html/1607.00570)). An IDF-weighted mean was worse than the plain mean on Wikipedia texts (24.00% vs 19.43% split error at 20 words) and better on Twitter (31.28% vs 33.68%). Weights learned for the task beat both.

### Max, min and power means

- **p-means.** Rücklé, Eger, Peyrard & Gurevych, *Concatenated Power Mean Word Embeddings as Universal Cross-Lingual Sentence Representations* ([arXiv 1803.01400](https://ar5iv.labs.arxiv.org/html/1803.01400)). The power mean ((x₁^p + … + xₙ^p)/n)^(1/p) per dimension; p = 1 is the mean, p = ±∞ the max and min. Monolingually they concatenate p ∈ {−∞, 1, +∞}; their best cross-lingual model adds p = 3. They found "positive power means are preferable over negative ones". The pooled vector is K × d long for K means. The pooling has no trained parameters.
- **SWEM.** Shen et al., *Baseline Needs More Love*, ACL 2018 ([arXiv 1805.09843](https://ar5iv.labs.arxiv.org/html/1805.09843)). On document categorisation, max pooling was slightly worse than the mean, but the two were complementary, so mean+max concatenation was usually the best of their simple variants. Max-pooled features were sparse and each dimension's top words "correspond to a common topic". (Their word vectors were trained with the task.)
- **Generalised mean (GeM).** Radenović, Tolias & Chum, TPAMI 2018 ([arXiv 1711.02512](https://ar5iv.labs.arxiv.org/html/1711.02512)). The same power mean, applied to non-negative CNN activations. "The pooling parameter p_k can be manually set or learned", and a single shared learned p worked best. Note that a non-integer p is undefined for negative values, so text-embedding dimensions would need shifting or an odd integer p (an algebraic point, not from the paper).

### Codebook methods: bag of visual words, VLAD, Fisher vectors

- **Bag of visual words (BoV).** Sivic & Zisserman, *Video Google*, ICCV 2003 ([record](https://mlanthology.org/iccv/2003/sivic2003iccv-video)), borrowed text retrieval for images: quantise each local descriptor to a "visual word" learned by k-means, then compare sets as word-count histograms with inverted files. The PDF was not read, so their weighting details are not verified here.
- **VLAD.** Jégou, Douze, Schmid & Pérez, *Aggregating local descriptors into a compact image representation*, CVPR 2010 ([HAL record](https://hal-univ-tlse3.archives-ouvertes.fr/INRIA/inria-00548637)). From Sánchez et al.'s description: assign each descriptor to its nearest k-means centre and, for each centre, sum the descriptors' differences from it. VLAD is a simplified Fisher vector (hard assignment, means only), and power and L2 normalisation "can also be applied to the VLAD with significant improvements" (IJCV 2013, §2.4). Size K × d. Unsupervised.
- **Fisher vectors.** Describe a set by its gradient with respect to a Gaussian mixture fitted without labels; size K(2D+1). Sánchez et al. note it is "almost dense", unlike sparse BoV histograms, and works well with linear classifiers (IJCV 2013).
- **NetVLAD.** Arandjelović et al., CVPR 2016 ([arXiv 1511.07247](https://arxiv.org/abs/1511.07247)). A VLAD layer trained end to end with a weakly supervised ranking loss. Supervised.

### Learned set functions

Deep Sets and Set Transformer are introduced in [prior-art.md](prior-art.md) §3. Details relevant here:

- **Deep Sets** (Zaheer et al., NeurIPS 2017, [arXiv 1703.06114](https://ar5iv.labs.arxiv.org/html/1703.06114)). The theorem f(X) = ρ(Σ φ(x)) is exact for a countable universe of items. For real-valued items it is proved only for fixed-size sets, with a latent size that grows with set size, plus an approximation result. The main model uses sum pooling. Supervised in their experiments.
- **Set Transformer** (Lee et al., ICML 2019, [arXiv 1810.00825](https://ar5iv.labs.arxiv.org/html/1810.00825)). Pooling by Multihead Attention (PMA) attends from k learned "seed" vectors to the set; most experiments use k = 1. Inducing points cut self-attention from O(n²) to O(nm). In their tables, attention pooling usually beat "rFF + Pooling" (the Deep Sets form). For example, unique-character counting accuracy was 0.4382 for rFF+Pooling and 0.6037 for SAB+PMA. On the largest point clouds, the gap was small (0.8933 vs 0.9040 at 5000 points).
- **Attention pooling.** Ilse, Tomczak & Welling, *Attention-based Deep Multiple Instance Learning*, ICML 2018 ([arXiv 1802.04712](https://ar5iv.labs.arxiv.org/html/1802.04712)). z = Σ a_k h_k with a_k = softmax over items of wᵀ tanh(V h_k), plus a gated variant. The weights sum to 1 so the pooling is invariant to bag size. The weights "provide insight into the contribution of each instance". Supervised (trained from bag labels).
- **OTKE.** Mialon, Chen, d'Aspremont & Mairal, *A Trainable Optimal Transport Embedding for Feature Aggregation*, ICLR 2021 ([arXiv 2006.12065](https://arxiv.org/abs/2006.12065)). A fixed-size embedding that aggregates a set's elements according to an optimal transport plan to a reference set. The reference can be trained end to end or learned with "a simple unsupervised learning mechanism with small computational cost".

All of these apply the same φ (or attention scorer) to every item's content vector. With content vectors as input, an unseen card gets a φ value like any other card ([prior-art.md](prior-art.md) §3).

### Set distances without a single vector

- **Word Mover's Distance (WMD).** Kusner, Sun, Kolkin & Weinberger, *From Word Embeddings To Document Distances*, ICML 2015 ([PMLR](https://proceedings.mlr.press/v37/kusnerb15.html)). The minimum cost of moving one bag's weighted items onto the other's, an Earth Mover's Distance. "The metric has no hyperparameters". It gave "unprecedented low" kNN classification error on eight datasets against seven baselines. From the full text (§4.1):
  - exact WMD costs O(p³ log p), where p is the number of unique items;
  - the **Word Centroid Distance** ‖X d − X d′‖₂, the distance between the two weighted means, is a lower bound on WMD and costs O(dp). It "is not very tight";
  - the **Relaxed WMD**, which drops one of the two flow constraints, is "significantly tighter" and costs O(p²);
  - "prefetch and prune" sorts candidates by the centroid distance, then skips any whose relaxed bound already exceeds the current k-th best. It pruned "up to 95% of all documents on some data sets".
- **Sinkhorn distances.** Cuturi, NeurIPS 2013 ([arXiv 1306.0895](https://arxiv.org/abs/1306.0895)). Entropic regularisation makes optimal transport "several orders of magnitude faster than that of transportation solvers"; exact transport is "prohibitive whenever the histograms' dimension exceeds a few hundreds".
- **Late interaction.** ColBERT (Khattab & Zaharia, SIGIR 2020, [arXiv 2004.12832](https://arxiv.org/abs/2004.12832)) keeps one vector per token and scores with a "lightweight" interaction step after independent encoding, so document vectors are precomputed. The MaxSim formula (each query token's best match, summed) is from the full paper, which was not read here. It is the same idea as the sum-max match kernel above.

These avoid the single vector at the cost of per-pair work. A common pattern in the sources is a cheap single-vector stage to shortlist, then the set distance to rerank (Kusner's prefetch and prune; ColBERT's pruning-friendly design).

---

## 3. Combining a sparse bag-of-items vector with a dense embedding

### Score fusion

- **Convex combination.** score = α·s_dense + (1 − α)·s_sparse, after normalising each score. Bruch, Gai & Ingber, *An Analysis of Fusion Functions for Hybrid Retrieval*, ACM TOIS 2023 ([arXiv 2210.11934](https://ar5iv.labs.arxiv.org/html/2210.11934), DOI 10.1145/3596512). Findings:
  - convex combination with theoretical min-max normalisation "significantly outperforms rrf on all datasets in terms of NDCG";
  - RRF's "NDCG swings wildly as a function of rrf parameters", and a tuned RRF transfers poorly to new domains;
  - min-max, z-score and other linear normalisations give rank-equivalent fusions up to a shift in the best α, so the choice matters less than expected; they prefer theoretical min-max (dividing by the score's known range) for stability;
  - α can be tuned on fewer than 5% of the training queries.
- **Reciprocal rank fusion (RRF).** Cormack, Clarke & Büttcher, SIGIR 2009 ([pdf](http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)). score(d) = Σ_r 1/(k + r(d)), with "k = 60 … fixed during a pilot investigation". Unsupervised, uses ranks only. It "almost invariably improved on the best of the combined results" in TREC and LETOR experiments.
- **BM25 + dense in practice.** Ma, Sun, Pradeep & Lin, *A Replication Study of Dense Passage Retriever* ([arXiv 2104.05740](https://ar5iv.labs.arxiv.org/html/2104.05740)). They used Sim + α·BM25, and gave a document missing from one list that list's minimum score. Unlike the original DPR paper, they found hybrid gains over dense alone statistically significant on most collections (NQ top-20 79.5 → 82.6).
- **Residual training.** Gao et al., CLEAR ([arXiv 2004.13969](https://ar5iv.labs.arxiv.org/html/2004.13969)), score with λ·s_lex + s_emb and train the dense model on BM25's errors, so it learns "semantic matching not captured by the lexical model".
- **Why sparse still helps.** Luan, Eisenstein, Toutanova & Collins, *Sparse, Dense, and Attentional Representations for Text Retrieval*, TACL 2021 ([arXiv 2005.00181](https://ar5iv.labs.arxiv.org/html/2005.00181)). The dense dimension needed to preserve BM25's rankings grows with document length, "suggesting limitations in the capacity of fixed-length encodings to support precise retrieval". Their hybrid is a linear score combination with "a single trainable weight λ, tuned on a development set".
- **Learned sparse vectors.** SPLADE (Formal, Piwowarski & Clinchant, SIGIR 2021, [arXiv 2107.05720](https://arxiv.org/abs/2107.05720)) learns sparse term weights with "explicit sparsity regularization and a log-saturation effect on term weights", keeping inverted-index efficiency. It needs a text vocabulary and training on relevance pairs.

### Concatenation with scaling

If both parts are L2-normalised, the inner product of [√α·dense, √(1−α)·sparse] vectors equals α·cos_dense + (1−α)·cos_sparse. (Algebra, not a cited result.) So concatenation is the convex combination of two cosines, in a single vector that one index can search. Bruch et al.'s point about normalisation applies: the two scores must be on comparable scales before mixing, or α only compensates for the scale.

### Unseen items in the sparse part

A bag-of-cards vector has one dimension per seen card. An unseen card has no dimension and no playability-based weight. [prior-art.md](prior-art.md) §3 covers how count models drop or smooth such items.

---

## 4. Autoencoders and supervised metric learning

### What autoencoders are and what they need

- **Plain and denoising autoencoders** learn to reconstruct the input through a bottleneck. Denoising autoencoders reconstruct clean inputs from corrupted ones, "a tractable unsupervised objective" (Vincent et al., [JMLR 11, 2010](https://jmlr.org/papers/v11/vincent10a.html)). No labels needed.
- **Variational autoencoders** add a KL term pulling codes towards a prior (Kingma & Welling, [arXiv 1312.6114](https://arxiv.org/abs/1312.6114)). Known pitfall: with a strong decoder, most training runs "consistently set q(z|x) equal to the prior p(z), bringing the kl divergence term … to zero", so the code carries nothing. Remedies were KL annealing and word dropout (Bowman et al., CoNLL 2016, [arXiv 1511.06349](https://ar5iv.labs.arxiv.org/html/1511.06349)).
- **Bag-of-items VAEs.** Mult-VAE (Liang, Krishnan, Hoffman & Jebara, WWW 2018, [arXiv 1802.05814](https://ar5iv.labs.arxiv.org/html/1802.05814)) encodes each user's click vector over items with a multinomial likelihood and an annealed KL weight β. Datasets had 136k–571k users and 17k–41k items. Input and output layers are sized to a fixed item count, so an item unseen at training has no slot.
- **Set autoencoders.** PISA (Kortvelesy, Morad & Prorok, AAMAS 2023, [arXiv 2302.12826](https://arxiv.org/abs/2302.12826)) is a permutation-invariant set autoencoder with a fixed-size code, "significantly lower reconstruction error than existing baselines" and a "similarity-preserving latent space". It was evaluated on multi-agent communication, not retrieval.
- **Denoising autoencoders for sentence vectors.** TSDAE (Wang, Reimers & Gurevych, Findings of EMNLP 2021, [arXiv 2104.06979](https://ar5iv.labs.arxiv.org/html/2104.06979)) needs only ~10K unlabelled sentences and reached "up to 93.1% of the performance of in-domain supervised approaches". The same paper notes that "a strong performance on STS data is not a good indicator for good performance on domain-specific tasks".

### Evidence on autoencoders for neighbour quality

- **Reconstruction is not the same goal as good neighbours.** Hill, Cho & Korhonen, *Learning Distributed Representations of Sentences from Unlabelled Data*, NAACL 2016 ([arXiv 1602.03483](https://ar5iv.labs.arxiv.org/html/1602.03483)). "The optimal approach depends critically on the intended application." The sequential denoising autoencoder was strong on supervised tasks, but "shallow log-linear models work best on unsupervised benchmarks", which compare vectors by cosine. They suggest models with non-linear decoders may give a space whose geometry cosine does not reflect.
- **Reconstruction underperformed correlation objectives** in Wang et al.'s multi-view comparison (§1 above).
- **Autoencoder codes versus TF-IDF.** Salakhutdinov & Hinton, *Semantic Hashing*, IJAR 50(7), 2009 ([pdf](https://www.cs.utoronto.ca/~rsalakhu/papers/semantic_final.pdf)). A deep autoencoder over word-count vectors gave "a much better representation of each document than Latent Semantic Analysis". But "TF-IDF is slightly more accurate than our 128-bit codes when retrieving the top few documents". Using the codes "to filter the documents given to TF-IDF" beat TF-IDF on the whole set.

### Supervised metric learning

- **NCA.** Goldberger, Roweis, Hinton & Salakhutdinov, NIPS 2004 ([record](https://mlanthology.org/neurips/2004/goldberger2004neurips-neighbourhood)). Learns a linear map L (a Mahalanobis metric) to maximise the expected leave-one-out kNN accuracy under a softmax over distances. scikit-learn's `NeighborhoodComponentsAnalysis` ([docs](https://scikit-learn.org/stable/modules/neighbors.html#neighborhood-components-analysis)) "stores a matrix of pairwise distances, taking n_samples ** 2 memory". Each iteration costs O(n_components × n_samples × min(n_samples, n_features)), with full-gradient L-BFGS. Unlike LDA it makes no assumption about class distributions.
- **LMNN.** Weinberger & Saul, [JMLR 10, 2009](https://jmlr.org/papers/v10/weinberger09a.html). A Mahalanobis metric trained so that "the k-nearest neighbors always belong to the same class" and other classes sit beyond a margin; a convex semidefinite program.
- **LDA projection.** scikit-learn's `LinearDiscriminantAnalysis.transform` ([docs](https://scikit-learn.org/stable/modules/lda_qda.html)) projects to a space of dimension "necessarily less than the number of classes". It assumes Gaussian classes with a shared covariance. Shrinkage (Ledoit-Wolf) regularises the covariance when samples are few, with the `lsqr` or `eigen` solvers.
- **Proxy losses.** Movshovitz-Attias et al., *No Fuss Distance Metric Learning using Proxies*, ICCV 2017 ([arXiv 1703.07464](https://arxiv.org/abs/1703.07464)). Each anchor is compared with learned class proxies rather than sampled triplets. The loss is "a tight upper bound of the original loss", "empirically better behaved", and converged "three times as fast".
- **Supervised contrastive loss.** Khosla et al., NeurIPS 2020 ([arXiv 2004.11362](https://arxiv.org/abs/2004.11362)). Pulls same-class points together and pushes other classes apart, using all same-class items in a batch. It beat cross-entropy and was more stable across hyperparameters.
- **Caution on reported gains.** Musgrave, Belongie & Lim, *A Metric Learning Reality Check*, ECCV 2020 ([arXiv 2003.08505](https://ar5iv.labs.arxiv.org/html/2003.08505)). Under fair, tuned comparisons, accuracy is roughly flat across years: newer losses perform about the same as the 2006 contrastive and triplet losses.

---

## Our reading (interpretation, not a research finding)

Short notes linking the findings to our case. None of this has been tested.

- The near-tie misses match the match-kernel description. Today's cosine is an average over all card pairs, so 50 shared shell cards outweigh 4 differing ones (the Blink vs Nadu Combo example). The fixes the literature uses for this are: per-item weights before pooling (SIF-style a/(a+playability), which needs no labels and gives an unseen card the weight of a never-played card), square-rooting copy counts, extra pooled statistics (max, min, or codebook blocks), and a sparse rarity-weighted score fused with the dense one.
- A linear projection (LDA, NCA, whitening) applied after the mean is the same as projecting every card and then averaging. It can reweight dimensions but cannot undo dilution by many shared cards. Anything that changes per-card weights, applies a non-linear φ before pooling, or adds non-mean statistics can.
- Hybrid fusion fits the evidence we already have: dense handles unseen cards, sparse handles rare exact cards. Concatenating unit-length dense and sparse vectors with √α weights gives the convex combination in one cosine. The sparse part gives nothing for unseen cards, so the dense part must carry them.
- Autoencoders look like the wrong tool for this question. We have ~200k labelled decks, and labels are what defines a good neighbour. The cited work finds reconstruction objectives misaligned with cosine neighbours, and item-ID autoencoders cannot represent unseen cards. A content-input set autoencoder could, but nothing found tests one for retrieval.
- Rough CPU costs, from arithmetic only. 84,000 × 256 float32 is about 86 MB, and one brute-force cosine query is about 21.5 million multiply-adds. Concatenated pooling multiplies both by the number of blocks (×3 for min/mean/max; ×K for VLAD). Full NCA in scikit-learn would need an 84,000² matrix (about 28 GB in float32), so it would need subsampling, class centroids or mini-batches. LDA on 256 to ~800 dimensions is cheap. WMD against every training row is not, but prefetch-and-prune over a shortlist from the current mean might be.

| Method | Labels | Unseen cards | Rough CPU cost (our estimate) | Fits NN ranking |
|---|---|---|---|---|
| Concatenation with block weights | No (weights tuned on eval) | Yes | None | Yes |
| CCA / DCCA | No (paired views) | Yes | Low / medium training | Yes, via projection |
| Late score fusion (convex, RRF) | α tuned | Through dense part | Two searches | Yes |
| SIF / IDF-weighted mean, common-component removal | No | Yes (weight for zero playability) | Negligible | Yes |
| Signed square root, L2 normalisation | No | Yes | Negligible | Yes |
| Min / max / p-mean concatenation | No | Yes | ×blocks in memory and search | Yes |
| BoV / VLAD / Fisher | No (k-means, GMM) | Yes | k-means fit; ×K vector length | Yes |
| Attention pooling, Deep Sets, Set Transformer, NetVLAD | Yes | Yes (content input) | Neural training; cheap inference | Yes, if trained for it |
| OTKE | Optional | Yes | Medium | Yes |
| WMD / Sinkhorn / late interaction | No | Yes | High per pair; rerank shortlist | Reranking only |
| Sparse + dense hybrid | α tuned | Dense part only | Sparse index plus dense | Yes |
| Autoencoder (plain, denoising, VAE, set) | No | Only with content input | Neural training | Weak evidence |
| LDA / NCA / LMNN / proxy / contrastive | Yes | Yes (applied to content vectors) | LDA low; NCA n² unless batched; neural losses need training | Yes, designed for it |

## Could not verify / open gaps

- SIF's full paper (OpenReview blocked): the weighting formula and component removal come from the official code, and the 10%–30% gain from the abstract.
- Jégou et al.'s burstiness paper and VLAD paper (HAL blocked). Their content is taken from Sánchez et al.'s 2013 summary.
- Sivic & Zisserman's Video Google weighting and stop list (PDF not reachable).
- Snoek et al.'s early-versus-late fusion result is from the abstract as shown in search results; the PDF was not read.
- Whether MKL beats a plain sum of kernels (Gönen & Alpaydın full text not read).
- ColBERT's MaxSim formula (full text not read).
- No source found that evaluates any of these pooling methods on card games, or a set autoencoder for nearest-neighbour retrieval.
- Some venues were not shown on the arXiv pages read and are given from the proceedings as commonly cited: Hill et al. (NAACL 2016), Luan et al. (TACL 2021), TSDAE (Findings of EMNLP 2021), Musgrave et al. (ECCV 2020), Khosla et al. (NeurIPS 2020), Bruch et al. (ACM TOIS 2023, matching the DOI on arXiv).
- All reported numbers are the authors' own and were not reproduced.
