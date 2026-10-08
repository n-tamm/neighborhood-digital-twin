# 11. Application and Visualization

The application is the main way a user experiences the project, but it should remain a thin, explainable layer over versioned analytical outputs. It should help someone investigate a community, not hide the evidence behind a polished score.

## Stage objective

Build a map-driven application that presents historical context, forecasts, analogues, model drivers, and scenario sensitivity through a coherent set of user tasks. The first release should be useful without requiring an AI assistant or live model training.

## Primary users and questions

The first design should support a curious resident, prospective home buyer, analyst, or planner who wants to ask:

- How has this community changed?
- What does the model expect over the chosen horizon, and how uncertain is it?
- Which historical communities looked similar at the same point in their development?
- What variables most influenced the result?
- How does the modeled distribution respond when selected inputs change?
- How does this area compare with its metro and nearby areas?

The interface should provide context for decisions, not issue investment, planning, or relocation instructions.

## Proposed information architecture

### 1. Overview

A national or regional map, search, data-coverage status, short project explanation, and a clear route into a selected tract. Avoid rendering every tract at full detail on initial load.

### 2. Community profile

Show the selected geography, current modeled state, historical trends, metro comparison, source dates, and missingness. Separate observed values from modeled or imputed values.

### 3. Forecasts

Show 1-, 3-, and 5-year outcomes where supported, with prediction intervals, baseline comparisons, backtest context, and short explanations of the strongest drivers. Do not imply that the center line is the one future that will occur.

### 4. Historical analogues

List similar tract-period observations, explain the dimensions that made them similar, and display the range of what happened next. Geography and time should remain visible so similarity does not become anonymity.

### 5. Trajectories

Present cluster or trajectory-type membership, the evidence behind the label, representative histories, and assignment confidence or stability. Labels should be descriptive rather than evaluative.

### 6. Scenario workspace

Let users adjust a small, approved set of inputs within plausible ranges. Always show the unchanged baseline next to the scenario, mark modified fields, and label results as model sensitivity rather than causal impact.

### 7. Methods and limitations

Expose data sources, version dates, model card, evaluation results, responsible-use boundaries, and known coverage gaps without making the user search the repository.

## Serving contract

The app should read an immutable serving bundle instead of rebuilding features or running training logic. The bundle should include:

- a release manifest and compatible schema version;
- tract geometries simplified for display;
- current state and historical series tables;
- forecasts and intervals;
- analogue and cluster results;
- approved scenario metadata or a lightweight inference artifact;
- explanation fields and quality flags;
- data-source and model-version metadata.

Document the detailed serving schema beside the export and loading code when it is implemented. The app must reject incompatible data rather than silently guessing at changed columns.

## Application boundaries

- `app/` owns pages, components, session state, formatting, and calls to the serving layer.
- `src/neighborhood_twin/` owns reusable data access, validation, inference, and analytical logic.
- Generated models and application data stay outside the source package and are not ordinary Git dependencies.
- Configuration should choose the bundle and runtime environment; application code should not contain local paths or secrets.

## Performance strategy

- Precompute tract-level views and common comparisons.
- Simplify map geometry at multiple zoom levels.
- Load only the selected region where possible.
- Cache immutable tables and expensive transforms using keys that include the bundle version.
- Keep the default app functional within the memory and CPU limits of the public host.
- Move heavy spatial joins, training, and batch inference out of request-time execution.

Set measurable budgets after the prototype: for example, a useful first view within several seconds on a cold start and sub-second updates for cached controls.

## Visualization rules

- Use the same units, baselines, and color meaning across views.
- Pair maps with values or distributions; maps alone make comparison difficult.
- Use diverging scales only when there is a meaningful midpoint.
- Avoid a red-to-green good/bad neighborhood scale.
- Show uncertainty as a first-class visual element.
- State whether values are nominal, real, per capita, rates, or indexes.
- Include accessible contrast, keyboard navigation, descriptive labels, and text alternatives for central findings.

## Scenario interaction rules

Each adjustable variable needs a definition, valid range, observed local range, transformation rule, and warning about interpretation. Linked variables should either update together using an explicit rule or be blocked when a combination falls outside training support. The interface should surface an out-of-distribution warning when a scenario is far from observed examples.

## Failure and empty states

Design explicit states for missing sources, unsupported tracts, stale bundles, unavailable horizons, failed inference, and low-confidence output. A blank chart or silent fallback is not acceptable. Where possible, retain the historical profile even if a forecast is withheld.

## Testing

- unit tests for formatters, input validation, and data access;
- contract tests against a small fixture bundle;
- smoke tests for every page and primary user flow;
- visual review at common desktop and mobile widths;
- accessibility checks for contrast, labels, focus order, and keyboard use;
- a manual review confirming that caveats remain visible in screenshots and demonstrations.

## Required outputs

- wireframe or page inventory tied to user questions;
- serving-bundle loader with schema validation;
- reusable map, trend, interval, comparison, and explanation components;
- scenario controls with guardrails;
- methods and limitations page;
- smoke-test checklist and deployment-ready entry point.

## Exit criteria

This stage is complete when a new user can select a supported community, understand what is observed versus modeled, follow the evidence behind a forecast, compare analogues, run a guarded scenario, and find the project limitations without reading the source code.
