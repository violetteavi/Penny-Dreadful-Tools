# Visualising deck space

Research for issue #64 (Archetype geometry: typical lists, defining cards and analogies in the deck-vector space), commissioned during the grilling of #62 (Deck diffs: what the cards kept, removed and added between two decks look like), before the two were split. Compiled 2026-10-16. Findings only: this document does not recommend an approach, and no experiments were run.
Terms follow [CONTEXT.md](../../CONTEXT.md) (deck vector, card weight, training row, label, archetype tree, top-level, parent and leaf archetype, season, candidates).
It builds on [combining-vectors.md](combining-vectors.md), which covers how deck vectors are formed, and does not repeat it.

## The question

Issues #64 and #62 explore the "IDF-average space". Each deck vector is the sum of its cards' combined embedding rows, each times √copies and its card weight, at unit length. That is a few hundred dimensions: a 256-d text embedding plus scaled card numbers. Decks are compared by cosine. There are about 84,000 training rows and hundreds of archetypes in the archetype tree. About 37% of decks are labelled at a parent archetype.

The exploration wants pictures of:

1. What archetypes look like in the space: how cohesive each is, how they overlap, and whether parent-labelled decks sit between their children.
2. Drift by season.
3. Deck diffs: the cards added and removed between a deck and its nearest training row.
4. Vector analogies, such as Orzhov Control − Orzhov Midrange + Mono Black Midrange ≈ Mono Black Control.

The output is a static results PDF made with matplotlib. An interactive page may follow.

This note asks which visualisations exist for high-dimensional labelled data, and which can be trusted for this data:

1. 2-D projections, what each preserves, and its pitfalls.
2. How to measure a projection's faithfulness.
3. Views that avoid a 2-D projection.
4. Showing vector arithmetic and difference vectors honestly.
5. Interactive tools for 84,000 points with labels and metadata.

## Summary

- **No 2-D projection keeps both neighbours and distances, so every picture of the full space distorts it.** Going from hundreds of dimensions to 2 "inevitably induces significant distortion" (Chari & Pachter, [PLoS Comput Biol 2023](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011288)). In their single-cell datasets, on average over 70% of each point's 30 nearest neighbours in t-SNE and UMAP plots were not its neighbours in the original space. They suggest treating such plots "as cartoon diagrams to be displayed post-analysis". The PaCMAP authors frame it as a trade-off: methods "can either handle one or the other, but not both" of local and global structure ([Wang et al., JMLR 2021](https://jmlr.org/papers/v22/20-1061.html)).
- **In t-SNE and UMAP plots, cluster sizes and the gaps between clusters are not reliable.** In t-SNE "you cannot see relative sizes of clusters", and "distances between well-separated clusters ... may mean nothing" ([Wattenberg, Viégas & Johnson, Distill 2016](https://distill.pub/2016/misread-tsne/)). UMAP "does not completely preserve density" and "can also create false tears in clusters" ([umap-learn docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)). The UMAP FAQ does say one of its goals is for distances between clusters to be meaningful ([FAQ](https://umap-learn.readthedocs.io/en/latest/faq.html)). Kobak & Linderman found that UMAP's better global layout came from its initialisation, not its algorithm ([Nat Biotechnol 2021](https://www.biorxiv.org/content/10.1101/2019.12.19.877522v1)).
- **Settings, initialisation and seeds change the picture.** t-SNE needs plots at several perplexities (Distill). With PCA initialisation the outcome is "reproducible" (Kobak & Berens, [Nat Commun 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6882829/)). In UMAP, setting `random_state` turns off most multithreading ([docs](https://umap-learn.readthedocs.io/en/latest/reproducibility.html)). PaCMAP's authors say TriMap's global structure "comes from an unexpected source, namely its initialization".
- **All the main methods handle 84,000 points and cosine.** Deck vectors are unit length, so Euclidean distance ranks neighbours exactly as cosine does. openTSNE uses that fact itself ([source](https://github.com/pavlin-policar/openTSNE/blob/master/openTSNE/nearest_neighbors.py)). On their 2021 hardware, PaCMAP, UMAP and TriMap each embedded the 70,000-point MNIST dataset in about a minute, and t-SNE took 14 minutes (Wang et al., Table 5). MDS and scikit-learn's `trustworthiness` both build full n × n matrices, so at 84,000 points they need a sample or archetype centroids.
- **Faithfulness can be measured, and the measures work without a picture.** Trustworthiness penalises false neighbours and continuity penalises missing ones. The Shepard diagram plots every original distance against its 2-D distance. Neighbourhood hit is the share of each point's 2-D neighbours that share its label ([Espadoto et al., TVCG 2021](https://webspace.science.uu.nl/~telea001/uploads/PAPERS/TVCG19/paper.pdf)). Venna et al. frame a plot as an information-retrieval task with a precision–recall trade-off ([JMLR 2010](https://jmlr.org/papers/v11/venna10a.html)). PaCMAP's authors score global structure as the share of random triplets whose distance order survives. A labelled variant uses class centroids instead of points.
- **Views without a projection keep exact numbers.** These include centroid similarity heatmaps ordered by the archetype tree or by clustering, dendrograms, silhouette plots, distance-to-centroid distributions and cluster-level graphs. Chari & Pachter recommend "dendrograms and trees" and "graph-based network diagrams" that "do not seek to display all point-wise information". PAGA draws one node per cluster, with edges weighted by connectivity, and preserves "the global topology of data" (Wolf et al., [Genome Biol 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6425583/)).
- **Analogy results depend on how the nearest-neighbour search is set up.** If the inputs are not excluded, the nearest word to a\* − a + b "was b in 93% of the cases" (Linzen, [RepEval 2016](https://arxiv.org/abs/1606.07736)). Even with them excluded, much of the success comes from b's neighbourhood. Linzen asks for an ONLY-B baseline (the nearest neighbour of b) to be reported alongside. With unit vectors, the offset method is a sum of three cosines, and one large term can dominate. 3CosMul balances the terms (Levy & Goldberg, [CoNLL 2014](https://aclanthology.org/W14-1618/)). Standard analogy code silently refuses to return input words, and this has produced misleading bias results (Nissim et al., [Computational Linguistics 2020](https://aclanthology.org/2020.cl-2.7/)).
- **Interactive tools.** These differ in where the data goes and in how many points they really project. Apple's Embedding Atlas is MIT-licensed and pip-installable. It can run in the browser with DuckDB-WASM, and it renders "up to a few million points" ([paper](https://arxiv.org/html/2505.06386)). Nomic Atlas is "a cloud-based platform" ([docs](https://docs.nomic.ai/atlas/embeddings-and-retrieval/guides/how-to-visualize-embeddings)). TensorFlow's Embedding Projector runs t-SNE on a 10,000-point sample and UMAP on a 5,000-point sample ([source](https://github.com/tensorflow/tensorboard/blob/master/tensorboard/plugins/projector/vz_projector/data.ts)). DataMapPlot takes several label layers, finest first, and writes a self-contained HTML file. Plotly's WebGL traces handle "up to around a million points" ([docs](https://plotly.com/python/performance/)).

---

## 1. Projections

### What applies to every method here

- **Cosine and unit vectors.** For unit vectors a and b, ‖a − b‖² = 2 − 2·cos(a, b), so Euclidean nearest neighbours are exactly cosine nearest neighbours. (Algebra, not a cited finding.) openTSNE's code relies on this: "The nearest neighbor ranking for cosine distance is the same as for euclidean distance on normalized data" ([nearest_neighbors.py](https://github.com/pavlin-policar/openTSNE/blob/master/openTSNE/nearest_neighbors.py)). So a method that only offers Euclidean distance still uses the right neighbours for deck vectors. Distances differ only by a monotone transform. Archetype centroids are not unit length (see §3), so this does not hold for them unless they are renormalised.
- **Scale.** scikit-learn's manifold guide says all these methods "are based on a nearest-neighbor search", so features need the same scale ([guide](https://scikit-learn.org/stable/modules/manifold.html)). For deck vectors, the relative scale of the text block and the card-numbers block is already fixed by the combined embedding's weights.
- **Large scatter plots in a PDF.** Drawing 84,000 points as vectors makes large, slow PDFs. Matplotlib can rasterise one artist while axes and text stay vector: "Setting rasterization only affects vector backends such as PDF, SVG, or PS", and resolution comes from the `dpi` passed to `savefig` ([demo](https://matplotlib.org/stable/gallery/misc/rasterization_demo.html)). The UMAP FAQ says "the real solution, particular with large datasets, is to use datashader", which aggregates points instead of overplotting them ([FAQ](https://umap-learn.readthedocs.io/en/latest/faq.html)).

### PCA

- Linear. It keeps the directions of largest variance, so it favours global over local structure. PHATE's authors criticise it for this ([Moon et al., Nat Biotechnol 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC7073148/)).
- Deterministic and fast. scikit-learn notes t-SNE "can take several hours on million-sample datasets where PCA will finish in seconds or minutes" ([guide](https://scikit-learn.org/stable/modules/manifold.html)).
- Classical MDS on Euclidean distances "is equivalent to PCA applied to this set of vectors" (same page).
- In the Espadoto et al. survey, "Of the techniques that do not require parameter tuning, PCA is the best performing, albeit with lower quality than that of the best projections" ([TVCG 2021](https://webspace.science.uu.nl/~telea001/uploads/PAPERS/TVCG19/paper.pdf), §8.1).
- Chari & Pachter found neighbourhoods were poorly kept even between 2-D embeddings and their own PCA input: Jaccard distances "consistently above 0.8 on average".

### MDS (metric, non-metric, classical)

- Metric MDS fits 2-D distances to the input dissimilarities by minimising stress, the sum of (d̂ᵢⱼ − dᵢⱼ(Z))². Non-metric MDS keeps only their order: "If δᵢⱼ > δₖₗ, then the embedding seeks to enforce dᵢⱼ(Z) > dₖₗ(Z)" ([scikit-learn guide](https://scikit-learn.org/stable/modules/manifold.html)).
- scikit-learn's `MDS` uses SMACOF. It accepts a `metric` string (anything `pdist` accepts, so cosine) or `"precomputed"` with a square distance matrix ([API](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.MDS.html)). It stores `dissimilarity_matrix_` as n × n. At 84,000 points that is about 7 × 10⁹ entries, or 56 GB in float64. (Arithmetic, not stated by the docs.) MDS over hundreds of archetype centroids is small.
- `stress_` guide values from the API page: 0.025 excellent, 0.05 good, 0.1 fair, 0.2 poor. In version 1.9 the default `n_init` changed to 1, and the default `init` will become `classical_mds` in 1.10.

### t-SNE (scikit-learn, openTSNE, FIt-SNE)

- **What it keeps.** Local neighbourhoods. The original paper reduces "the tendency to crowd points together in the center of the map" and aims at a map that "reveals structure at many different scales" (van der Maaten & Hinton, [JMLR 2008](https://jmlr.org/papers/v9/vandermaaten08a.html)). scikit-learn's guide: "Global structure is not explicitly preserved. This problem is mitigated by initializing points with PCA."
- **Distortions** (Wattenberg et al., [Distill 2016](https://distill.pub/2016/misread-tsne/)):
  - Cluster sizes: "density equalization happens by design", so "you cannot see relative sizes of clusters in a t-SNE plot."
  - Gaps: "distances between well-separated clusters in a t-SNE plot may mean nothing."
  - Noise: low perplexity makes clumps in random data. "Recognizing these clumps as random noise is an important part of reading t-SNE plots."
  - Perplexity: "Getting the most from t-SNE may mean analyzing multiple plots with different perplexities."
  - Convergence: "there's no fixed number of steps that yields a stable result"; "pinched" shapes suggest stopping too early.
- **Practice at scale** (Kobak & Berens, [Nat Commun 10:5416, 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6882829/)):
  - With random initialisation, "the relative position of clusters on the t-SNE plot is almost arbitrary", and it "often strongly depends on the random seed". PCA initialisation "makes the t-SNE outcome reproducible".
  - A learning rate of n/12; "whenever n∕100≫30, combine perplexity 30 with the large perplexity n∕100"; exaggeration of about 4 "for very large data sets".
  - Exact t-SNE is "computationally unfeasible for n≫10,000". Barnes-Hut "becomes very slow for n≫100,000". FIt-SNE's interpolation is O(n): 1 million points in "29 min" on four cores.
  - t-SNE "does not construct any mapping f(x)". New points can be placed at the median 2-D position of their k nearest reference points.
- **FIt-SNE.** Linderman et al., *Fast interpolation-based t-SNE*, Nat Methods 16:243–245, 2019 ([arXiv 1712.09005](https://arxiv.org/abs/1712.09005)). It targets datasets of "hundreds of thousands to millions" of points.
- **openTSNE.** Poličar, Stražar & Zupan, J. Stat. Softw. 109(3), 2024 ([docs](https://opentsne.readthedocs.io/en/latest/)).
  - Defaults ([API](https://opentsne.readthedocs.io/en/latest/api/index.html)): `initialization='pca'`, `negative_gradient_method='auto'` (Barnes-Hut for small data, FFT interpolation for large), `learning_rate='auto'` (N / exaggeration), and `n_jobs=1`.
  - Supported metrics include cosine (its Annoy and scikit-learn neighbour back ends list it).
  - `transform` adds new points to an existing embedding. "Each point is optimized only against the existing embedding", so the new points do not interact with each other. That suits placing a later season's decks on a map fitted to earlier seasons.
- **scikit-learn `TSNE`** ([API](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)). `init='pca'` has been the default since 1.2. Barnes-Hut is O(N log N), "only works when the target dimensionality is 3 or less", and can embed "hundreds of thousands of data points" ([guide](https://scikit-learn.org/stable/modules/manifold.html)). `metric` accepts any `pdist` metric. "The KL divergence is not convex", so different initialisations reach different local minima.

### UMAP, supervised UMAP, densMAP, AlignedUMAP

- **Claims.** The abstract says UMAP "arguably preserves more of the global structure with superior run time performance" than t-SNE (McInnes, Healy & Melville, [arXiv 1802.03426](https://arxiv.org/abs/1802.03426)). The FAQ: "One of UMAPs goals is to have distance between clusters of points be meaningful."
- **Counter-evidence.**
  - Kobak & Linderman, *Initialization is critical for preserving global data structure in both t-SNE and UMAP*, Nat Biotechnol 39:156–157, 2021 ([preprint](https://www.biorxiv.org/content/10.1101/2019.12.19.877522v1)). The "alleged superiority of UMAP can be entirely attributed to different choices of initialization". "UMAP with random initialization preserves global structure as poorly as t-SNE with random initialization."
  - Böhm, Berens & Kobak ([JMLR 23, 2022](https://jmlr.org/papers/v23/21-0055.html)): "UMAP embeddings correspond to t-SNE with increased attraction". Stronger attraction shows continuous structure better. Stronger repulsion separates discrete clusters better and gives higher kNN recall.
  - The umap-learn docs: UMAP "does not completely preserve density" and "can also create false tears in clusters, resulting in a finer clustering than is necessarily present in the data" ([clustering page](https://umap-learn.readthedocs.io/en/latest/clustering.html)).
- **Parameters** ([parameters](https://umap-learn.readthedocs.io/en/latest/parameters.html), [API](https://umap-learn.readthedocs.io/en/latest/api.html)). `n_neighbors` (default 15) "controls how UMAP balances local versus global structure". `min_dist` (default 0.1) "controls how tightly UMAP is allowed to pack points together". `init='spectral'` by default. `metric='cosine'` is supported.
- **Seeds.** "UMAP is a stochastic algorithm." Setting a seed turns off "the multi-threading that does not support explicit reproducibility", so seeded runs are slower ([reproducibility](https://umap-learn.readthedocs.io/en/latest/reproducibility.html)).
- **New points.** `transform` assumes the new data's distribution matches the training data. The docs point to Parametric UMAP for cases where "this can go wrong" ([transform](https://umap-learn.readthedocs.io/en/latest/transform.html)).
- **Supervised and semi-supervised UMAP** ([docs](https://umap-learn.readthedocs.io/en/latest/supervised.html)).
  - Passing labels gives clean class separation, "which is expected – we gave the algorithm all the class information".
  - `target_weight` runs from 0.0 ("weights predominantly on data") to 1.0 ("a strong emphasis on target"); the default 0.5 balances them. Label −1 means unlabelled.
  - The default `target_metric='categorical'` only measures "whether categories match or are different" ([source docstring](https://github.com/lmcinnes/umap/blob/master/umap/umap_.py)). So it would treat a parent archetype as one more flat class, unrelated to its children. (Reading of the docstring; not tested.)
- **densMAP.** Narayan, Berger & Cho, Nat Biotechnol 39:765–774, 2021 ([preprint](https://www.biorxiv.org/content/10.1101/2020.05.12.077776v1)). t-SNE and UMAP "neglect the local density of data points in the original space", so "densely populated subpopulations of cells are given more visual space". densMAP adds the local density as a regulariser, weighted by `dens_lambda` (default 2.0). It is "a little slower than standard UMAP" ([demo](https://umap-learn.readthedocs.io/en/latest/densmap_demo.html)). Chari & Pachter found their arbitrary-shape "Picasso" embeddings scored comparably even to den-SNE and densMAP on their distance measures.
- **AlignedUMAP** ([docs](https://umap-learn.readthedocs.io/en/latest/aligned_umap_basic_usage.html)) embeds a sequence of related datasets, such as time slices, together. Points shared by consecutive slices are linked by a relation dictionary. `alignment_regularisation` sets how hard they are kept in place, and `alignment_window_size` sets how many neighbouring slices count. It "only supports sequences of datasets with relations between each consecutive pair". That fits seasons when the same training rows or archetype centroids appear in neighbouring seasons.

### PaCMAP

- Wang, Huang, Rudin & Shaposhnik, *Understanding How Dimension Reduction Tools Work*, [JMLR 22(201), 2021](https://jmlr.org/papers/v22/20-1061.html) ([arXiv](https://ar5iv.labs.arxiv.org/html/2012.04456)).
- **How it works.** It uses three kinds of pair. Neighbour pairs attract, "mid-near" pairs attract weakly to keep global structure, and further pairs repel. Their weights change over three optimisation phases.
- **Evaluation.**
  - Local structure: kNN and SVM accuracy in the embedding.
  - Global structure: "Random Triplet Accuracy", the share of sampled triplets whose distance order survives, and a centroid version for labelled data.
  - Findings: "methods that favor preservation of local structure (UMAP, t-SNE) tend to perform better on local-preservation metrics", while "global structure metrics are where algorithms like PaCMAP and TriMap really shine".
  - "Unlike UMAP and TriMap, which gain their global structure through initialization ... PaCMAP creates the global structure completely through its graph component selection."
  - On t-SNE and UMAP: "t-SNE can be very sensitive to the perplexity parameter and creates spurious clusters", and on MNIST it created "false clusters".
- **Runtime** (Table 5; 2× Xeon E5-2640 v4; 70,000 MNIST points): t-SNE 14:02, LargeVis 20:19, UMAP 1:09, TriMap 1:14, PaCMAP 0:52. On 3–4 million points, LargeVis and UMAP ran out of the 64 GB memory limit and t-SNE did not finish in 24 hours. (Their t-SNE was the Belkina et al. implementation, not openTSNE.)
- **Package** ([README](https://github.com/YingfanWang/PaCMAP)): `n_neighbors=10` for data under 10,000 points, and 10 + 15·(log₁₀ n − 4) above that (about 17 at 84,000). `MN_ratio=0.5`, `FP_ratio=2`, and `init='pca'` by default. The README warns that changing these "will affect the result of dimension reduction significantly". The source supports `distance` of euclidean, manhattan, angular ("i.e. cosine") or hamming ([pacmap.py](https://github.com/YingfanWang/PaCMAP/blob/master/source/pacmap/pacmap.py)).

### TriMap

- Amid & Warmuth, [arXiv 1910.00204](https://arxiv.org/abs/1910.00204). It is built on triplet constraints ("a is more similar to b than to c"). It claims better global structure than t-SNE, LargeVis and UMAP, handles millions of points, and introduces a global score based on how clusters are placed relative to each other.
- PaCMAP's authors show "TriMap's ability to preserve global structure comes from an unexpected source, namely its initialization", and that "TriMap also struggles with local structure sometimes".
- The source supports angular ("i.e. cosine") distance ([trimap_.py](https://github.com/eamid/trimap/blob/master/trimap/trimap_.py)).

### PHATE

- Moon et al., *Visualizing structure and transitions in high-dimensional biological data*, [Nat Biotechnol 37:1482–1492, 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC7073148/). It "captures both local and global nonlinear structure using an information-geometric distance".
- **How it works.** It builds a diffusion operator from local affinities, powers it to t steps, compares points by a "potential distance" between log-transformed transition probabilities, and embeds that distance with metric MDS.
- It is designed for "continual progressions, branches, and clusters", and its authors criticise t-SNE for shattering trajectories into clusters.
- **Scale.** "For N much larger than 50000, computational complexity can become an issue". A landmark version handles this (`n_landmark=2000` by default). The paper reports 2.5 hours for 1.3 million cells.
- **Cosine.** `knn_dist` and `mds_dist` both list 'cosine' as a recommended value ([phate.py](https://github.com/KrishnaswamyLab/PHATE/blob/main/Python/phate/phate.py)).

### LargeVis

- Tang, Liu, Zhang & Mei, WWW 2016 ([arXiv 1602.00370](https://arxiv.org/abs/1602.00370)). It builds an approximate kNN graph, then lays the graph out with asynchronous SGD in linear time, for "millions of high-dimensional data points".
- The official code is C++ with a Python wrapper that needs GSL to build. Its repository was last pushed in May 2023 ([GitHub](https://github.com/lferry007/LargeVis)).
- In PaCMAP's benchmark it was the slowest method on 70,000 points (20 minutes).

### LDA as a supervised projection

- LDA projects "to a linear subspace consisting of the directions which maximize the separation between classes". The output dimension "is necessarily less than the number of classes". It assumes Gaussian classes with a shared covariance ([scikit-learn](https://scikit-learn.org/stable/modules/lda_qda.html)). A 2-D LDA plot shows the two most discriminating directions out of up to (classes − 1).
- Like supervised UMAP, it uses the labels it is asked to show, so class separation in the plot is partly by construction. A parent archetype is one more class to LDA. (Our reading.)

### Comparison

| Method | Preserves | 84k points | Cosine | Main pitfall |
|---|---|---|---|---|
| PCA | Global linear variance; exact, deterministic | Seconds | Equivalent on unit vectors (centred) | Hundreds of archetypes overlap in two linear directions; little local structure |
| MDS (metric / non-metric) | Pairwise distances / their order (stress) | n × n matrix (~56 GB at 84k); fine for centroids | `metric='cosine'` or precomputed | Quadratic memory; SMACOF local minima |
| t-SNE (openTSNE, FIt-SNE, sklearn BH) | Local neighbourhoods | Yes (FFT O(n); BH up to ~100k) | openTSNE: yes; sklearn: any `pdist` metric | Cluster sizes and gaps meaningless; perplexity; random init makes layout arbitrary |
| UMAP | Local; some global with spectral init (disputed) | Yes (~1 min on 70k, 2021) | `metric='cosine'` | `n_neighbors`/`min_dist`; false tears; density lost; seeds vs threads |
| Supervised UMAP / LDA | Label separation plus data structure | Yes | UMAP yes; LDA linear | Separation shown is partly put there by the labels; labels treated as flat classes |
| densMAP | UMAP plus relative local density | Yes, a little slower | Yes | Still a 2-D neighbour embedding |
| PaCMAP | Local and global (mid-near pairs) | Yes (~1 min on 70k) | `distance='angular'` | Parameters change results "significantly" |
| TriMap | Global (triplets), mainly via init | Yes | Angular | Global layout comes largely from PCA init; weaker local |
| PHATE | Continuous progressions, branches | Landmarks needed above ~50k | `knn_dist='cosine'` | Built for trajectories, not many discrete classes |
| LargeVis | Local (kNN graph layout) | Designed for millions | Not checked | Unmaintained build; slow in PaCMAP's benchmark |

---

## 2. Measuring a projection's faithfulness

- **Trustworthiness and continuity** (Venna & Kaski, ICANN 2001). These are rank-based and lie in [0, 1].
  - Trustworthiness penalises points that are among the k nearest in 2-D but not in the original space, each in proportion to its original rank. "Any unexpected nearest neighbors in the output space are penalised in proportion to their rank in the input space" ([scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.trustworthiness.html)).
  - Continuity is the mirror: original neighbours missing from the 2-D neighbourhood. Espadoto et al.: trustworthiness "tells how much one can trust that local patterns in a projection, e.g., clusters, represent actual patterns in the data" ([TVCG 2021](https://webspace.science.uu.nl/~telea001/uploads/PAPERS/TVCG19/paper.pdf), §6; they use k = 7).
  - scikit-learn has `trustworthiness(X, X_embedded, n_neighbors=5, metric=...)`, which accepts cosine. It requires k < n/2. It builds a dense n × n distance matrix, its argsort and an n × n inverted index ([source](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/manifold/_t_sne.py)). At 84,000 points that is three matrices of 7 × 10⁹ entries, so it needs a sample. (Memory arithmetic ours.) scikit-learn has no continuity function.
- **Co-ranking matrix and R_NX(K).** Lee & Verleysen, *Quality assessment of dimensionality reduction: Rank-based criteria*, Neurocomputing 72(7–9):1431–1443, 2009. A co-ranking matrix compares neighbour ranks before and after projection. Trustworthiness, continuity and "intrusions" versus "extrusions" are blocks of it ([summary via the R coRanking package](https://cloud.r-project.org/web/packages/coRanking/refman/coRanking.html)). R_NX(K) is 0 for a random embedding and 1 for a perfect one, at each neighbourhood size K.
- **Neighbour retrieval precision and recall.** Venna, Peltonen, Nybo, Aidos & Kaski ([JMLR 11, 2010](https://jmlr.org/papers/v11/venna10a.html)) treat a plot as a tool "to find similar data based on the similarities shown on the display", with "the fundamental tradeoff between precision and recall". kNN recall (the share of each point's k original neighbours that are among its k 2-D neighbours) is the measure behind Chari & Pachter's Jaccard figures and Böhm et al.'s attraction–repulsion results.
- **Shepard diagram and Shepard goodness.** The Shepard diagram is "a scatterplot of the pairwise (Euclidean) distances" in the original space against those in 2-D. Shepard goodness is its Spearman rank correlation. Normalised stress measures distance preservation directly (Espadoto et al., §6, Table 5). These are global, distance-based checks. They complement the rank-based local measures above.
- **Neighbourhood hit** is the share of each point's k 2-D neighbours that have the same label, averaged over points (Espadoto et al.). It measures label separation in the picture, not faithfulness to the original space. The same measure in the original space gives a baseline to compare with. (Our reading.)
- **Global structure with labels.** PaCMAP's "centroid triplet accuracy" checks whether the order of distances among class centroids survives the projection ([paper](https://ar5iv.labs.arxiv.org/html/2012.04456), §8). Chari & Pachter used correlations between neighbour rankings of cell types. They found them "≤ 0.4" in 2-D and at least a third lower than in higher-dimensional PCA spaces.
- **Results depend on the measure and its settings.** Espadoto et al. found "the four overall best performing techniques (t-SNE, UMAP, IDMAP and PBC) require some tuning effort over most parameters to yield optimal results". The PaCMAP paper's tables rank methods differently on local and global measures.

---

## 3. Views that avoid a 2-D projection

- **Archetype centroids and cohesion.** For unit vectors x₁…xₙ with mean m, ‖m‖² is the average of cos(xᵢ, xⱼ) over all ordered pairs, including each vector with itself. So a centroid's length is a direct cohesion measure, and an archetype whose decks agree has a longer centroid. Cosine between two centroids renormalises them. (Algebra, not a cited finding.)
- **Similarity heatmaps between centroids.** seaborn's `clustermap` draws a "hierarchically-clustered heatmap" with dendrograms. It accepts precomputed `row_linkage` and `col_linkage`, and `row_colors` bars can mark one or more label levels ([docs](https://seaborn.pydata.org/generated/seaborn.clustermap.html)). The rows can also be ordered by the archetype tree instead of by clustering. Ordering by data-driven clustering and by the tree answer different questions: what the space groups together, versus whether the tree's groups are compact.
  - SciPy's `optimal_leaf_ordering` reorders a linkage "to minimize the distance between adjacent leaves" without changing the tree ([docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.optimal_leaf_ordering.html)).
  - `cophenet` gives the cophenetic correlation, which measures how well a dendrogram's merge heights reproduce the original distances ([docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.cophenet.html)).
- **Confusion-style heatmaps from neighbours.** For each archetype, the share of its decks' k nearest training rows that carry each other label. This is neighbourhood hit split by label pair, computed in the original space, so nothing is lost to projection. (Our reading; it is the original-space version of Espadoto et al.'s measure.)
- **Dendrograms and cluster-level graphs.** Chari & Pachter suggest "hierarchical relationship diagrams such as dendrograms and trees" and "graph-based network diagrams". They also recommend "higher-level diagrams that do not seek to display all point-wise information". PAGA is one such graph: "A PAGA graph is obtained by associating a node with each partition and connecting each node by weighted edges", and "PAGA maps preserve the global topology of data" (Wolf et al., [Genome Biol 20:59, 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6425583/)). With archetypes as the partitions, edge weights would show which archetypes' decks are neighbours. PAGA positions can also initialise a 2-D embedding: "PAGA-initialized single-cell embeddings are faithful to the global topology".
- **Silhouette plots.** For each point, s = (b − a) / max(a, b), where a is the mean distance within its own cluster and b is the mean distance to the nearest other cluster. Values near 0 "indicate overlapping clusters" ([scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_samples.html)). Any `pairwise_distances` metric works, including cosine. `silhouette_score` has a `sample_size` argument for large data ([docs](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)); `silhouette_samples` does not. Labels at different depths of the tree overlap by definition. A parent archetype's decks are expected to be near its children, so a low silhouette for a parent is not by itself a defect. (Our reading.)
- **Distance-to-centroid distributions** (box or violin plots of cosine to the own centroid and to the nearest other centroid, one row per archetype). These show spread and outliers per archetype. They are one-dimensional summaries of the same quantities silhouette uses. (No specific source found; standard practice.)
- **Hierarchy-aware views.** Whether parent-labelled decks sit between their children can be checked without a picture. Compare each parent-labelled deck's cosine to its parent's centroid and to each child's centroid. The same comparison applies to a deck's position along the segment between two child centroids. (Our reading.) Poincaré embeddings learn hyperbolic coordinates that "outperform Euclidean embeddings significantly on data with latent hierarchies" (Nickel & Kiela, [arXiv 1705.08039](https://arxiv.org/abs/1705.08039)). They embed a hierarchy or graph, not given vectors, so they would show the tree rather than deck space.
- **Small multiples.** One panel per archetype (or per season), each showing that subset on shared axes, or over a grey background of all decks. With a shared fitted projection, openTSNE's `transform` and UMAP's `transform` place each subset on the same map. AlignedUMAP is the joint alternative for seasons (§1).
- **Parallel coordinates.** pandas has `parallel_coordinates(frame, class_column, ...)` ([docs](https://pandas.pydata.org/docs/reference/api/pandas.plotting.parallel_coordinates.html)). With hundreds of uninterpretable text-embedding dimensions, the axes would carry no meaning. The card-numbers block (mana value, colours, stats) has named dimensions and is short. (Our reading.)

---

## 4. Vector arithmetic, analogies and difference vectors

- **The offset method.** Mikolov, Yih & Zweig, *Linguistic Regularities in Continuous Space Word Representations*, NAACL 2013, pp. 746–751 ([anthology](https://aclanthology.org/N13-1090/)). It answers a : a\* :: b : ? with the nearest neighbour of a\* − a + b. In the example from the brief: a = Orzhov Midrange, a\* = Orzhov Control, b = Mono Black Midrange, expected b\* = Mono Black Control.
- **The input words must be excluded, and that matters.** Linzen, *Issues in evaluating semantic spaces using word analogies*, RepEval 2016, pp. 13–18 ([arXiv 1606.07736](https://arxiv.org/abs/1606.07736)).
  - Without exclusion, "the nearest neighbor of a∗− a + b was b in 93% of the cases and a∗ in 5% of the cases (it was never a)".
  - "Most studies exclude a, a∗ and b from consideration." Linzen notes this heuristic, though reasonable, puts "into question the interpretation of the success of the analogy solver as evidence for the geometric organization of the underlying semantic space".
  - He gives baselines that ignore the offset. ONLY-B returns the nearest neighbour of b. IGNORE-A returns the nearest neighbour of a\* + b. ADD-OPPOSITE uses −(a\* − a) + b. REVERSE applies the method backwards. IGNORE-A "outperformed ONLY-B in ten out of 14 categories". Reversing the analogy lowered accuracy (mean −0.11), although the offset is the same both ways.
  - His recommendation: "report the performance of the simple baselines we have suggested, in particular ONLY-B and possibly also IGNORE-A".
- **With unit vectors, the offset is a sum of cosines.** Levy & Goldberg, *Linguistic Regularities in Sparse and Explicit Word Representations*, CoNLL 2014, pp. 171–180 ([anthology](https://aclanthology.org/W14-1618/)). With unit-length vectors, the offset method is equivalent to arg max cos(b\*, b) − cos(b\*, a) + cos(b\*, a\*). Such sums "allow one sufficiently large term to dominate the expression". Their 3CosMul is cos(b\*, b)·cos(b\*, a\*) / (cos(b\*, a) + ε), with cosines first mapped to [0, 1] by (x + 1)/2. It raised analogy accuracy, for example from 62.70% to 66.72% on the Google set with embeddings. They also describe PAIRDIRECTION, cos(b\* − b, a\* − a), which compares directions only. Deck vectors are unit length, but archetype centroids are not (§3), so the equivalence holds only after renormalising.
- **Dependence on vector similarity.** Rogers, Drozd & Li, *The (too many) problems of analogical reasoning with word vectors*, \*SEM 2017, pp. 135–148 ([anthology](https://aclanthology.org/S17-1017/)). "The vector offset (as well as two other, better-performing methods) suffers from dependence on vector similarity."
- **Silent exclusion can mislead.** Nissim, van Noord & van der Goot, *Fair Is Better than Sensational*, Computational Linguistics 46(2), 2020 ([anthology](https://aclanthology.org/2020.cl-2.7/), [arXiv](https://ar5iv.labs.arxiv.org/html/1905.09866)). In the standard word2vec and gensim code, "the input terms of the analogy query are not allowed to be returned", so "it is impossible to obtain man is to doctor as woman is to doctor". With the inputs allowed, the unconstrained offset returned "doctor". They argue this "exacerbated some possibly non-existing biases".
- **Testing offsets without the analogy test.** Fournier, Dunbar & Dupoux, *Analogies minus analogy test*, CoNLL 2020 ([anthology](https://aclanthology.org/2020.conll-1.29/)). They measure "class-wise offset concentration", meaning whether pairs related in the same way share an offset direction, and "pairing consistency", separately from nearest-neighbour search. For deck space, the analogous check is whether Control − Midrange offsets point the same way across colour pairs, compared with offsets between random archetype pairs. (Our reading of how it maps.)
- **Showing offsets in a picture.** The Embedding Projector's custom projection builds axes "from two text searches, using the difference between their point centroids" ([Smilkov et al. 2016](https://ar5iv.labs.arxiv.org/html/1611.05469)). That is a linear projection onto chosen difference vectors, so it keeps those directions exactly and ignores everything else. Arrows drawn on a t-SNE or UMAP map do not represent vector differences: those maps are non-linear and do not preserve distances (§1). (Our reading.)
- **Deck diffs as difference vectors.** Before normalisation, a deck vector is a weighted sum over cards. So the difference between two unnormalised deck sums is the weighted sum of cards added minus cards removed, plus the change in √copies for cards in both. Normalising each deck to unit length rescales the two sums by different amounts, so the difference of the unit vectors is not exactly that card-level difference. (Algebra, not a cited finding.)

---

## 5. Interactive tools

| Tool | Where data goes | Python | Projects itself | Scale noted by source |
|---|---|---|---|---|
| TensorFlow Embedding Projector | Browser (WebGL); standalone repo archived 2026-04-19 | Via TensorBoard or TSV files | PCA, t-SNE, UMAP, custom | t-SNE on 10,000-point sample, UMAP on 5,000, PCA on 50,000 with input over 200 dims randomly projected to 200 first |
| Apple Embedding Atlas | Local; browser with DuckDB-WASM, or a server DuckDB | `pip install embedding-atlas`; CLI, Jupyter widget | UMAP, or supplied 2-D coordinates | "Up to a few million points", WebGPU |
| Nomic Atlas | Cloud platform; login required | `pip install nomic` | Yes | "Handles millions of embeddings" |
| DataMapPlot | Local; static or self-contained HTML | Yes | No; takes 2-D coordinates | Not stated |
| Plotly | Local HTML | Yes | No | WebGL "up to around a million points" |
| Bokeh | Local HTML / server | Yes | No | WebGL better above ~25,000 points |

- **Embedding Projector** (Smilkov et al., [arXiv 1611.05469](https://arxiv.org/abs/1611.05469)). It offers PCA, t-SNE and custom projections, plus a list of nearest neighbours with distances for a clicked point. Its own source caps the points it projects: `TSNE_SAMPLE_SIZE = 10000`, `UMAP_SAMPLE_SIZE = 5000`, `PCA_SAMPLE_SIZE = 50000`, and input of more than `PCA_SAMPLE_DIM = 200` dimensions is randomly projected before PCA ([data.ts](https://github.com/tensorflow/tensorboard/blob/master/tensorboard/plugins/projector/vz_projector/data.ts)). The standalone repository "was archived by the owner on Apr 19, 2026" ([GitHub](https://github.com/tensorflow/embedding-projector-standalone)).
- **Embedding Atlas** (Ren, Hohman, Lin & Moritz, Apple, [arXiv 2505.06386](https://arxiv.org/html/2505.06386); [repo](https://github.com/apple/embedding-atlas)). MIT licence. It provides automatic density-based clustering and labels, nearest-neighbour search, and metadata views that cross-filter each other. "We use UMAP to project them into 2D coordinates", or users "supply pre-computed 2D coordinates". DuckDB in the browser gives "in-browser data exploration without the need for a backend server". According to the paper's comparison, most other tools do not cross-filter metadata at scale, and almost all need a backend server for computation. (Paraphrased from the paper's prose.)
- **Nomic Atlas** ([guide](https://docs.nomic.ai/atlas/embeddings-and-retrieval/guides/how-to-visualize-embeddings)): "a cloud-based platform for scalable, interactive embedding visualization". You upload embeddings with `dataset.add_data(embeddings=..., data=metadata)` and then "Log in to Nomic Atlas to explore and share". Privacy options and limits are on pages not read.
- **DataMapPlot** (Tutte Institute, [repo](https://github.com/TutteInstitute/datamapplot), [docs](https://datamapplot.readthedocs.io/en/latest/)). It has "essentially only two functions: create_plot and create_interactive_plot". `create_interactive_plot(data_map_coords, *label_layers, hover_text=...)` takes 2-D coordinates "usually ... produced via a dimension reduction technique such as UMAP, t-SNE, PacMAP, PyMDE". The label layers are "each at a different level of resolution", finest first ([source](https://github.com/TutteInstitute/datamapplot/blob/main/datamapplot/create_plots.py)), which matches leaf, mid-level and top-level archetypes. `inline_data=True` puts the data in one HTML file, which is portable "but can result in very large file sizes".
- **Plotly** ([performance](https://plotly.com/python/performance/)). "It is possible to represent up to around a million points with WebGL-enabled traces"; for more, it points to datashader. WebGL traces exported to PDF or SVG are embedded "as an encapsulated raster", and "it may not be possible to render more than 8 WebGL-involving figures on the same page".
- **Bokeh** ([WebGL guide](https://docs.bokeh.org/en/latest/docs/user_guide/output/webgl.html)): `figure(output_backend="webgl")`. Canvas suits "fewer than 10,000 markers or points", and WebGL is usually noticeably better above "25,000 markers or points".

---

## Sources

Projections and their critiques:
- van der Maaten & Hinton, *Visualizing Data using t-SNE*, JMLR 9, 2008. https://jmlr.org/papers/v9/vandermaaten08a.html
- Wattenberg, Viégas & Johnson, *How to Use t-SNE Effectively*, Distill, 2016. https://distill.pub/2016/misread-tsne/
- Kobak & Berens, *The art of using t-SNE for single-cell transcriptomics*, Nat Commun 10:5416, 2019. https://pmc.ncbi.nlm.nih.gov/articles/PMC6882829/
- Kobak & Linderman, *Initialization is critical for preserving global data structure in both t-SNE and UMAP*, Nat Biotechnol 39(2):156–157, 2021 (preprint read). https://www.biorxiv.org/content/10.1101/2019.12.19.877522v1
- Böhm, Berens & Kobak, *Attraction-Repulsion Spectrum in Neighbor Embeddings*, JMLR 23, 2022. https://jmlr.org/papers/v23/21-0055.html
- Linderman et al., *Fast interpolation-based t-SNE*, Nat Methods 16(3):243–245, 2019. https://arxiv.org/abs/1712.09005
- Poličar, Stražar & Zupan, *openTSNE*, J Stat Softw 109(3), 2024. https://opentsne.readthedocs.io/en/latest/ ; source https://github.com/pavlin-policar/openTSNE
- McInnes, Healy & Melville, *UMAP*, arXiv 1802.03426. https://arxiv.org/abs/1802.03426 ; docs https://umap-learn.readthedocs.io/ ; source https://github.com/lmcinnes/umap
- Narayan, Berger & Cho, *Assessing single-cell transcriptomic variability through density-preserving data visualization*, Nat Biotechnol 39(6):765–774, 2021 (preprint read). https://www.biorxiv.org/content/10.1101/2020.05.12.077776v1
- Wang, Huang, Rudin & Shaposhnik, *Understanding How Dimension Reduction Tools Work*, JMLR 22(201), 2021. https://jmlr.org/papers/v22/20-1061.html ; full text https://ar5iv.labs.arxiv.org/html/2012.04456 ; package https://github.com/YingfanWang/PaCMAP
- Amid & Warmuth, *TriMap*, arXiv 1910.00204. https://arxiv.org/abs/1910.00204 ; source https://github.com/eamid/trimap
- Moon et al., *Visualizing structure and transitions in high-dimensional biological data*, Nat Biotechnol 37(12):1482–1492, 2019. https://pmc.ncbi.nlm.nih.gov/articles/PMC7073148/ ; source https://github.com/KrishnaswamyLab/PHATE
- Tang, Liu, Zhang & Mei, *Visualizing Large-scale and High-dimensional Data* (LargeVis), WWW 2016. https://arxiv.org/abs/1602.00370 ; code https://github.com/lferry007/LargeVis
- Chari & Pachter, *The specious art of single-cell genomics*, PLoS Comput Biol 19(8):e1011288, 2023. https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011288
- scikit-learn: manifold guide https://scikit-learn.org/stable/modules/manifold.html ; TSNE https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html ; MDS https://scikit-learn.org/stable/modules/generated/sklearn.manifold.MDS.html ; LDA https://scikit-learn.org/stable/modules/lda_qda.html

Faithfulness measures:
- Espadoto, Martins, Kerren, Hirata & Telea, *Towards a Quantitative Survey of Dimension Reduction Techniques*, IEEE TVCG 27(3):2153–2173, 2021. https://webspace.science.uu.nl/~telea001/uploads/PAPERS/TVCG19/paper.pdf
- Venna & Kaski, *Neighborhood Preservation in Nonlinear Projection Methods*, ICANN 2001 (cited via scikit-learn). https://scikit-learn.org/stable/modules/generated/sklearn.manifold.trustworthiness.html
- Venna, Peltonen, Nybo, Aidos & Kaski, *Information Retrieval Perspective to Nonlinear Dimensionality Reduction for Data Visualization*, JMLR 11, 2010. https://jmlr.org/papers/v11/venna10a.html
- Lee & Verleysen, *Quality assessment of dimensionality reduction: Rank-based criteria*, Neurocomputing 72(7–9):1431–1443, 2009 (via coRanking docs). https://cloud.r-project.org/web/packages/coRanking/refman/coRanking.html

Non-projection views:
- Wolf et al., *PAGA*, Genome Biol 20:59, 2019. https://pmc.ncbi.nlm.nih.gov/articles/PMC6425583/
- seaborn clustermap https://seaborn.pydata.org/generated/seaborn.clustermap.html ; SciPy optimal_leaf_ordering and cophenet https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html ; scikit-learn silhouette https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_samples.html ; pandas parallel_coordinates https://pandas.pydata.org/docs/reference/api/pandas.plotting.parallel_coordinates.html
- Nickel & Kiela, *Poincaré Embeddings for Learning Hierarchical Representations*, arXiv 1705.08039. https://arxiv.org/abs/1705.08039

Analogies:
- Mikolov, Yih & Zweig, NAACL 2013. https://aclanthology.org/N13-1090/
- Levy & Goldberg, CoNLL 2014. https://aclanthology.org/W14-1618/
- Linzen, RepEval 2016. https://arxiv.org/abs/1606.07736
- Rogers, Drozd & Li, \*SEM 2017. https://aclanthology.org/S17-1017/
- Nissim, van Noord & van der Goot, Computational Linguistics 46(2), 2020. https://aclanthology.org/2020.cl-2.7/
- Fournier, Dunbar & Dupoux, CoNLL 2020. https://aclanthology.org/2020.conll-1.29/

Tools:
- Smilkov et al., *Embedding Projector*, arXiv 1611.05469. https://arxiv.org/abs/1611.05469 ; source https://github.com/tensorflow/tensorboard/tree/master/tensorboard/plugins/projector
- Ren, Hohman, Lin & Moritz, *Embedding Atlas*, arXiv 2505.06386. https://arxiv.org/html/2505.06386 ; https://github.com/apple/embedding-atlas
- Nomic Atlas docs. https://docs.nomic.ai/atlas/embeddings-and-retrieval/guides/how-to-visualize-embeddings
- DataMapPlot. https://github.com/TutteInstitute/datamapplot
- Plotly performance. https://plotly.com/python/performance/ ; Bokeh WebGL https://docs.bokeh.org/en/latest/docs/user_guide/output/webgl.html ; matplotlib rasterization https://matplotlib.org/stable/gallery/misc/rasterization_demo.html

## Could not verify

- The published versions of Kobak & Linderman (Nat Biotechnol 2021) and Narayan et al. (Nat Biotechnol 2021) were behind Nature's login. Quotes come from the bioRxiv preprints. Volume and pages come from Crossref.
- Wolf et al. (PAGA) was read through PubMed Central, not the publisher's page.
- Venna & Kaski (ICANN 2001) and Lee & Verleysen (2009) were not read. Their definitions come from scikit-learn, Espadoto et al. and the coRanking package docs.
- TriMap, LargeVis, UMAP and FIt-SNE claims come from abstracts and docs. Their full papers were not read. Whether LargeVis's code supports a cosine metric was not checked.
- Embedding Atlas's paper comparison table is icons only. Per-tool cells were not read, so the comparison there is from the paper's prose.
- Nomic Atlas: privacy options, size limits and pricing were not read.
- DataMapPlot's offline-mode docs page timed out. Offline behaviour is taken from the `inline_data` docstring in its source.
- Chari & Pachter's article was corrected in November 2025 (e1013655). The correction was not read.
- The PaCMAP runtimes are from the authors' 2021 hardware on 784-dimensional MNIST. They were not reproduced, and deck vectors have a different dimension.
- No source was found that evaluates any of these views on card-game decks, on labels arranged in a tree, or on parent-labelled items.
- All reported numbers are the authors' own and were not reproduced.
