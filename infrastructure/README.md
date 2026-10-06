# Infrastructure and Deployment

This folder will hold platform configuration needed to run the project outside a developer's laptop: Databricks bundle definitions, documentation publishing, and Streamlit deployment settings. GitHub Actions workflows live in `.github/workflows/`, where GitHub expects them.

Infrastructure files should be added only when they are executable and tested. Placeholder cloud resources create confusion, so the current architecture is documented in `docs/implementation/12_deployment_and_operations.md` until each deployment component is implemented.

The intended split is:

- Databricks for batch ETL, Delta tables, larger experiments, and MLflow;
- GitHub for source, review, CI, releases, and documentation;
- Streamlit Community Cloud for the public interactive application;
- GitHub Pages for documentation and a static fallback.

Never commit access tokens, populated secrets files, workspace exports containing credentials, or state files with sensitive values.
