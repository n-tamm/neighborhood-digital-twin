# Figure 1: Current National Pipeline Attrition

**File:** `01_pipeline_attrition.png`

## Question

How does the current national tract universe narrow as the project requires ACS coverage,
similarity features, FHFA history, and forecast eligibility?

## Construction

The figure reads the governed state-coverage summary and totals five counts: canonical tracts,
tracts with a current ACS profile, similarity candidates, tracts with any FHFA history, and
current forecast candidates. The bars are displayed as counts of Census tracts.

## Interpretation

The largest practical narrowing occurs around FHFA availability. That is expected because FHFA
tract HPI covers a filtered single-family market and requires usable price history. The descriptive
and similarity populations can remain broader because they do not require that target.

Read the chart as an availability summary, not as a final model funnel. A candidate count says
that the required source fields exist; it does not guarantee that every tract will receive a
prediction for every origin and horizon.

## Limits

- The bars are related populations, but the visual should not be used to infer row-level causes
  of exclusion.
- Counts do not indicate model accuracy or neighborhood quality.
- Current coverage does not describe pre-2020 tract-vintage comparability.

**Source contract:** [`gold_eda_state_coverage`](../../data/24_gold_eda_state_coverage.md)

**Rendering code:** [`03_render_eda_figures.py`](../../../notebooks/04_exploration/03_render_eda_figures.py)
