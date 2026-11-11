# `scalable_analogue_summary`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.scalable_analogue_summary`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one horizon and exact or approximate retrieval configuration.
- **Purpose:** provides the configuration-level comparison used to decide whether an LSH
  shortlist offers enough fidelity and runtime benefit for later production retrieval.

The exact-reference rows report perfect fidelity by definition and provide measured exhaustive
runtime. Approximate rows summarize complete-result share, recall, rank behavior, outcome drift,
shortlist size, and retrieval time. Runtime from one development run should be interpreted with
fidelity and repeated operational evidence rather than as a universal latency guarantee.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.
