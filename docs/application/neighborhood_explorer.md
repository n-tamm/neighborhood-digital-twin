# Neighborhood Explorer

## Purpose

The first application release turns the existing analytical products into one understandable
neighborhood investigation flow. It is not a generic dashboard and does not assign a neighborhood
score. A user starts with a place, sees what evidence is available, and can then move between the
current profile, the quality-gated forecast, historical analogues, Data Science Results,
and methods.

The layout takes inspiration from the information hierarchy used by public map tools such as the
[Opportunity Atlas](https://opportunityatlas.org/): persistent place controls, a dominant map,
and nearby contextual evidence. No source code or visual implementation was copied. The project
uses its own data contracts, language, component design, and model boundaries.

## Implemented user flow

1. **Choose how to find a tract.** In live mode, the expanded, recommended control accepts a street
   address and asks the public Census Geocoder to identify its tract and recognizable place or
   county context. A user therefore does not need to know a tract number. The left panel also
   accepts a county, state, or optional exact 11-digit 2020 tract GEOID. The main geography panel
   supports two map paths: select a nearby tract from the local map, or open `Browse U.S.`, select
   a state and county, and click a tract-center point over familiar basemap labels. The text list
   remains as an accessible alternative and includes county, state, population, both forecast
   horizons, and analogue availability.
2. **Choose the analogue horizon.** One-year and three-year controls affect historical outcome
   evidence only. They do not change or imply a forecast.
3. **Check evidence availability.** Status badges show whether the current profile, FHFA history,
   analogue result, and forecast are available. Text and symbols accompany color.
4. **Orient and navigate on the map.** The selected tract is shown with both a visible point and
   its simplified outline within nearby tract boundaries. A local tract click changes the active
   neighborhood. The state map colors only the share of tracts that support the complete analogue
   method, while its hover and selected-state cards also report one- and three-year forecast
   coverage. A forecast is counted when both supervised model rows exist. It does not score
   housing markets or neighborhood quality.
5. **Open a focused tab.** Overview, Forecast, Historical analogues, Data Science Results, and
   Methods & limitations keep different evidence types from being blended together.

## Screen responsibilities

### Overview

The overview reports the current ACS population, housing units, household income, rent, housing
structure mix, occupancy, and tenure. It then shows observed FHFA HPI history. The left chart axis
retains the observed index. A display-only right axis anchors the latest observed HPI point to the
ACS median owner-occupied value and scales the earlier index path proportionally. This is a more
readable scale, not observed sale prices or an individual-property valuation. The housing mix is
important because FHFA outcomes cover the single-family market while the profile covers the full
housing stock.

### Forecast

The forecast screen shows regularized-linear and gradient-boosted-tree estimates at one and three
years. Cards translate cumulative log change into total percentage change and retain the average
annual rate. A grouped chart compares both models, their calibrated ranges, and a clearly separate
state-trend baseline. An app-level series key appears immediately above the plot so the navy linear
bars, teal tree bars, and gold baseline diamonds can be identified without hovering or depending
on Plotly's embedded legend placement. Extra left margin and
automatic axis sizing keep the y-axis label visible.

Later-period evaluation details are available in an optional section. Published model results stay
visible even when they miss an evaluation check.

The screen also lets a user apply the modeled tract-HPI change to a reference dollar amount. This
is a display-only translation for understanding scale. It does not change a prediction, use
property characteristics, or estimate the future value of an individual home. The default reference
is the ACS median owner-occupied value when available, and the user can replace it. The point amount
applies the model's cumulative HPI change to that reference. The displayed range applies the lower
and upper bounds from the model-horizon's 90% split-conformal interval. An expandable explanation
reports the calibration sample size and clarifies that the interval comes from absolute errors on
a reserved historical calibration period.

### Historical analogues

The analogue screen reads one complete validated release. It provides the number and geographic
diversity of matches, the descriptive distribution of their observed later outcomes, a ranked
match table, five feature-family gaps, plain-language strongest-shared and largest-difference
callouts, side-by-side tract footprint maps, and the selected match's observed post-match
trajectory.

The ranked county table is the one detailed-match selector. Selecting a row changes the footprint,
feature-gap explanation, and observed trajectory below it. The national map remains available for
zoom and hover context, but it does not compete with the table for selection state.

The page repeatedly labels those outcomes as historical evidence. Similarity distance explains
retrieval, not why prices later changed, and a historical path is not presented as a causal or
probabilistic forecast.

### When a result is unavailable

The Forecast and Historical analogues tabs explain missing results for the selected tract and
horizon. Forecast groups horizons when they share an explanation. Each explanation uses the
availability record, the release's starting year, and the tract's source data.

- **Missing forecast or historical matches.** Both products require a usable FHFA single-family
  home price index for the release's starting year. The forecast uses it as the starting point
  for price change. Historical matching uses it to compare recent price trends with earlier
  neighborhoods. When the starting value is missing, the app names the year and gives the latest
  usable observation or says that the tract has no usable FHFA history.
- **Missing Census estimates or display data.** The app identifies missing Census inputs when
  the records support that explanation. A gap in the current Census profile can coexist with
  published model results because the model uses data available at its starting point. Overview
  explains absent Census profiles, empty FHFA histories, and missing inputs for the illustrative
  dollar scale. Missing display boundaries and missing annual observations within historical
  match paths receive their own notes.
- **Missing release evidence.** A missing availability record, a result that could not be loaded,
  and an unpublished result with no confirmed cause each get their own explanation. The app
  reports the source gap or release status it can verify.

The November 27, 2026 audit checked all 85,528 tracts for both products at both horizons. Every
unavailable forecast or match lacked the usable 2025 starting index. For example, Washtenaw
County, Michigan tract 4260.02 has 38 usable annual observations through 2024. Its current Census
profile also lacks median gross rent, which the app reports as a separate gap. The detailed audit
records the coverage counts, other tract examples, and checks against live Databricks data.
[Nationwide availability audit](deployment_and_testing.md#nationwide-availability-audit)

### Data Science Results

This screen explains the analytical sequence without requiring Databricks access. Data foundation,
forecasting, and historical-analogue sections use reviewed figures generated by the project's EDA
and modeling jobs. Commentary states the target, time split, evaluation method, major numerical
result, release decision, and product consequence. The page does not fit models or recompute
metrics in a user session.

### Methods and limitations

This screen records the release ID, schema version, data year, profile build, and upstream
similarity run. It also states the main product exclusions: individual property valuation,
neighborhood quality ranking, buy/sell advice, and causal comparison.

## Responsive and accessible behavior

The interface uses Streamlit's responsive columns and a compact breakpoint for small screens.
Central status messages do not rely on color alone. Charts retain hover labels and the application
does not hide Streamlit's accessibility controls. Formal keyboard, screen-reader, contrast, and
mobile visual review are still required before a final release.

## Visual system

The current design uses a dark navy background rather than pure black. Raised surfaces remain
visibly separate, primary text stays near white, and muted text retains contrast. Teal identifies
the current neighborhood, gold identifies historical analogue evidence, and blue identifies an
observed primary series. Dark Carto map tiles retain roads and place context beneath brighter tract
outlines. Color is paired with labels, ranks, status symbols, and hover text rather than carrying
meaning by itself.
