# Current Project State and Next Work

This is the implementation handoff as of November 21, 2026. It records what is actually running,
what the current evidence supports, and what should happen next. Detailed execution order remains
in [the pipeline runbook](docs/PIPELINE_RUN_ORDER.md).

## Current answer

The public-data pipeline, current historical-analogue system, first production forecast release,
and interactive Databricks application are implemented. The application now combines current
community context, observed FHFA history, approved historical analogues, and a quality-gated
one-year forecast with a calibrated interval. The three-year forecast candidate remains in the
evaluation record but is deliberately unavailable in the app because it failed the locked test.

The remaining work is no longer basic pipeline construction. It is coordinated refresh work,
application review, report integration, and targeted model research that must preserve the
already opened locked-test result.

## Data and pipeline checkpoint

- ACS covers all 50 states and Washington, D.C., for 2010-2024. FHFA tract HPI history extends
  through 2025.
- The governed geography hierarchy is country, Census region, Census division, state, county,
  and 2020 Census tract. ZIP codes are not forced into this hierarchy.
- Longitudinal features crossing the 2020 tract redesign are limited to the reviewed 59,607-tract
  stable cohort. Post-2020-only tracts remain available for current profiles and later-origin
  modeling where no cross-vintage claim is needed.
- Fully observed FHFA targets are no longer removed merely because they cross 2019-2020. The
  stable-cohort rule controls the feature history that crosses the redesign. The rebuilt panel has
  no cross-2020 non-stable modeling row.
- One-year training uses 2011-2020 origins, validation uses 2021-2022, calibration uses 2023, and
  the locked test uses 2024. Three-year training uses 2011-2016, validation uses 2017-2018,
  calibration uses 2019, 2020-2021 are purged, and the locked test uses 2022.
- Jobs 301, 302, 500, 504, 605, 701, 400, 401, 600, 606, and 900 have been run successfully from
  the corrected contract. Metadata, validation summaries, and report-ready figures are current.

## Forecast checkpoint

### Frozen development choices

- The one-year champion is a Spark gradient-boosted tree with depth 2 and 50 iterations. Its
  corrected validation MAE is 0.0733 in cumulative log HPI change.
- The three-year development choice is the state-current-trend baseline. Its corrected validation
  MAE is 0.0666. This choice was frozen before calibration and locked-test outcomes were read.
- Prediction intervals use a 90% split-conformal absolute-residual radius estimated from one
  reserved calibration origin per horizon.

### Locked results and release decision

| Horizon | Locked observations | Champion MAE | Zero-change MAE | Interval coverage | Decision |
|---|---:|---:|---:|---:|---|
| 1 year | 42,082 | 0.0599 | 0.0627 | 89.4% | Published |
| 3 years | 45,887 | 0.2943 | 0.1566 | 48.2% | Withheld |

The one-year champion clears the minimum release rules: at least 1,000 observations, MAE no worse
than zero change, and empirical interval coverage within ten percentage points of the nominal 90%
level. It is not uniformly best—the state-trend baseline has slightly lower one-year locked MAE—
so the app displays that baseline beside the model rather than claiming universal superiority.

The three-year method fails both accuracy and interval-coverage requirements. Persisting the
unusually high 2022 statewide annual trend for three years produced mean predicted cumulative log
growth of 0.442 versus 0.149 observed. This is a genuine temporal-regime failure, not a geography
mapping error. It must remain in the final results and must not be retuned away using the locked
outcome.

### Current serving release

- Job 701 publishes 46,719 approved one-year forecasts from a 2025 origin with valid point,
  baseline, and interval fields.
- Every one of the 85,528 current profile tracts has an availability row for both one- and
  three-year horizons.
- The entire three-year horizon is marked `horizon_failed_locked_release_gate`; tract-level
  one-year gaps retain model-readiness reasons rather than silently falling back.
- Three final forecast figures are versioned in Databricks and exported locally under the ignored
  `reports/generated/model-evaluation/forecast-final-20261119T173650231784Z/` review directory.

## Similarity checkpoint

- Weighted standardized distance with ten distinct physical tracts remains the selected
  historical-analogue representation. PCA remains an audit lens.
- The exact KD-tree retrieval design reproduced the exhaustive reference and supports national
  batch generation.
- The active analogue release contains ranked matches, summaries, availability, deterministic
  match explanations, and observed annual outcome trajectories.
- Analogue outcomes remain descriptive historical context. They are not the primary forecast and
  are not a causal estimate.

The corrected historical target and model-readiness build is newer than the active analogue
release. Before the final report and deployment freeze, rerun the dependent similarity sequence
from the earliest workflow whose inputs changed, then republish jobs 700 and 800. Do not mix old
similarity metrics with a newly rebuilt candidate pool without recording the lineage change.

## Application checkpoint

- The Databricks app is live at
  `https://neighborhood-intelligence-3866391918408215.aws.databricksapps.com`.
- The live repository independently selects complete analogue and forecast releases so it cannot
  mix partial table versions.
- The Forecast tab shows the one-year point estimate, 90% interval, state-trend baseline, target
  scope, driver summary, and release lineage.
- The three-year horizon is shown as withheld with the locked MAE, zero-change comparison, and
  failed coverage requirement.
- Connecticut history uses the audited planning-region-to-2020 tract bridge. Map selection uses
  visible points at national extent and canonical tract outlines at local extent.
- Sample mode remains intentionally small and does not contain a production forecast. Live app
  review must therefore be performed in Databricks.

## Immediate next sequence

1. **Review the live forecast experience.** Check a mix of eligible and ineligible tracts across
   regions, confirm the interval and baseline language is understandable, and confirm that the
   withheld three-year state is obvious rather than looking like missing data.
2. **Refresh dependent similarity outputs.** Rebuild only the workflows affected by the corrected
   historical target/model-readiness lineage, validate changes, and republish the analogue serving
   and communication products.
3. **Create the integrated model story.** Combine the corrected validation, locked-test,
   uncertainty, release-gate, and analogue results in the report and standup materials. Preserve
   the distinction between development evidence and final locked evidence.
4. **Perform application acceptance testing.** Verify content delivery, empty states, maps,
   Connecticut behavior, release IDs, responsiveness, and practical usefulness. Avoid substituting
   click analytics for correctness and clarity.
5. **Polish and freeze deployment.** Remove stale generated artifacts, confirm every final figure
   can be reproduced, run the full test suite and bundle validation, and record the final commit
   and Databricks release IDs.

## Research after the reported three-year result

Any new three-year work is a separate research iteration. Plausible directions include damped
trend baselines, direct modeling of change relative to a state or national market path, and
regime-aware calibration using more independent origins. Those methods may be useful for a future
version, but they cannot replace or relabel the already opened three-year locked result in this
capstone.

## Known repository follow-up

The tracked Python files and notebooks now contain the required AI-assistance wording and a model
label, and saved output containing a personal absolute path was removed from the local forecast
demonstration notebook. The feature-ablation notebook records additional Copilot assistance, but
the contributing author still needs to confirm its exact underlying model and any available
settings. Those details must not be guessed.

The workspace also contains two user-scoped deployments of most bundle jobs. A run-history audit
found one successful forecast-baseline run from the second deployment and no ETL, similarity,
serving, presentation, or metadata runs from it. The corrected canonical forecast sequence ran
later and superseded that result. Use the canonical maintainer profile, verify `bundle summary`,
and invoke jobs by bundle key during the final similarity refresh. A future shared CI/CD bundle
must bind the existing canonical resources before obsolete duplicate jobs are removed.
