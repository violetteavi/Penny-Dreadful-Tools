# Deck diffs, Stage 1

#62 (Deck diffs: what the cards kept, removed and added between two decks look like). PRs: none. Nothing is tuned. pairs.csv and cards.csv are next to the results PDF.

## Provenance

| | run 17 | run 14 | run 16 |
|---|---|---|---|
| run | `17` | `14` | `16` |
| model | `17` | `14` | `16` |
| name | `embedding nearest deck` | `embedding nearest deck` | `bag of cards nearest deck` |
| params | `{'copies': 'sqrt', 'embedding': 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39', 'weights': 'idf'}` | `{'embedding': 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39'}` | `{'copies': 'sqrt'}` |
| snapshot | `1` | `1` | `1` |
| scheme | `3` | `3` | `3` |
| identity hash | `010e60c099c37adc004a5889a061d2ab67e1a7e2` | `cc3c7702f71ec408825e027e80beee6d2c587b05` | `349b02f01c9a83a8df9636792949c98366ec483a` |
| embedding hash | `3168bf8be50e24653c59ec118af99cbd99235ea96a1ea5d4580f8028062bda5a` | `3168bf8be50e24653c59ec118af99cbd99235ea96a1ea5d4580f8028062bda5a` | `None` |
| card weights hash | `2a2377a012a1d7001fd424156cca9d367a8e7db0` | `None` | `2a2377a012a1d7001fd424156cca9d367a8e7db0` |
| training fingerprint | `94024d074aaaf87c6796e491e6c26aaf3c8320b8` | `94024d074aaaf87c6796e491e6c26aaf3c8320b8` | `94024d074aaaf87c6796e491e6c26aaf3c8320b8` |

## Pairs

| Group | Pairs |
|---|---|
| coverage, season 39, ancestor/descendant | 1956 |
| coverage, season 39, near rival | 9780 |
| coverage, season 39, same | 1937 |
| coverage, season 39, same branch | 1850 |
| coverage, season 39, sibling | 1768 |
| coverage, season 39, unrelated | 1956 |
| coverage, training, ancestor/descendant | 2000 |
| coverage, training, near rival | 10000 |
| coverage, training, same | 2000 |
| coverage, training, same branch | 1905 |
| coverage, training, sibling | 1841 |
| coverage, training, unrelated | 2000 |
| match 16, right | 1340 |
| match 16, wrong | 616 |
| match 17, right | 1346 |
| match 17, wrong | 610 |
| typical, guessed, wrong | 1113 |
| typical, true, right | 1937 |

Skipped: coverage, season 39, same branch: nothing to draw 106, coverage, season 39, same: nothing to draw 19, coverage, season 39, sibling: nothing to draw 188, coverage, training, same branch: nothing to draw 95, coverage, training, sibling: nothing to draw 159, typical, guessed: under 10 rows 3, typical, true: under 10 rows 19.

## Medians

| Group | copies_removed | copies_added | unseen_added | season_gap | r17_cosine | r17_net_shift | r17_blended_fraction | r17_blended_on_axis | r17_share_fraction | r17_share_on_axis | r14_net_shift | r16_net_shift | r16_blended_fraction |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| coverage, season 39, ancestor/descendant | 57 | 57 | 4 | 16 | 0.756 | 0.738 | -0.7 | 0.255 | -0.748 | 0.106 | 0.58 | 1.32 | -0.746 |
| coverage, season 39, near rival | 45 | 44 | 4 | 8 | 0.953 | 0.352 | -0.226 | 0.202 | -0.485 | 0.162 | 0.277 | 1.19 | -0.532 |
| coverage, season 39, same | 45 | 45 | 4 | 10 | 0.898 | 0.505 | -0.119 | 0.183 | -0.279 | 0.129 | 0.363 | 1.19 | -0.289 |
| coverage, season 39, same branch | 59 | 59 | 4 | 14 | 0.726 | 0.776 | -1.09 | 0.54 | -0.974 | 0.397 | 0.627 | 1.33 | -0.99 |
| coverage, season 39, sibling | 56 | 56 | 4 | 16 | 0.751 | 0.742 | -0.974 | 0.482 | -0.899 | 0.327 | 0.587 | 1.31 | -0.936 |
| coverage, season 39, unrelated | 60 | 60 | 4 | 15 | 0.639 | 0.877 | -1.39 | 0.564 | -0.946 | 0.365 | 0.704 | 1.33 | -0.992 |
| coverage, training, ancestor/descendant | 56 | 56 | 0 | 1 | 0.757 | 0.739 | -0.456 | 0.219 | -0.676 | 0.0925 | 0.575 | 1.4 | -0.697 |
| coverage, training, near rival | 41 | 41 | 0 | 0 | 0.954 | 0.344 | -0.184 | 0.184 | -0.454 | 0.154 | 0.273 | 1.26 | -0.489 |
| coverage, training, same | 42 | 42 | 0 | 0 | 0.907 | 0.472 | -0.00517 | 0.17 | 0.0128 | 0.115 | 0.35 | 1.26 | 0.0117 |
| coverage, training, same branch | 58 | 58 | 0 | 0 | 0.712 | 0.797 | -1.08 | 0.524 | -0.976 | 0.399 | 0.628 | 1.41 | -1 |
| coverage, training, sibling | 56 | 56 | 0 | 0 | 0.752 | 0.742 | -0.89 | 0.436 | -0.845 | 0.309 | 0.58 | 1.41 | -0.901 |
| coverage, training, unrelated | 59 | 60 | 0 | 0 | 0.637 | 0.888 | -1.45 | 0.567 | -0.965 | 0.365 | 0.699 | 1.41 | -1.01 |
| match 16, right | 22 | 23 | 4 | 2 | 0.966 | 0.325 | -0.0629 | 0.164 | -0.199 | 0.125 | 0.203 | 0.813 | -0.252 |
| match 16, wrong | 33 | 34 | 8 | 3 | 0.923 | 0.453 | -0.486 | 0.335 | -0.501 | 0.206 | 0.297 | 0.929 | -0.549 |
| match 17, right | 28 | 28 | 3 | 3 | 0.975 | 0.259 | -0.0476 | 0.115 | -0.167 | 0.108 | 0.188 | 0.942 | -0.186 |
| match 17, wrong | 45.5 | 46 | 7 | 7 | 0.958 | 0.336 | -0.2 | 0.199 | -0.543 | 0.162 | 0.26 | 1.16 | -0.579 |
| typical, guessed, wrong | 49 | 49 | 8 | 12 | 0.89 | 0.525 | -0.491 | 0.343 | -1.06 | 0.327 | 0.39 | 1.2 | -1.13 |
| typical, true, right | 42 | 42 | 4 | 8 | 0.931 | 0.434 | -0.256 | 0.221 | -0.66 | 0.232 | 0.3 | 1.14 | -0.662 |

## Across spaces

Sign agreement / Spearman / small-flip share (both |fraction| < 0.05), over pairs with both shifts.

| Group | 17 vs 14 | 17 vs 16 | 17 embedding vs 17 share | 17 share vs bag, 17 neighbours | bag, 17 neighbours vs bag, own |
|---|---|---|---|---|---|
| coverage, season 39, ancestor/descendant | 0.85 / 0.80 / 0.01 (1956) | 0.78 / 0.37 / 0.00 (1956) | 0.78 / 0.41 / 0.00 (1956) | 0.98 / 0.98 / 0.41 (1956) | 0.96 / 0.91 / 0.08 (1956) |
| coverage, season 39, near rival | 0.85 / 0.72 / 0.13 (9721) | 0.84 / 0.34 / 0.02 (9721) | 0.84 / 0.32 / 0.02 (9721) | 0.99 / 0.97 / 0.51 (9721) | 0.99 / 0.96 / 0.37 (9721) |
| coverage, season 39, same | 0.83 / 0.83 / 0.09 (1937) | 0.70 / 0.48 / 0.02 (1937) | 0.70 / 0.45 / 0.02 (1937) | 0.94 / 0.97 / 0.27 (1937) | 0.97 / 0.98 / 0.31 (1937) |
| coverage, season 39, same branch | 0.99 / 0.90 / 0.00 (1850) | 0.98 / 0.35 / 0.00 (1850) | 0.98 / 0.33 / 0.03 (1850) | 1.00 / 0.97 / – (1850) | 1.00 / 0.97 / 0.00 (1850) |
| coverage, season 39, sibling | 0.97 / 0.91 / 0.02 (1768) | 0.96 / 0.40 / 0.00 (1768) | 0.96 / 0.36 / 0.00 (1768) | 1.00 / 0.97 / 0.75 (1768) | 0.99 / 0.96 / 0.00 (1768) |
| coverage, season 39, unrelated | 0.99 / 0.88 / 0.00 (1956) | 0.99 / 0.29 / 0.00 (1956) | 0.98 / 0.27 / 0.00 (1956) | 1.00 / 0.97 / 0.50 (1956) | 1.00 / 0.96 / 0.22 (1956) |
| coverage, training, ancestor/descendant | 0.87 / 0.84 / 0.02 (2000) | 0.71 / 0.43 / 0.00 (2000) | 0.72 / 0.44 / 0.01 (2000) | 0.97 / 0.97 / 0.30 (2000) | 0.94 / 0.93 / 0.05 (2000) |
| coverage, training, near rival | 0.85 / 0.74 / 0.11 (9902) | 0.79 / 0.35 / 0.03 (9902) | 0.79 / 0.35 / 0.03 (9902) | 0.97 / 0.97 / 0.47 (9902) | 0.96 / 0.95 / 0.31 (9902) |
| coverage, training, same | 0.85 / 0.86 / 0.12 (2000) | 0.69 / 0.52 / 0.05 (2000) | 0.69 / 0.51 / 0.03 (2000) | 0.91 / 0.96 / 0.20 (2000) | 0.95 / 0.98 / 0.42 (2000) |
| coverage, training, same branch | 0.98 / 0.91 / 0.13 (1905) | 0.97 / 0.35 / 0.00 (1905) | 0.97 / 0.33 / 0.02 (1905) | 1.00 / 0.97 / 0.50 (1905) | 1.00 / 0.97 / 0.00 (1905) |
| coverage, training, sibling | 0.96 / 0.92 / 0.04 (1841) | 0.93 / 0.44 / 0.01 (1841) | 0.93 / 0.40 / 0.01 (1841) | 0.99 / 0.97 / 0.30 (1841) | 0.99 / 0.95 / 0.13 (1841) |
| coverage, training, unrelated | 0.99 / 0.91 / 0.10 (2000) | 0.98 / 0.30 / 0.00 (2000) | 0.98 / 0.27 / 0.00 (2000) | 1.00 / 0.97 / 1.00 (2000) | 1.00 / 0.96 / 0.25 (2000) |
| match 16, right | 0.79 / 0.75 / 0.35 (1339) | 0.69 / 0.47 / 0.06 (1339) | 0.69 / 0.49 / 0.07 (1339) | 0.97 / 0.96 / 0.68 (1339) | 0.98 / 0.98 / 0.64 (1339) |
| match 16, wrong | 0.92 / 0.71 / 0.00 (614) | 0.92 / 0.20 / 0.04 (614) | 0.92 / 0.21 / 0.08 (614) | 0.99 / 0.94 / 0.50 (614) | 0.99 / 0.96 / 0.20 (614) |
| match 17, right | 0.73 / 0.61 / 0.30 (1345) | 0.69 / 0.32 / 0.08 (1345) | 0.65 / 0.29 / 0.06 (1345) | 0.90 / 0.95 / 0.22 (1345) | 0.97 / 0.98 / 0.74 (1345) |
| match 17, wrong | 0.82 / 0.65 / 0.18 (609) | 0.86 / 0.26 / 0.06 (609) | 0.86 / 0.30 / 0.03 (609) | 0.99 / 0.97 / 0.25 (609) | 0.99 / 0.97 / 0.50 (609) |
| typical, guessed, wrong | 0.95 / 0.82 / 0.13 (1113) | 0.89 / 0.25 / 0.01 (1113) | 0.89 / 0.27 / 0.00 (1113) | 0.98 / 0.96 / 0.18 (1113) | 0.99 / 0.95 / 0.00 (1113) |
| typical, true, right | 0.82 / 0.79 / 0.05 (1937) | 0.80 / 0.39 / 0.01 (1937) | 0.80 / 0.37 / 0.01 (1937) | 0.98 / 0.97 / 0.23 (1937) | 0.99 / 0.98 / 0.19 (1937) |

## Timings

| Step | Seconds |
|---|---|
| run 17: refit | 62 |
| run 17: geometry | 4 |
| pairs | 28 |
| run 17: specificity | 13 |
| run 17: measures | 410 |
| run 14: refit | 67 |
| run 14: geometry and measures | 373 |
| run 16: refit | 66 |
| run 16: geometry and measures | 27 |
| peak memory, MB | 2858 |
