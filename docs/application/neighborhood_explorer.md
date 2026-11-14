# Neighborhood Explorer

## Purpose

The first application release turns the existing analytical products into one understandable
neighborhood investigation flow. It is not a generic dashboard and does not assign a neighborhood
score. A user starts with a place, sees what evidence is available, and can then move between the
current profile, the pending forecast, historical analogues, and methods.

The layout takes inspiration from the information hierarchy used by public map tools such as the
[Opportunity Atlas](https://opportunityatlas.org/): persistent place controls, a dominant map,
and nearby contextual evidence. No source code or visual implementation was copied. The project
uses its own data contracts, language, component design, and model boundaries.

## Implemented user flow

1. **Choose how to find a tract.** The left panel accepts county, state, or an exact 11-digit 2020
   tract GEOID. The main geography panel also supports two map paths: select a nearby tract from
   the local map, or open `Browse U.S.`, select a state, and narrow to county and tract.
2. **Choose the analogue horizon.** One-year and three-year controls affect historical outcome
   evidence only. They do not change or imply a forecast.
3. **Check evidence availability.** Status badges show whether the current profile, FHFA history,
   analogue result, and forecast are available. Text and symbols accompany color.
4. **Orient and navigate on the map.** The selected tract is shown with both a visible point and
   its simplified outline within nearby tract boundaries. A local tract click changes the active
   neighborhood. The state map colors only the share of tracts that support the complete analogue
   method; it does not score housing markets or neighborhood quality.
5. **Open a focused tab.** Overview, Forecast, Historical analogues, and Methods & limitations keep
   different evidence types from being blended together.

## Screen responsibilities

### Overview

The overview reports the current ACS population, housing units, household income, rent, housing
structure mix, occupancy, and tenure. It then shows observed FHFA HPI history. The housing mix is
important because FHFA outcomes cover the single-family market while the profile covers the full
housing stock.

### Forecast

The current forecast screen is a product boundary, not an unfinished blank page. It states that no
approved serving output exists, shows whether the selected tract is a candidate, and records what
the final screen must contain: a one-year primary estimate, a separately justified longer horizon,
a calibrated interval, a baseline comparison, and model drivers. No validation prediction or
analogue outcome is displayed as the tract's expected future.

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
