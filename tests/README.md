# Tests

Tests are organized by the kind of failure they are meant to catch:

- `unit/`: deterministic behavior of small functions;
- `data_contracts/`: schema, grain, types, ranges, and required lineage fields;
- `integration/`: small end-to-end paths using committed fixtures;
- `regression/`: approved outputs whose unexpected change needs review;
- `app/`: serving-bundle and application-start smoke tests;
- `fixtures/`: small, documented, redistributable samples.

The national pipeline does not run in CI. CI uses small fixtures that preserve difficult cases such as missing HPI years, tract splits, high ACS margins of error, and unsupported scenarios. Larger validation runs belong in Databricks or a documented local process.
