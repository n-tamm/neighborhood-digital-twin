# Historical Analogue Stability Evaluation

## Question

A useful similarity result should not change completely because one reasonable modeling choice
moves slightly. Stability testing keeps the query cases, candidate timing, training period,
imputation, and scaling fixed while changing one declared representation choice at a time.

The goal is not to manufacture one invariant list. Some movement is expected, especially near the
top-ten boundary. The goal is to identify whether the application would tell a broadly consistent
story and which assumptions control that story.

## Declared variants

### Baselines

- weighted standardized distance with equal total weight per feature family;
- six-component PCA fitted to the weighted standardized representation.

The audit must reproduce the published job-502 ranks before another variant is interpreted.

### Small weight changes

Each feature family is separately set to 80% and 120% of its baseline factor. The family factors
are then normalized so total squared-distance weight remains equal to the number of families.
These ten variants test local sensitivity around the current equal-family design.

### Feature-family ablations

Each family is removed once, and the remaining families are renormalized. These are stress tests,
not small perturbations. Their results must be reported separately from the 80% and 120% tests.

### PCA component count

Five- and seven-component PCA variants are compared with the six-component baseline. Component
count remains a representation choice; explained variance alone does not select a winner.

### Candidate uniqueness

If repeated physical tracts occur, both baseline representations are reranked after keeping only
the closest historical year from each candidate tract. This tests whether repeated states from one
community materially change the evidence or outcome summary.

## Stability metrics

For each query and variant, report:

- top-ten overlap count and share;
- top-ten Jaccard similarity;
- top-three retention;
- mean absolute rank displacement among shared matches;
- change in the median analogue estimate;
- change in the inverse-distance estimate;
- change in later-outcome error on the identical query; and
- changes in candidate age and geographic diversity.

Top-ten retention is described as high at 70% or more, moderate from 50% through 69%, and low
below 50%. These are project review bands, not general scientific cutoffs. Report distributions
and low-stability cases rather than only an average.

## Candidate-shortlist performance design

Exact national retrieval is appropriate for the two baselines, but repeating the full
query-to-candidate cross join for every perturbation would be unnecessarily expensive. The planned
audit will retrieve a large exact shortlist under both baseline representations, take their union
for each query, and rerank the declared variants inside that union.

Small weighted-distance changes can be certified against the baseline shortlist boundary when the
variant's tenth distance is smaller than the mathematical lower bound for any excluded candidate.
Family ablations and alternate PCA dimensions do not have the same guarantee and must be labeled
as shortlist-based stress tests unless an exact spot check supports them. The shortlist size and
certification result belong in every published row.

This distinction prevents a computational shortcut from being described as exact retrieval.

## Leakage and consistency checks

Publication must stop if:

- baseline ranks do not reproduce job 502;
- query keys or candidate populations change unintentionally between variants;
- a query tract matches itself;
- a candidate outcome ends after the query origin;
- a query receives fewer than the declared number of matches;
- normalized feature weights do not reconcile;
- future query outcomes affect query or neighbor selection; or
- source run and configuration lineage are missing.

The locked temporal test remains unopened. Stability is evaluated on the existing development
queries and cannot be used to justify a final performance claim from the small sample.

## Decision role

This analysis can recommend that a representation is too unstable or that a particular family
dominates unexpectedly. It cannot permanently select the application representation by itself.
The final choice also requires the expanded or justified evaluation sample planned for the next
modeling branch, along with substantive case review and later-outcome performance.
