# Contracts

Contracts describe the tables and interfaces shared between workstreams. They should include grain, keys, required fields, units, nullability, lineage, quality checks, and compatibility rules.

Initial cross-workstream contracts:

- [Neighborhood state](neighborhood_state.md): the central tract-year representation;
- [Application serving bundle](serving_bundle.md): the immutable boundary between batch analysis and the UI.

Additional contracts to add when their implementations begin include:

- source snapshot manifest;
- silver FHFA, ACS, geography, and macro tables;
- forecast targets and split assignments;
- predictions and calibrated intervals;
- historical analogues;
- scenario definitions and outputs;

Start with a human-readable Markdown contract. Add JSON Schema, Pydantic models, Pandera, Spark schemas, or another machine-readable form when the corresponding pipeline is implemented. The machine check and the written definition must agree.
