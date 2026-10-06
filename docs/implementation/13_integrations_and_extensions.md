# 13. Integrations and Extensions

This project can grow in many directions, but optional work should enter through stable interfaces rather than enlarge the core until it becomes impossible to finish. Extensions belong here only after the baseline pipeline, forecast, evaluation, and application path work end to end.

## Stage objective

Define how new data, models, services, and user experiences can be added without breaking reproducibility or changing the project's claims by accident.

## Extension admission test

Before adding an integration, answer:

1. Which user or research question does it improve?
2. Is the data or service accessible to every team member under acceptable terms?
3. Does it add information available at prediction time?
4. What baseline or ablation will show whether it helped?
5. What new maintenance, privacy, cost, or deployment risk does it create?
6. Can the core application still work when it is unavailable?

An exciting source that cannot pass these questions should remain a documented future direction.

## New data-source integration

Each source should implement the same conceptual path: acquire, preserve raw snapshot, validate, standardize geography and time, publish a curated table, and register lineage. Add a source manifest, data dictionary fields, quality rules, license notes, expected refresh cadence, and a small fixture before using it in features.

Promising staged sources include building permits, transit access, business openings and closures, environmental exposure, climate risk, local land-use changes, mortgage conditions, and public-health aggregates. Availability and comparability vary substantially across cities, so local sources should not quietly become requirements for a national model.

## Natural-language interface

An AI layer can help users navigate the application or ask questions such as why an interval is wide. It should retrieve values, explanations, and citations from approved analytical outputs; it should not invent forecasts or replace the models.

A safe initial design would:

- translate a question into a limited set of read-only application functions;
- return structured results from the serving bundle;
- generate an explanation grounded in those results;
- show the underlying values and source links;
- refuse unsupported causal, personal, or prescriptive requests;
- function as an optional feature so the core application is still complete without it.

Do not send sensitive data, unpublished credentials, or unrestricted source extracts to an external model provider. Record provider, model, prompt version, cost limits, and evaluation if this layer is implemented.

## Programmatic API

If another interface needs the results, add a small read-only API over the serving contract. Version endpoints, validate tract IDs and dates, return model and bundle metadata with each response, and rate-limit expensive calls. Avoid deploying an API merely to separate Python files; it is justified when there is a real second consumer.

## Spatial database

Flat columnar files are likely enough for the MVP. PostGIS, a cloud warehouse, or a geospatial catalog becomes useful when the project needs frequent spatial queries, multi-user updates, larger coverage, or multiple applications. Migration should preserve the same curated-table and serving-bundle contracts.

## Learned representations

The first analogue model should use standardized, interpretable features. Autoencoders, contrastive learning, graph embeddings, or sequence representations can be tested later against that baseline. An extension is useful if it improves held-out retrieval, stability, or downstream prediction and if the resulting similarity can still be explained.

## National expansion

Expansion should happen by adding metros or states through the same pipeline, not by weakening validation to accept inconsistent data. Track coverage explicitly and distinguish nationally comparable sources from local enhancements. Consider regional models or partial pooling when one national relationship does not fit every housing market.

## Feature flags and graceful degradation

Optional capabilities should be controlled through configuration. The application should hide an unavailable integration cleanly and preserve the core historical and forecast experience. Never catch an integration failure and display stale or fabricated output without a warning.

## Extension proposal template

For each proposed addition, record:

- owner and decision date;
- user question;
- interface and dependencies;
- data/license review;
- experiment and success metric;
- operational cost;
- responsible-use concerns;
- fallback behavior;
- decision: adopt, revise, defer, or reject.

Material architecture decisions should also receive an ADR in `docs/decisions/`.

## Exit criteria

This stage is complete for a chosen extension when it uses a documented interface, can be disabled without breaking the core product, has its own validation evidence, and adds measurable value relative to the simpler system.

