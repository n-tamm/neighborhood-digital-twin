# 01 — Data Discovery and Feasibility

## Purpose

The first technical milestone should answer whether the proposed tract-level study is possible with the data, time, and free compute available. It is cheaper to narrow the geography or target now than after the application and model interfaces are built.

## Questions to settle

- How many tracts and forecast-origin years have usable FHFA targets?
- Where is coverage systematically missing, and what kinds of communities may be underrepresented?
- Which ACS fields have stable definitions, acceptable margins of error, and defensible release timing?
- Can older observations be mapped to 2020 tracts with acceptable loss and uncertainty?
- Are one-, three-, and five-year targets available for enough independent periods?
- Can the pilot run locally and in Databricks within quota and storage limits?
- Which demonstration metros provide useful differences in size, region, growth, and data coverage?

## Pilot scope

Use three to five metros or states that expose different problems rather than only convenient places. Detroit is a useful candidate because it matches the project's Michigan context and prior neighborhood-trajectory literature. Add at least one faster-growing market and one place with thinner coverage. The pilot is for stress testing, not selecting favorable results.

## Work plan

### FHFA audit

Record the current file location, publication date, years, fields, row count, tract count, missing-value behavior, geography vintage, and hash. Profile first and last observation per tract, gaps within each series, and target availability by year and metro. Do not impute the prediction target during the feasibility decision.

### ACS audit

Choose 8–12 variables that cover population, income, housing units, vacancy, tenure, housing burden, and one or two other high-value dimensions. Pull estimates and margins of error together. Record the ACS table, concept, universe, variable label, release year, survey window, and API availability.

### Geography audit

Construct zero-padded GEOIDs and measure direct matches to 2020 tract identifiers. For earlier tract vintages, inspect one-to-one, split, merge, and complex mappings. Map row loss and identify whether problem areas are concentrated in specific states or metros.

### Target and baseline spike

Define a provisional forecast origin and calculate one-year and three-year HPI changes without using future information in features. Fit persistence and regional-trend baselines. The goal is not a final score; it is to verify that the target, timing, and evaluation code behave sensibly.

### Scale estimate

Estimate raw and processed storage, national row counts, memory needs, expected API calls, Spark runtime, and app-bundle size. Test any outbound-network restriction before designing Databricks acquisition around live downloads.

## Required outputs

- source feasibility table with access, license, time, geography, and coverage findings;
- FHFA coverage and row-attrition report;
- ACS variable shortlist with margins-of-error assessment;
- geography match report and pilot map;
- provisional target definition and baseline results;
- national versus selected-metro resource estimate;
- written go, narrow, or fallback recommendation.

## Acceptance checks

The original planning thresholds are:

- at least 95% successful geography matching among retained FHFA rows;
- at least 20,000 usable tracts and eight forecast-origin years for a national design;
- enough recent observations for a locked temporal test;
- stable coverage in at least ten varied metros if national modeling is retained;
- a reproducible pilot baseline from a clean run;
- no dependence on restricted, proprietary, or individual-level data.

These are decision thresholds, not claims about data quality. If they are missed, record the evidence and choose a narrower metro set or county fallback rather than quietly relaxing filters.

## Common failure modes

- counting overlapping ACS releases as independent annual samples;
- treating an FHFA missing value as zero change;
- building targets before deciding what was known at the forecast date;
- selecting pilot metros only because they have complete data;
- assuming a crosswalk is valid because row counts match;
- spending the feasibility week on a polished interface instead of coverage evidence.

## Handoff

The accepted scope, source shortlist, target timing, and geography choice become decision records. Acquisition and geography work should not begin at full scale until these decisions are clear.
