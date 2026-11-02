# Figure 6: Similarity Representation Diagnostics

**File:** `06_similarity_representation_diagnostics.png`

## Question

How do standardized-raw and PCA retrieval differ in returned-distance spread, geographic reach,
and top-10 neighbor agreement?

## Construction

The left panel shows each representation's 10th-to-90th percentile distance range, interquartile
range, and median. The right panel shows cross-state share, same-county share, and mean raw/PCA
top-10 overlap.

## Current result

Six PCA components retain 95.5% of standardized variance, but raw and PCA lists overlap by only
55% on average. Cross-state shares are approximately 91.7% for raw retrieval and 95.0% for PCA.
Both search nationally, but representation choice changes many selected communities.

## Interpretation limits

- Distances are comparable only within one representation.
- Geographic diversity is descriptive, not proof of match quality.
- Overlap measures sensitivity to representation choice; it does not say which list is correct.
- Historical outcome utility, perturbation stability, and structured case review are not yet
  implemented.

**Source:** [`similarity_baseline_summary`](../../data/50_evaluation_similarity_baseline_summary.md)

**Detailed interpretation:** [Similarity evaluation](../../similarity/evaluation_and_results.md)
