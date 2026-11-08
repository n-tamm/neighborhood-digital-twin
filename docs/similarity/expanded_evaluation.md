# Expanded Historical Analogue Evaluation

## Why this stage exists

Jobs 502 and 601 established that the historical workflow is time-safe and that weighted
standardized matching is easier to explain and reasonably stable under small weight changes.
Those conclusions came from 16 queries per horizon, however. Job 602 expands the validation
sample before the application representation is frozen.

This is a model-selection workflow, not a final test. It reads only rows whose frozen temporal
role is `validation`; the locked temporal tests remain unavailable.

## Query selection

The eligible population contains validation tract-years that have an observed FHFA target and
complete predictions from all declared forecast comparators. Queries are grouped by:

- forecast horizon;
- forecast-origin year;
- Census region; and
- development-state or held-out-state role.

Within each group, the same deterministic GEOID hash used by job 502 orders the tracts. Job 602
selects up to five queries from every available group, compared with one in job 502. This produces
a larger, geographically and temporally balanced sample without choosing examples based on their
later outcomes.

The first live coverage review showed that this balanced core could still miss a rare but relevant
category, including tracts below 25% single-family housing at one year. The workflow therefore
adds one deterministic query for any housing-composition, community-size, or ACS-uncertainty
category not already represented. The supplement is selected without looking at later outcomes
and adds only a few queries rather than multiplying every category into every sampling stratum.
The full sample is then compared with the eligible validation population so disproportionate
groups remain visible.

## Retrieval policy

Both representations search the same historical candidate population:

1. weighted standardized features with equal total weight per feature family; and
2. six-component PCA retained as the comparison representation.

A candidate outcome must end by the query year, the query tract cannot match itself, and
candidates remain limited to geographic-development states. Unlike the original baseline, job
602 keeps only the closest historical state from each physical candidate tract before choosing
the top ten. Every result therefore represents ten distinct communities rather than repeat years
from the same tract.

## Evaluation evidence

The workflow publishes the same retrieval and outcome metrics used by job 502, but adds scorecard
slices for:

- housing-composition band;
- community-size band; and
- ACS-uncertainty band.

It also publishes selected-versus-eligible query shares. A share difference near zero means the
expanded sample resembles the eligible population for that category. A larger difference is a
warning that the aggregate result may be influenced by uneven sampling.

The final representation decision will not be made from MAE alone. Later-outcome accuracy from
job 602 must be interpreted together with the stability, feature-level fidelity, and explanation
evidence from job 601. Historical analogue estimates remain secondary context unless they show a
clear and repeatable advantage over the primary forecast.

## Publication checks

Job 602 stops before writing tables if:

- a query is not a validation row;
- a candidate outcome was unavailable at the query date;
- a query matches itself;
- a top-ten list repeats a physical candidate tract;
- weighted and PCA results do not cover identical queries;
- forecast comparators are incomplete;
- an available sampling group receives fewer than the requested number of queries; or
- an eligible housing-composition, community-size, or ACS-uncertainty category has no query; or
- coverage shares or run lineage do not reconcile.

## Databricks outputs

| Schema | Table | Role |
|---|---|---|
| `neighborhood_twin_model` | `historical_analogue_selection_match` | Expanded ranked match evidence |
| `neighborhood_twin_model` | `historical_analogue_selection_prediction` | Analogue estimates and forecast comparators |
| `neighborhood_twin_evaluation` | `historical_analogue_selection_summary` | Retrieval and representation diagnostics |
| `neighborhood_twin_evaluation` | `historical_analogue_selection_scorecard` | Overall and subgroup outcome evaluation |
| `neighborhood_twin_evaluation` | `historical_analogue_selection_coverage` | Selected-versus-eligible sample coverage |

## Current status

The workflow code and bundle definition are implemented. Live row counts, coverage findings,
method comparisons, and the final representation decision will be recorded here only after the
Databricks run and post-publication reconciliation succeed.
