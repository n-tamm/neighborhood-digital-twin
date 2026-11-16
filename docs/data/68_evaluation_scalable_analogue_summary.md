# `scalable_analogue_summary`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.scalable_analogue_summary`
- **Sample:** [scalable_analogue_summary.jsonl](../../data/samples/scalable_analogue_summary.jsonl)
- **Grain and key:** one horizon and exact or approximate retrieval configuration.
- **Purpose:** provides the configuration-level comparison used to decide whether an LSH
  shortlist offers enough fidelity and runtime benefit for later production retrieval.

The exact-reference rows report perfect fidelity by definition and provide measured exhaustive
runtime. Approximate rows summarize complete-result share, recall, rank behavior, outcome drift,
shortlist size, and retrieval time. Runtime from one development run should be interpreted with
fidelity and repeated operational evidence rather than as a universal latency guarantee.

Community recall and tract-year-state recall are separate. Recovering the same physical tract at
a different historical origin year can change the later outcome even when community overlap is
perfect.

The eight-row validated summary supports rejecting the tested LSH approach for serving. It
shortlists 88.7% to 99.9% of all possible query-candidate pairs and takes roughly three to five
times as long as the cached exact-reference segment in the same run.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.
