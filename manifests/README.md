# Manifests

Manifests make data and model builds traceable. They describe what was read, when it was retrieved, what code and configuration produced an output, and how to verify that the same bytes are being used.

Expected manifest types:

- source snapshot manifests;
- schema fingerprints and data-contract versions;
- feature-table build manifests;
- model and calibration manifests;
- application serving-bundle manifests.

Manifests are small and should normally be committed. They must not include API keys, tokens, private filesystem paths, or restricted data. Paths should be relative or logical storage identifiers.
