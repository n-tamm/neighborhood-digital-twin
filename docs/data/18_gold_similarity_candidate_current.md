# `gold_similarity_candidate_current`

[Back to the data documentation index](README.md)

- **Layer:** Gold current products
- **Databricks table:** `workspace.neighborhood_twin_dev.gold_similarity_candidate_current`
- **Sample:** [gold_similarity_candidate_current.jsonl](../../data/samples/gold_similarity_candidate_current.jsonl)

- **Grain and key:** one row per candidate 2020 tract GEOID.
- **Purpose:** offers a reproducible starting cohort for similarity experiments. A tract must have
  current ACS coverage, positive population and housing-unit estimates, and at least eight of the
  twelve governed similarity inputs.
- **Caution:** this is an availability screen, not a declaration that the eventual feature set or
  matching method is valid. Those choices still require modeling and evaluation.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.
