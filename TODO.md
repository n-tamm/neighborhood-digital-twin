# Current Project State and Next Work

This is the implementation handoff as of November 22, 2026. It records what is actually running,
what the current evidence supports, and what should happen next. Detailed execution order remains
in [the pipeline runbook](docs/PIPELINE_RUN_ORDER.md).

## Current answer

The public-data pipeline, historical-analogue system, corrected two-model forecast release, and
interactive Databricks application are implemented. The app shows regularized-linear and gradient-
boosted-tree results at both one and three years. State and county trends remain baselines, and an
evaluation warning stays visible without hiding the one-year linear result.

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
- Jobs 301, 302, 500, 400, 401, 600, and the similarity workflows have current upstream outputs.
  Forecast jobs 504, 605, 606, 701, and 900 completed on November 22 under the corrected two-model
  contract. The superseded version-1 serving tables are no longer active.

## Forecast checkpoint

### Corrected two-model contract

- The project models are L2-regularized linear regression and Spark gradient-boosted trees.
- Both models are retained at one and three years. The one-year tree uses depth 2 and 50
  iterations; the three-year tree uses depth 4 and 30 iterations. Linear uses L2 parameter 0.05.
- Validation MAE is 0.0733 for the tree and 0.0766 for linear at one year, and 0.0807 for the tree
  and 0.1033 for linear at three years.
- State trend achieved lower three-year validation MAE than either supervised model, but it is a
  baseline result rather than the project model.
- Job 504 now calibrates a separate 90% split-conformal interval for every model-horizon pair.
- Job 605 records threshold warnings separately for each pair. A warning does not withhold the
  forecast or promote a baseline.
- Job 701 publishes both supervised results at both horizons for each model-ready tract.

### Completed forecast sequence

- Jobs 504, 605, and 606 succeeded under finalization run
  `29c68a5af1e74daab6e06ff7aa2aa9e9`; all four supervised model-horizon combinations are present.
- Job 701 activated version-2 release `forecast-20261122T164538152848Z` with 186,876 forecast rows,
  46,719 eligible tracts, four model-horizon combinations, and 171,056 availability rows.
- Job 900 reapplied descriptions and column comments. Corrected samples, figure assets, and result
  documentation were refreshed from the governed outputs.
- The app was redeployed as `01f1e6af5d19196980e82abe8deb8c4b`, reached `SUCCEEDED`, and returned
  to `RUNNING`. Manual browser acceptance of forecast cards, warnings, figure readability, and
  responsive layout remains open.

The prior state-trend finalization remains historical evidence of the design error. Because its
later outcomes were already viewed, the corrected run must not be described as a new untouched
model-selection test or used to retune the fixed model settings.

## Similarity checkpoint

- Weighted standardized distance with ten distinct physical tracts remains the selected
  historical-analogue representation. PCA remains an audit lens.
- The exact KD-tree retrieval design reproduced the exhaustive reference and supports national
  batch generation.
- The active analogue release contains ranked matches, summaries, availability, deterministic
  match explanations, and observed annual outcome trajectories.
- Analogue outcomes remain descriptive historical context. They are not the primary forecast and
  are not a causal estimate.

The full dependent sequence was refreshed on November 21 from jobs 501 through 604, then jobs 700,
800, 600, and 900. Active release `analogue-20261121T163609734965Z` is tied to corrected
model-readiness build `20261119T161033445114Z` and exact-tree run
`344fbe71819f4a779b36701a5fdaf7b8`. Both horizons provide ten matches for 46,719 eligible tracts;
all 85,528 current tracts retain an explicit availability row per horizon.

The expanded validation result still supports weighted standardized matching over PCA. The
distance-weighted analogue MAE is 0.0794 at one year and 0.0840 at three years. Analogues beat zero
change at both horizons but do not beat the best forecast comparator, so their application role
remains historical context and a secondary estimate.

## Application checkpoint

- The Databricks app is live at
  `https://neighborhood-intelligence-3866391918408215.aws.databricksapps.com`.
- The live repository independently selects complete analogue and forecast releases so it cannot
  mix partial table versions.
- The corrected Forecast tab is designed to show linear and boosted-tree point estimates and 90%
  intervals at one and three years, with the state trend kept separate as a baseline.
- Evaluation warnings report MAE, zero-change comparison, and interval coverage without hiding a
  model result.
- Connecticut history uses the audited planning-region-to-2020 tract bridge. Map selection uses
  visible points at national extent and canonical tract outlines at local extent.
- App Review 1 changes are implemented on the application branch: all browser counts use readable
  thousands separators; state, county, search, and tract choices separate analogue and forecast
  status by horizon; and live mode opens with a
  recommended Census address-to-2020-tract lookup with an explicit external-request notice.
  County browsing adds a clickable tract-center map over familiar basemap labels, while its text
  choices retain county, state, population, both forecast horizons, and analogue status.
- A Data Science Results tab now walks through geography readiness, the two supervised forecast
  models and their baselines, later-period error and uncertainty, and similarity method selection.
  Its corrected forecast assets come from job-606 build
  `forecast-final-20261122T163847149439Z`.
- Sample mode remains intentionally small and does not contain a production forecast. Live app
  review must therefore be performed in Databricks.

## Immediate next sequence

1. **Review the corrected forecast experience.** Check eligible and ineligible tracts across
   regions. Confirm that both models and horizons, their intervals, separate baseline, and the
   one-year linear warning are understandable.
2. **Review the refreshed analogue experience.** Check available and unavailable tracts, both
   horizons, match explanations, geographic diversity, observed path gaps, and release lineage.
3. **Create the integrated model story.** Combine validation, later-period error, uncertainty,
   evaluation warnings, and analogue results in the report and standup materials. Preserve the
   distinction between development evidence and later evaluation.
4. **Perform application acceptance testing.** Verify content delivery, empty states, maps,
   Connecticut behavior, address matching, comma-formatted coverage, forecast status at every
   browser level, Data Science figure readability, release IDs, responsiveness, and practical
   usefulness. Avoid substituting click analytics for correctness and clarity.
5. **Polish and freeze deployment.** Select the report figures, confirm report values against the
   final manifests, complete the remaining course deliverables, rerun the clean-checkout gates,
   and tag the reviewed commit. Do not rerun frozen models merely to improve reported results.

## Research after the current three-year models

Any new three-year method is a separate research iteration. Plausible directions include direct
modeling of change relative to a state or national path and regime-aware calibration using more
independent origins. Those methods may be useful later, but the current linear and boosted-tree
settings must not be tuned against the already inspected 2022–2025 outcomes.

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

The November 22 App Review 1 deployment used the canonical `team` bundle and changed only source
files; it did not run or modify any pipeline job. Streamlit is now pinned to `1.55.0`, which removes
the FastAPI/Starlette conflict seen with the unconstrained latest release. The latest application
deployment, `01f1e67db64d1b1abeabb637ed7bfeef`, is running successfully.
Databricks still reports
`Security scan failed: scanner run failed` without returning a vulnerability result. Databricks
documents this beta scan as non-blocking and an incomplete run as unavailable. Review the app's
Security tab, retry, or escalate the scan before final release; do not describe it as passed.

The course-specification review still has four submission-level gates outside the implemented
code: complete the final report and its team-contribution statement, select and integrate at least
three generated figures with reconciled values, produce the three-to-five-minute video or poster,
and publish the capstone-gallery post. The partner also needs to confirm the exact Copilot model
and any exposed settings for the feature-ablation notebook. Repeat the secret, path, dependency,
attribution, link, AI-disclosure, and clean-checkout audits after those final materials are added.
