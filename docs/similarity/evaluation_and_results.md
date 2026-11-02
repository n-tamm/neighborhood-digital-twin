# Similarity Evaluation and Current Results

There is no single correct list of similar communities. The current workflow therefore uses
unsupervised diagnostics to describe how the representations behave. These diagnostics are
necessary for model development but do not establish that a match is useful.

## Implemented diagnostics

| Diagnostic | Interpretation |
|---|---|
| PCA explained variance | Share of standardized feature variation retained by six components |
| Distance percentiles | Spread of returned distances within one representation |
| Distance IQR | Middle-half concentration of returned distances |
| Cross-state share | How often retrieval reaches beyond the query state |
| Same-county share | How often retrieval collapses to very local matches |
| Raw/PCA top-10 overlap | Sensitivity of the selected neighbor list to representation choice |

Distance values cannot be compared directly between raw and PCA spaces. Their usefulness lies in
the distribution within each representation, not in asking which representation has the smaller
number.

## Current findings

- Six PCA components retain 95.5% of standardized variance.
- Raw and PCA top-10 lists overlap by 5.5 matches, or 55%, on average.
- Approximately 91.7% of raw matches and 95.0% of PCA matches cross a state boundary.
- Both representations search nationally rather than returning only local tracts.

The 55% overlap is the main development finding. PCA retains most overall variance but changes
nearly half of the selected neighbors. Explained variance alone cannot choose the representation.

## What can be concluded

- The implemented features support national retrieval for the six review queries.
- Raw and PCA representations produce materially different match sets.
- Representation choice needs concrete case review and sensitivity analysis.

## What cannot be concluded

- The diagnostics do not show that a matched community had a useful later trajectory.
- High cross-state share is not automatically better than a local match.
- A small Euclidean distance does not mean two communities are identical.
- The six query tracts are not enough to establish national retrieval quality.

## Evaluation still absent from the current implementation

- time-safe historical query and candidate construction;
- later-outcome accuracy and comparison with random or regional matches;
- stability under feature, scaling, weighting, and time-window changes;
- feature-family fidelity and explanation of important differences;
- structured human review across a wider query set; and
- application coverage, latency, and unavailable-result behavior.

The current evaluation visual is documented separately in
[Similarity representation diagnostics](../model_evaluation/figures/06_similarity_representation_diagnostics.md).
