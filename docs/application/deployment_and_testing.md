# Application Deployment and Testing

## Local sequence

From the repository root:

```powershell
python -m pip install -e ".[dev,app]"
python -m ruff check app tests/unit/test_app_data.py tests/unit/test_app_presentation.py
python -m mypy app/neighborhood_app tests/unit/test_app_data.py tests/unit/test_app_presentation.py
python -m pytest tests/unit/test_app_data.py tests/unit/test_app_presentation.py
python -m streamlit run app/streamlit_app.py
```

Sample mode is credential-free and is the correct mode for routine UI work. It is not a substitute
for a live contract check before a release.

## Databricks deployment sequence

The Databricks CLI must be authenticated with the `neighborhood-twin` profile. Then run:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run neighborhood_housing_intelligence --profile neighborhood-twin -t team
databricks apps get neighborhood-intelligence --profile neighborhood-twin --output json
```

Bundle deployment creates or updates the app definition and uploads source, but the bundle run is
what starts compute and deploys the app revision. The app resource injects the warehouse ID into
`app.yaml`; host and service-principal credentials come from the Databricks runtime.

The initial app is private. Do not grant the workspace-wide `users` group access as an incidental
part of source deployment. Add the partner or another reviewer explicitly after the owner has
verified live data, caveats, and error handling.

## Implemented automated checks

- configuration mode, warehouse, and SQL-identifier validation;
- independent analogue- and forecast-release completeness and validated-status checks;
- real local fixture loading and horizon availability;
- known-answer formatting and place labels;
- polygon-map construction and selected-boundary layering;
- lightweight county tract-map construction and point-selection identifiers;
- one-connection batching for the nine neighborhood result sets when a forecast release exists;
- preservation of missing HPI observations;
- full Streamlit startup in sample mode with no rendered exception;
- Ruff and mypy checks for the application modules; and
- live Declarative Automation Bundle validation.

The smoke test previously found a duplicate Plotly element ID because the same map appears in two
screen locations. Unique component keys now make that layout explicit. The first chart run also
identified Plotly's deprecated Mapbox trace; the implementation now uses the current MapLibre map
trace.

## Required release review

Before calling an app revision complete, check:

1. the app process reaches a running state and the root page loads;
2. address lookup, county/state search, exact GEOID search, and county-map selection all work;
3. at least one available and one unavailable tract/horizon state render correctly;
4. the active analogue release ID is the same across availability, summary, match, explanation,
   and path, and the forecast tables share their own complete release ID;
5. all ten live matches appear even though the local fixture contains only one;
6. no analogue outcome or trend baseline is described as the selected tract's supervised
   forecast, and weak model results remain visible with their evaluation warnings;
7. desktop and narrow layouts retain readable titles, legends, tables, and caveats; and
8. the service principal has no write permission and no access to raw or modeling tables.

Visual accessibility review and live browser review are still manual gates. A future CI job may
run the local smoke tests, but it should not contact the shared warehouse on every pull request.

## Initial live verification

On November 14, 2026, the private app definition deployed successfully and reached `RUNNING` with
a successful snapshot deployment. An authenticated root request returned HTTP 200. The exact live
repository path selected release `analogue-20261113T132155097077Z`, returned 12 bounded results for
the default county search, loaded 34 FHFA history rows, and loaded 20 match rows: ten for each of
the one- and three-year horizons. A full Streamlit render against those live tables completed with
no rendered exception. This verifies initial connectivity and contract compatibility; it does not
replace the remaining manual browser, responsive-layout, and accessibility review.

## Boundary-map and latency verification

The boundary iteration was tested against the same warm SQL warehouse and Autauga County tract
used for the initial live review. Before batching, repository startup took 3.11 seconds, search
took 1.65 seconds, and neighborhood loading took 11.57 seconds. After batching and adding geometry,
startup took 3.14 seconds, search took 1.68 seconds, and neighborhood loading took 6.22 seconds.
The selected view returned 17 local context polygons and all 20 analogue polygons. The complete
live Streamlit render finished in 8.92 seconds with eight Plotly figures and no exception.

These are development measurements from one warm-warehouse run, not a service-level guarantee.
They demonstrate that connection reuse more than offsets the added geometry payload. Cold app or
warehouse startup can still take longer, while cached tab and horizon changes should be much
faster because they do not query the warehouse again.

Map construction was also exercised against Michigan, New York County, Alaska, and Honolulu
tracts. Their context windows returned 51, 71, 80, and 31 polygons respectively without a query or
figure error; Alaska reached the intentional 80-row cap. The New York example also confirmed that
the local boundary map remains available when a selected analogue horizon has no matches. This is
a structural check of framing and empty-state behavior, not a substitute for viewing each map in
a browser.

## Superseded version-1 forecast release verification

On November 19, 2026, job 701 activated a version-1 release with 46,719 one-year rows and 171,056
availability rows across both supported horizons. Direct reconciliation found no invalid interval
ordering. All 85,528 three-year rows are unavailable with
`horizon_failed_locked_release_gate`; one-year gaps retain tract-level readiness reasons.

The bundle granted the app service principal read-only access to the two forecast tables and the
app restarted successfully. This release is now superseded by the version-2 two-model contract and
must not be treated as the final forecast design.

## Version-2 forecast release verification

On November 22, 2026, jobs 504, 605, and 606 completed under forecast finalization run
`29c68a5af1e74daab6e06ff7aa2aa9e9`. Job 701 initially stopped because the existing version-1
serving tables had an incompatible schema. The two legacy tables were preserved under explicit
schema-v1 backup names, and rerun `1072028212048142` then created clean version-2 tables and
activated release `forecast-20261122T164538152848Z`. Job 900 reapplied governed metadata. After
the version-2 tables, manifest, representative tract, and app startup were validated, the temporary
backups and obsolete `forecast_release_gate` table were removed; their replacement is
`forecast_evaluation_threshold`.

The active release contains 186,876 forecast rows: 46,719 eligible tracts multiplied by two
horizons and two supervised models. Its availability product contains 171,056 tract-horizon rows,
with 93,438 available. The manifest has both expected components, and tract `01001020300` returns
regularized-linear and gradient-boosted-tree forecasts at both one and three years. State trend is
retained only as labeled baseline context.

The canonical app was restarted after release activation. Final application deployment
`01f1e6af5d19196980e82abe8deb8c4b` reached `SUCCEEDED`, with the app `RUNNING` and compute
`ACTIVE`. An unauthenticated endpoint check reached the expected Databricks sign-in redirect. The
Data Science Results page now uses the corrected job-606 figures. Authenticated browser review of
the revised forecast cards, warnings, figures, and narrow layout remains a manual acceptance gate.

## Final analytical refresh verification

On November 21, 2026, the corrected similarity chain refreshed jobs 501-604, published analogue
release `analogue-20261121T163609734965Z`, rebuilt both similarity figure sets, and reapplied
metadata. Manifest and table counts reconcile for all five analogue components. Both horizons
contain 46,719 available tracts with ten matches per tract; all 85,528 current tracts retain an
availability row at each horizon.

The app was restarted from the canonical bundle after publication. Deployment
`01f1e5ee73f318f08ea19c7378f192eb` reached `SUCCEEDED`, with app status `RUNNING` and compute
status `ACTIVE`. Its service principal has `CAN_USE` on one SQL warehouse and `SELECT` on exactly
twelve named profile, geography, analogue, and forecast tables. It has no raw/model-table access
and no write permission. Manual cross-browser, responsive-layout, and tract-by-tract content
acceptance remain release gates for the team.

## App Review 1 deployment verification

On November 22, 2026, the first application-review changes were deployed from the canonical
`team` bundle. Deployment `01f1e670f3b71ea380273906be0b8dbf` reached `SUCCEEDED`; the app
returned to `RUNNING` with `ACTIVE` compute. The bundle deploy changed only source files and did
not create, change, or delete a Databricks job or table resource.

The live repository contract returned all 51 state or district rows and exposed both analogue
and version-1 one-year forecast coverage. Michigan, for example, returned 2,972 current tracts,
including 2,286 analogue-ready and 2,286 forecast-ready tracts. Oakland County returned 350 tract
choices with population and both model-status fields. A full neighborhood load for tract
`01001020300` independently selected analogue release
`analogue-20261121T163609734965Z` and forecast release
`forecast-20261119T172707640214Z`, with 20 analogue rows and one version-1 forecast row. This
confirmed that the new browser fields did not mix releases or require access beyond the twelve
named read-only tables.

The optional address lookup was checked against the Census Geocoder with the Census Bureau's
known address at 4600 Silver Hill Road. It resolved to 2020 tract `24033802405` and returned
Suitland CDP, Prince George's County, Maryland as recognizable place context. The lookup still
needs one manual submission from the authenticated Databricks app to verify application-runtime
egress and the rendered privacy notice.

Streamlit is pinned to `1.55.0` for reproducible deployment. Streamlit 1.60 and later install
Starlette directly, which conflicted with the FastAPI version in the Databricks base image. The
pinned release installed without a dependency conflict, passed the local 160-test suite and a
headless sample render, and started successfully in Databricks. The eight Data Science images in
the app were also checksum-matched to their governed report sources before deployment.

Databricks still logs `Security scan failed: scanner run failed` while allowing the deployment to
complete. [Databricks documents this beta scan](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/security-scanning)
as non-blocking and records a scan that cannot complete as unavailable rather than clean. This is
therefore not a reported clean scan and not a reported vulnerability. Review the deployment's
Security tab and retry or raise the platform issue before the final release is declared secure.
Manual browser acceptance remains required for the address lookup, narrow layout, figure
readability, empty states, and cross-browser behavior.

The tract-discovery follow-up deployed on November 22 as
`01f1e67db64d1b1abeabb637ed7bfeef`. It reached `SUCCEEDED`, with the app `RUNNING` and compute
`ACTIVE`. The canonical bundle uploaded source only and left all 34 declared Databricks resources
unchanged. The current build log contains no package conflict or application startup exception;
the beta source scanner remains unavailable with the same `scanner run failed` message.

A direct read-only contract check returned 51 state or district summaries and confirmed the
version-1 release had no three-year forecasts. The Oakland County check returned 350 current tract
choices, 299 version-1 one-year forecasts, no three-year forecasts, and display bounds
for all 350 tracts. State, county, tract, and search queries all returned the new horizon-specific
fields. This validates the data behind the new coverage cards, labels, and county tract-location
map; manual browser review still needs to confirm the interaction and visual spacing.
