# Historical Analogue Stability Evaluation

## Question

A useful similarity result should not change completely because one reasonable modeling choice
moves slightly. Stability testing keeps the query cases, candidate timing, training period,
imputation, and scaling fixed while changing one declared representation choice at a time.

The goal is not to manufacture one invariant list. Some movement is expected, especially near the
top-ten boundary. The goal is to identify whether the application would tell a broadly consistent
story and which assumptions control that story.

The implemented job is `601 Evaluation | Historical Analogue Audit`. It reads the published
job-502 matches and `gold_modeling_panel`, records variant matches in the model schema, and writes
query-level stability results to the evaluation schema. The validated November 7 run uses the
same 32 development queries as job 502 and preserves all 21 variants for every query.

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

Small weighted-distance changes are certified against the baseline shortlist boundary when the
variant's tenth distance is smaller than the mathematical lower bound for any excluded candidate.
The distinct-tract variants use the same boundary check in their baseline representation. A tie at
the boundary is deliberately not certified. Family ablations and alternate PCA dimensions do not
have the same guarantee and are labeled as shortlist-based stress tests. The shortlist size,
boundary distances, lower bound, and certification result belong in every published row.

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

## First audit results

The published audit contains 6,720 individual matches and 672 query-level stability rows. The
weighted and PCA baselines reproduce job 502 exactly. All 320 small-weight query variants and all
64 distinct-tract query variants passed the mathematical shortlist-boundary test. Family
ablations and alternate PCA dimensions remain clearly labeled as shortlist-based stress tests.

The local-weight result is reassuring. Moving one family at a time to 80% or 120% of its baseline
factor retained 93.4% of the weighted top ten on average. The tenth-percentile query retained 90%,
the worst query retained 80%, and 95% of baseline top-three positions remained in the perturbed
top three. The median analogue outcome changed by about 0.006 cumulative log-change units on
average. The current equal-family design is therefore not balanced on a knife edge.

Removing a whole family produces a different result and should not be mixed with that local
stability claim. Ablations retained only 37.6% of neighbors on average. Market trajectory had the
largest effect: removing it retained 16.6% on average and produced some zero-overlap top tens.
This does not prove that market trajectory is the correct or most important real-world concept;
it shows that the current match definition depends strongly on it.

PCA component count is also consequential. Five- and seven-component PCA variants retained 50.9%
of the six-component top ten on average, with zero overlap for the most sensitive queries. Because
these are shortlist-based stress tests, the exact percentages describe the evaluated candidate
union rather than a certified national reranking. They still reinforce that explained variance
alone is not a sound representation-selection rule.

Seventeen of 32 baseline query lists repeated a physical candidate tract at more than one year in
both representations. The baseline averaged 9.31 distinct communities per top ten. Enforcing one
historical state per physical tract retained 93.1% of matches on average, was boundary-certified
for every query, and restored ten distinct communities. The application should therefore use the
distinct-community rule by default while retaining tract-year candidates internally for audit.

## Representation decision after expanded evaluation

Later-outcome accuracy does not clearly separate the representations on this small sample.
Weighted median is the strongest analogue estimate at one year, while PCA inverse-distance is the
strongest at three years; neither beats the primary state-trend or regularized-linear forecast.
Weighted standardized retrieval became the application default because it is stable under
reasonable weight changes, easier to explain feature by feature, and less likely to hide a large
family-level difference. Job 602 expanded the sample to 88 one-year and 90 three-year queries and
found lower overall analogue MAE for weighted retrieval at both horizons. PCA remains a development
comparison, not a second user-facing lens. This freezes the retrieval representation for the next
implementation stage; it does not turn analogue outcomes into the primary forecast or authorize
opening the locked temporal test.
