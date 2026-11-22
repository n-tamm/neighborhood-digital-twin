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
2. a county search and an exact GEOID search both work;
3. at least one available and one unavailable tract/horizon state render correctly;
4. the active analogue release ID is the same across availability, summary, match, explanation,
   and path, and the forecast tables share their own complete release ID;
5. all ten live matches appear even though the local fixture contains only one;
6. no analogue outcome is described as the selected tract's forecast, and the failed three-year
   forecast appears as withheld rather than missing;
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

## Forecast release verification

On November 19, 2026, job 701 activated a forecast release with 46,719 one-year rows and 171,056
availability rows across both supported horizons. Direct reconciliation found no invalid interval
ordering. All 85,528 three-year rows are unavailable with
`horizon_failed_locked_release_gate`; one-year gaps retain tract-level readiness reasons.

The bundle granted the app service principal read-only access to the two forecast tables and the
app restarted successfully. Live review should now confirm that an eligible tract shows the point,
90% interval, state baseline, and release lineage, while the three-year warning communicates the
locked failure metrics clearly.

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
