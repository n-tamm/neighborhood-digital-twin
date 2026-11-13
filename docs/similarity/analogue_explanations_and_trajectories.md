# Analogue Explanations and Historical Trajectories

## Why these products exist

A distance and ranked list are not enough to make a historical match understandable. Two tracts
can have a small overall distance while still differing meaningfully on housing structure,
affordability, or recent market movement. The application also needs more than the candidate's
final outcome: it should show the observed path between the historical origin and endpoint.

Serving contract 1.1 adds two deterministic products to every national analogue release:

- an explanation row for each ranked match; and
- an aligned annual FHFA path for each match from candidate origin through the selected horizon.

Neither product uses an LLM. They are calculated from the same fitted preprocessing, feature
definition, matched keys, and public FHFA data used by the evaluated analogue system.

## Explanation method

The query and candidate features are processed inside the same horizon-specific training fit used
for retrieval. Imputation and standardization are learned from eligible point-model training rows,
not from the current query population. For each of the twelve governed features, the explanation
calculates the absolute standardized query-to-candidate gap.

Those feature gaps are then summarized into the five families used by the model:

1. community scale;
2. occupancy and tenure;
3. housing structure;
4. affordability; and
5. recent housing-market trajectory.

Each family receives the mean absolute standardized gap across its features. Smaller values mean
the pair looks more alike within that family; larger values identify an important difference. The
serving row retains all five family gaps, the two closest families, the two most different
families, the closest individual feature, and the most different individual feature. It also
stores readable labels, query and candidate values for the two highlighted features, and counts
of features filled by the training-fitted imputer.

This is an explanation of the implemented distance, not an explanation of why housing prices
changed. The system does not describe any feature as a cause or treat a close family as evidence
that the query will follow the candidate's later outcome.

## Why standardized gaps are used

Raw gaps are not directly comparable: a population difference may be measured in thousands while
an occupancy-rate difference is a fraction. Standardization puts the model inputs on the scale
used by retrieval. The explanation still carries unscaled values for the highlighted features so
the application can translate the result back into recognizable terms.

Family gaps are reported before the family-specific distance multiplier is applied. This makes a
gap readable within the original standardized feature space. The overall `similarity_distance`
remains the authoritative weighted Euclidean ranking measure.

## Historical trajectory method

For each match, the trajectory begins at the candidate origin year with cumulative change equal
to zero. Annual one-year rows from `gold_forecast_target_historical` supply intermediate FHFA
single-family HPI observations. The endpoint comes directly from the match's approved one- or
three-year target record, so a valid endpoint is not discarded when an intermediate annual
observation is unavailable. Every row records:

- the year offset and actual observation year;
- the observed HPI;
- cumulative log and percentage change from the candidate origin;
- whether that annual point is observed;
- whether the full path is complete;
- whether the row is the declared horizon endpoint; and
- source-snapshot and serving-release lineage.

The endpoint must reproduce the later outcome already stored on the ranked match within numerical
tolerance. A path may retain an explicit missing intermediate observation, but it cannot publish
an unobserved or inconsistent endpoint. This distinction matters because a three-year target can
be valid even when the HPI is unavailable in one of the two years between its origin and endpoint.

## Application presentation

For a selected match, the application can state the two closest and two most different families,
then show the highlighted feature values as supporting detail. It should avoid labels such as
“identical” or “best community.” A small gap only means close under this representation.

The trajectory should be drawn on an aligned elapsed-year axis so candidates from different
calendar years can be compared. The actual candidate year and location must remain visible. A
calendar-year view can be offered as supporting context, but aligning by offset makes the
post-match path readable. The plot must say that these are observed historical FHFA paths, not
forecast lines or scenario effects.

## Publication gates

The release is blocked unless:

- every ranked match has exactly one explanation row;
- family names belong to the governed registry and gap ordering is internally consistent;
- imputation counts remain within the twelve-feature contract;
- every match has offsets zero through its declared horizon with no duplicate offset;
- every match has exactly one endpoint;
- every endpoint is observed and reconciles to the match outcome;
- explanation and trajectory release IDs match the other serving products; and
- all five serving tables pass their checks before the manifest is written.

These checks establish structural integrity and faithful explanation of the implemented method.
They do not establish causal validity or turn the analogue range into calibrated uncertainty.

## Code and operations

- [`analogue_serving_enrichment.py`](../../src/neighborhood_twin/analogue_serving_enrichment.py)
  owns the reusable builders and validation gates.
- [`01_build_analogue_serving_products.py`](../../notebooks/06_representations/01_build_analogue_serving_products.py)
  builds the products during job 700 while the horizon-specific representation is already fitted.
- [Current analogue serving products](analogue_serving_products.md) defines the shared release and
  application reading rule.
- [Pipeline run order](../PIPELINE_RUN_ORDER.md) defines refresh and recovery behavior.

## First validated release

Job 700 published schema-1.1 release `analogue-20261113T132155097077Z` in 470 seconds. It contains
934,380 explanation rows and 2,803,140 trajectory rows, alongside the unchanged national match,
summary, and availability populations. The five-row manifest was written only after every key,
gap, offset, and endpoint check passed.

Every one-year path is complete. Of the 467,190 three-year match paths, 444,093 are complete and
23,097 contain at least one explicit missing intermediate value. The latter group contains 29,804
missing annual points, but every final endpoint remains observed and reconciled. The application
can therefore draw connected lines only for complete paths and show gaps or a coverage note for
the remainder without discarding their valid later outcome.

The first live attempt exposed the distinction behind that rule: the builder initially tried to
derive every endpoint through a chain of one-year targets. Some three-year outcomes were valid
even though an intermediate annual origin was unavailable, so the gate correctly rejected the
release. The implementation now reads each endpoint from its approved direct horizon target and
uses annual records only for intermediate points. The failed attempt wrote no data or manifest.

Explanations also preserve missingness evidence. At both horizons, 68,370 match rows correspond to
6,837 current queries with at least one training-imputed feature. Candidate imputation affects
23,409 one-year match rows and 17,921 three-year rows. Housing structure is most often the closest
family, while recent market trajectory is most often the largest difference. These are useful
model-behavior findings for visual design, not causal findings about neighborhood change.
