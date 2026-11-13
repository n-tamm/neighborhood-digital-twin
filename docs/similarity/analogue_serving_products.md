# Current Analogue Serving Products

## Purpose

Job 700 turns the evaluated similarity method into data the application can safely use. It does
not choose a new representation, tune weights, or claim that analogues outperform the forecasting
model. It applies the approved weighted representation and exact KD-tree retrieval to the full
eligible current population, then publishes a compact, versioned release.

This distinction matters. Jobs 502, 601, and 602 established how historical matching behaves and
how useful its later outcomes are. Jobs 603 and 604 selected a practical retrieval engine. Job 700
is the first production-style batch publication step.

## Inputs and frozen choices

The workflow reads:

- `gold_modeling_panel`, which contains the point-in-time features, split roles, and historical
  FHFA outcomes;
- `gold_tract_profile_current`, which supplies the complete current profile population, readable
  place labels, housing composition, and coverage flags; and
- `analogue_tree_benchmark_match`, which proves that job 604 evaluated the same model-readiness
  build and current as-of year.

The release uses the selected weighted-standardized representation, one- and three-year outcome
horizons, ten distinct historical tract matches, and the exact KD-tree configuration validated in
job 604. Imputation and standardization are fit on eligible point-model training rows only. A
candidate's later outcome must end by the current query year, the query tract cannot match itself,
and locked temporal-test rows cannot enter the candidate pool.

## Build sequence

For each horizon, the notebook:

1. rebuilds the governed historical feature representation from the current modeling panel;
2. collects finite candidate and current-query vectors in deterministic GEOID order;
3. constructs the exact KD-tree over eligible historical tract-year states;
4. retrieves ten distinct non-self tracts for every eligible current query, expanding through
   distance-boundary ties when needed;
5. joins the returned keys back to governed place labels, candidate dates, and observed later
   outcomes; and
6. combines both horizons under one immutable serving release ID.

The release is then reduced into three application-facing tables and validated as one unit.

## Published tables

### `serving_analogue_match_current`

One row represents one ranked historical match for a current tract and horizon. It contains the
query and candidate identities, readable geography, candidate year and outcome end year, observed
later FHFA change, similarity distance, match rank, housing-model cohort, and release lineage.

The application can use this table for a ranked match list and later-trajectory evidence. It
should not describe a candidate outcome as something that will happen to the selected tract.

### `serving_analogue_summary_current`

One row represents one current tract and horizon. It summarizes the ten matches with median and
inverse-distance-weighted later change, 10th-to-90th percentile descriptive outcome range, match
distance, candidate age, and cross-state share. The range is explicitly marked as descriptive,
not a calibrated prediction interval.

### `serving_analogue_availability_current`

One row exists for every current profile tract and supported horizon, including unsupported cases.
It says whether a complete result is available and, if not, identifies the first applicable
reason: missing current ACS profile, insufficient similarity features, missing FHFA history, or
missing model-ready market features. It also carries a housing-composition band and warning so
the application can explain that later outcomes describe FHFA's single-family market rather than
all housing in the tract.

### `serving_release_manifest`

The manifest has one row per component table in a validated release. It records row counts, schema
version, as-of year, horizons, top-k setting, retrieval method, source model-readiness build, and
source job-604 run. The manifest is written after the data tables. Application code should only
select a release that has validated manifest rows for all three required tables.

## Publication and rollback behavior

Serving tables are append-only and partitioned by `serving_release_id`. A new job run does not
overwrite the previous approved release. This provides traceability and a simple rollback path.
If a run fails after writing some data rows but before writing the manifest, those rows are not an
active release. They can be removed later using the exact failed release ID; they must never be
selected merely because their build timestamp is recent.

## Validation gates

Publication stops unless all of the following hold:

- the model panel and job-604 evidence point to one identical model-readiness build;
- job 604 represents one exact retrieval run at the requested as-of year;
- each available tract-horizon has exactly ten ranks and ten distinct candidate tracts;
- ranks run from one through ten without duplicate query keys;
- no match uses the query tract, a future candidate outcome, or a locked temporal-test row;
- every available key has matches and one summary, and no unavailable key has either;
- every current profile has exactly one availability row per supported horizon;
- the summary range remains labeled as uncalibrated historical context; and
- all three release row counts are positive and reconcile before the manifest is written.

Job 900 then applies table descriptions and column comments. These checks protect structure and
timing; they do not make the historical outcomes causal or convert them into a primary forecast.

## Application use

The application should begin with the availability table. For an available tract and horizon, it
can read the corresponding summary and ten matches from the same release ID. For an unavailable
tract, it should keep the broader community profile visible and show the recorded reason rather
than returning an empty chart.

Match explanations and aligned historical trajectories are intentionally not part of this first
release. They require their own tested contracts so they can name the strongest shared traits and
largest differences without recomputing model logic in the app. The next communication notebook
should also read these governed tables rather than retraining the representation during a standup.

## First live release

The November 12, 2026 release `analogue-20261112T220655832818Z` passed every publication gate and
activated three component tables in a 433-second end-to-end job run:

| Table | Rows |
|---|---:|
| `serving_analogue_match_current` | 934,380 |
| `serving_analogue_summary_current` | 93,438 |
| `serving_analogue_availability_current` | 171,056 |

The release covers 46,719 eligible current tracts at each of the one- and three-year horizons,
with ten distinct matches per tract and horizon. Availability spans all 85,528 canonical current
profile rows per horizon. In each horizon, 1,121 rows lack a current ACS profile, 1,037 have
insufficient current similarity features, 19,443 lack FHFA history, and 17,208 lack the complete
model-ready market features required by this representation. These categories are explicit
application states, not rows silently dropped from the product.

The release points to model-readiness build `20261107T185721624743Z` and exact-tree evaluation run
`fae78721154347039d41864bad2e871a`. Job 900 then confirmed comments on all 26 availability, 35
match, 39 summary, and 13 manifest columns.

## Refresh rule

Rerun job 700 only after job 604 is current for the model-readiness build, or when the serving
contract itself changes. A visualization or application-layout change does not require a new
serving release. See the [pipeline run order](../PIPELINE_RUN_ORDER.md) for the full sequence and
recovery rules.
