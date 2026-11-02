# Exploratory Data Analysis

The implemented EDA answers four questions in sequence:

1. Which communities and measures are available?
2. Where does availability differ across housing types, places, and time?
3. Which data-quality and geography rules affect interpretation?
4. Is the resulting panel suitable for the current model baselines?

It is primarily a data-readiness analysis. The figures describe coverage, observed patterns, and
model inputs; they do not estimate causal effects or final model performance.

## How the workflow is built

The Databricks workflow has two steps:

1. `400 Exploration | EDA Readiness` creates governed summary tables and validation results.
2. `401 Exploration | Visual EDA` refreshes the visual summaries, renders twelve PNGs, checks
   that all expected files are nonempty, and publishes a versioned manifest.

The summary and rendering steps are separate so a figure is built from a small, reviewable Delta
contract rather than recalculating analytical populations inside plotting code. The current
matched set is identified in
`workspace.neighborhood_twin_gold.gold_eda_figure_manifest`. The live image files are stored in
the `workspace.neighborhood_twin_gold.eda_figures` managed volume.

The [EDA figure inventory](../../reports/EDA_FIGURES.md) records the current build, exact storage
path, reproduction commands, and visual-review checks. The figure-building notebooks are
[`02_build_visual_eda.py`](../../notebooks/04_exploration/02_build_visual_eda.py) and
[`03_render_eda_figures.py`](../../notebooks/04_exploration/03_render_eda_figures.py).

## Recommended figure sequence

The figures are numbered to tell a data-readiness story. Reading isolated maps before the
coverage and cohort figures can give the wrong impression about what a blank area or population
change means.

### 1. Current national pipeline attrition

`01_pipeline_attrition.png` starts with the canonical tract universe and shows the counts that
retain current ACS data, similarity features, any FHFA history, and current forecast eligibility.

Read this as an availability funnel, not a sequence in which every bar is necessarily a strict
subset of the prior bar. The main result is that FHFA history is the largest practical constraint
on forecast reach. Candidate counts are preliminary data screens, not the final number of model
predictions.

### 2. Housing composition and FHFA coverage

`02_housing_composition_coverage.png` compares the share of current-ACS tracts with any FHFA
history and the share meeting current forecast-candidate rules across single-family housing-share
bands.

Coverage rises as single-family housing becomes a larger part of the tract's housing stock. This
supports a core product limitation: the forecast describes the FHFA-covered single-family market
and should not be presented as equally representative of heavily multifamily communities. The
figure shows target availability, not that single-family composition causes an HPI outcome.

### 3. Forecast candidates versus excluded tracts

`03_forecast_included_excluded_comparison.png` reports standardized mean differences between
current-ACS tracts that pass the forecast screen and those that do not. Positive values mean the
candidate group has a higher mean; negative values mean the excluded group does.

Standardization puts unlike measures on a common scale. The dashed lines at `-0.2` and `0.2` are
visual reference points for differences worth investigating, not automatic significance tests.
The figure reveals selection into the model population. It does not show causal effects or prove
that the future forecast errors will follow the same differences.

### 4. FHFA annual HPI behavior over time

`04_hpi_temporal_behavior.png` shows the median annual tract HPI change and the 10th-to-90th
percentile range from 1990 onward for the United States and the three display states: Arizona,
Michigan, and Pennsylvania.

The wide changes over time and differences among states explain why a random row split would be
misleading and why regional-trend baselines are necessary. The percentile band summarizes the
tracts available in each year; it does not correct for changes in historical FHFA coverage.

### 5. ACS measurement uncertainty

`05_acs_measurement_uncertainty.png` shows the twelve measures with the highest 90th-percentile
relative margin of error and marks each measure's median. Relative margin of error is the
published 90% margin of error divided by the absolute estimate.

Large ratios indicate that a measure can be noisy relative to its value. Near-zero estimates can
produce very large ratios, so the chart should be used to identify fragile feature families, not
to rank the substantive importance of variables. The forecast scorecard later slices results by
core ACS uncertainty instead of assuming every estimate is equally precise.

### 6. Stable historical and broader post-2020 coverage

`06_tract_vintage_coverage.png` separates the source tract universe from the usable analytical
cohort for each ACS release. Its main purpose is to make the 2020 geography break visible.

The increase from the 59,607-tract stable cohort to roughly 84,400 post-2020 tracts is a change in
geography and analytical population, not sudden neighborhood creation. Any analysis crossing
2020 must use the stable cohort. Post-2020 descriptive work may use the broader cohort, but the
two populations should be reported separately.

### 7. Model-feature completeness

`07_model_feature_completeness.png` shows the fifteen least-complete approved inputs in the
point-in-time historical feature table before model preprocessing. A 95% guide line makes the
remaining missingness visible.

The selected feature set is broadly populated, but the model still needs an explicit missing-data
rule. The implemented linear pipeline uses median values learned only from training rows. The
figure does not justify complete-case filtering, which would unnecessarily change the analytical
population.

### 8. Independent forecast-origin years

`08_model_split_origin_years.png` counts distinct forecast-origin years by horizon and frozen
split role. This is more informative than the raw number of tract rows because tracts from the
same origin share the same national time context.

The one-year horizon has ten training origins and is the primary model result. Three years has six
and is secondary. Five years has only three and remains exploratory. Calibration and locked-test
cells show reserved periods, not results that have already been examined.

### 9. Current forecast-candidate maps

`09_forecast_candidate_maps.png` maps current eligibility in Arizona, Michigan, and Pennsylvania
and pairs the maps with coverage information. It helps distinguish an actual unavailable area
from a plotting omission and shows how eligibility is distributed inside different states.

These three states are a visual pilot, not the geographic scope of the data pipeline. The project
is national. The simplified tract geometry is approved for display only and cannot be used to
derive adjacency, distance, or spatial weights.

### 10. Tract HPI change, 2020-2025 and 2024-2025

`10_hpi_change_2020_2025_maps.png` uses fixed observed endpoints for the three pilot states. The
long view shows cumulative change from 2020 through 2025; the short view shows the latest
one-year change from 2024 through 2025.

The same scale is used across states for each measure, missing tracts are gray, and color limits
are clipped at the 5th and 95th percentiles so a small number of extremes do not flatten the rest
of the map. Compare broad geographic patterns, then use the recent view to see whether current
movement aligns with the five-year pattern. The maps are descriptive and cannot identify the
cause of a gain or decline.

### 11. County HPI trend story

`11_county_hpi_trend_story.png` dissolves display geometry to county shapes, maps median tract
change, and pairs the map with a scatterplot of 2020-2025 change against 2024-2025 movement.

The county median is a display summary of observed tract changes, not a newly estimated county
HPI. The paired layout makes the intended finding testable: a county can have strong cumulative
growth since 2020 while its latest movement is weaker or negative. The supporting scatterplot
should be read with the map rather than treating color alone as the analysis.

### 12. State forecast coverage by Census region

`12_state_forecast_coverage.png` reports current forecast-candidate share for every state, grouped
by Census region. It confirms that the source pipeline is national while making within-region
coverage differences visible.

The percentages describe target availability and history depth. They do not rank expected market
performance, model accuracy, or neighborhood quality.

## Filters and visual assumptions

| Choice | Current rule | Why it matters |
|---|---|---|
| Historical HPI view | Observation year 1990 or later | Keeps the temporal figure focused on the period with broader tract coverage |
| Map pilot states | Arizona, Michigan, and Pennsylvania | Provides contrasting, reviewable examples; it does not limit the national tables or models |
| Long and recent map periods | 2020-2025 and 2024-2025 with observed endpoints | Prevents tracts with different “latest” years from being compared as though the dates match |
| Choropleth limits | 5th-to-95th percentile for the mapped metric | Preserves visible variation; extreme observations still exist in the source table |
| Missing map values | Dedicated gray | Separates unavailable measurements from a low or negative value |
| Housing bands | Based on ACS attached plus detached single-family share | Makes FHFA representativeness visible |
| ACS uncertainty | Published 90% MOE divided by absolute estimate | Allows measures on different scales to be compared, with caution near zero |
| Geography | Canonical 2020 display geometry | Supports consistent maps but not spatial modeling |

## What the EDA establishes

- The public-source pipeline supports national current profiles and historical modeling, but
  forecast coverage is not uniform.
- FHFA availability is meaningfully related to housing composition, so coverage and errors must
  be reported alongside forecasts.
- Geography changes at 2020 require separate stable and broad cohorts.
- HPI behavior varies by time and place, supporting temporal validation and regional baselines.
- The approved model features are sufficiently populated for a training-fitted imputation
  pipeline.
- Five-year forecasting has too few independent training origins for a strong headline claim.

The EDA does not establish a final forecasting model, prove that current similarity matches are
useful, or make a causal claim about why a neighborhood changed. Those questions belong to model
evaluation and, later, the application.
