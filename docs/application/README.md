# Application Documentation

This folder documents the application that is implemented now: current profiles, observed FHFA
history, a quality-gated one-year forecast, historical analogues, maps, and explicit unavailable
states. Scenario analysis and an AI question layer are not implemented and are not described as
current product features.

Read the files in this order:

1. [Neighborhood explorer](neighborhood_explorer.md) explains the user flow and what each screen
   communicates.
2. [Data access and contracts](data_access_and_contracts.md) explains the live and local data
   boundaries, release-selection rules, and table usage.
3. [Charts and interpretation](charts_and_interpretation.md) explains each implemented visual and
   the claims it can and cannot support.
4. [Deployment and testing](deployment_and_testing.md) gives the local and Databricks run sequence,
   current access model, tests, and failure checks.

The source entry point is [`app/streamlit_app.py`](../../app/streamlit_app.py). Broader planned
capabilities remain in
[implementation stage 11](../implementation/11_application_and_visualization.md).
