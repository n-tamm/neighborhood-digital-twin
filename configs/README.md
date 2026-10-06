# Configuration

Configuration files describe choices that should be reviewable without editing Python: enabled sources, selected features, forecast horizons, split dates, experiment settings, scenario bounds, and serving-bundle scope.

Configuration is versioned with the code that interprets it. A run records the configuration hash so a result can be tied back to the exact choices that produced it.

Planned files:

- `sources.yml`: approved source endpoints, grains, vintages, and acquisition options;
- `features.yml`: feature families, units, transformations, timing, and inclusion status;
- `experiments.yml`: split definitions, baselines, candidate model, seeds, and metrics;
- `scenarios.yml`: permitted scenario variables, units, bounds, and support rules;
- `app.yml`: demonstration regions, bundle version, and display defaults.

Examples are templates, not final decisions. Secrets never belong in these files.
