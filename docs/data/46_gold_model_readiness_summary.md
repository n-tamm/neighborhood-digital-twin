# `gold_model_readiness_summary`

[Back to the data documentation index](README.md)

- **Layer:** Gold model readiness
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_model_readiness_summary`
- **Sample:** [gold_model_readiness_summary.jsonl](../../data/samples/gold_model_readiness_summary.jsonl)
- **Grain and key:** one summary group, optional horizon, dimension name, and dimension value.
- **Purpose:** makes feature-cohort and model-panel coverage quick to review without scanning the
  two-million-row modeling panel.
- **Main structure:** feature cohort, temporal role, geographic role, or modeling cohort; row and
  distinct-tract counts; independent origin-year count and range; observed-target count; locked
  temporal-evaluation count; build lineage.

The current table has 95 rows. It is useful for release checks and planning, but it does not
replace the append-only quality metrics. Hard invariants such as duplicate keys, future ACS use,
target timing, split reconciliation, and holdout-region count remain in
`workspace.neighborhood_twin_quality.gold_quality_metrics`.

The summary makes the main limitation visible: the five-year horizon has many tract rows but only
three independent training origins. Row volume should never be mistaken for independent temporal
evidence when repeated tract observations and overlapping ACS releases are involved.

It also profiles 34 raw features, housing-mix bands, and housing-unit relative-MOE bands. Core ACS
composition fields are complete after the model-feature eligibility join, while exact five-year
HPI lags are present for 92.1 percent of rows and median gross rent for 97.2 percent. These
summaries are intended to drive explicit preprocessing and subgroup evaluation decisions rather
than a blanket complete-case filter.
