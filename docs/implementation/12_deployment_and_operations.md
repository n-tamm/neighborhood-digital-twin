# 12. Deployment and Operations

Deployment should make the work easy to inspect while keeping the analytical pipeline reproducible. The recommended first architecture separates public application hosting from batch research and model development so free-tier limitations do not dictate the project design.

## Recommended deployment shape

Use three connected environments:

1. **GitHub** is the source of truth for code, documentation, reviews, releases, and automated checks.
2. **Databricks Free Edition** is an optional shared batch environment for exploration, feature construction, model training, and serving-bundle generation.
3. **Streamlit Community Cloud** is the preferred public application host for the capstone demonstration. A small GitHub Pages site can provide static project documentation and a durable landing page.

Databricks Free Edition is useful for collaborative learning but currently has quotas, restricted outbound access, serverless-only compute, and no service-level agreement. Databricks Apps also require authenticated workspace access, so they should be treated as a team preview option rather than the only public demo. Verify these conditions again before the final deployment because free offerings change.

## Environment strategy

| Environment | Purpose | Data | Deployment expectation |
|---|---|---|---|
| Local development | Fast iteration and tests | Small samples or cached public data | Reproducible from documented setup |
| Databricks | Optional heavy pipeline and model runs | Versioned tables and artifacts | Manual or scheduled batch runs within free limits |
| CI | Linting, unit tests, contract tests | Tiny committed fixtures only | Runs on pull requests and protected branches |
| Preview app | Team review of release candidates | Candidate serving bundle | May be private or temporary |
| Public app | Capstone demonstration | Approved, compact serving bundle | Stable URL with no secrets in the client |

Development and production should use the same package functions and contracts. Notebook-only logic should not be required to reproduce a released bundle.

## Build and release flow

```mermaid
flowchart LR
    A[Feature branch] --> B[Automated checks]
    B --> C[Reviewed merge]
    C --> D[Versioned pipeline run]
    D --> E[Evaluation gate]
    E --> F[Serving bundle]
    F --> G[Bundle validation]
    G --> H[Preview deployment]
    H --> I[Release tag]
    I --> J[Public application]
```

The serving bundle should be immutable and identified by a release ID. Code, configuration, raw-source versions, feature schema, model version, and evaluation summary should all be traceable from its manifest.

## Continuous integration

Initial checks should include:

- package installation on the supported Python version;
- linting and formatting validation;
- unit and contract tests;
- import and configuration smoke tests;
- Markdown-link checks when practical;
- detection of accidentally committed secrets or large data files.

Later, add a small application smoke test and a build check for the public host. Heavy training and full data refreshes should not run on every pull request.

## Continuous delivery

Streamlit Community Cloud can deploy directly from a GitHub branch and update when that branch changes. For the capstone, point production at a stable release branch or tag-derived branch rather than an individual feature branch. Use a preview deployment for UI review if the hosting limits allow it.

GitHub Pages is appropriate for static documentation, project findings, and a fallback landing page; it cannot run the Python application. Keep a clear link between the landing page, live app, repository, data sources, and model card.

## Secrets and configuration

- Commit `.env.example`, never `.env` or credentials.
- Store host secrets in the deployment platform's secret manager.
- Give credentials the narrowest practical permissions.
- Prefer public download URLs and cached snapshots over long-lived personal tokens.
- Do not print secrets in notebook output or CI logs.
- Validate required settings at startup and fail with a useful message.

## Data and artifact publishing

Do not place unrestricted raw extracts or large model artifacts in ordinary Git history. Publish only data that its license permits, and record checksums and source metadata. Small fixtures, aggregated application tables, or release artifacts can use GitHub Releases, object storage, or another documented public location depending on size and terms.

Every bundle release should contain or reference:

- release and schema versions;
- creation timestamp and pipeline commit;
- geography vintage and observation cutoff;
- source snapshot identifiers;
- model and feature versions;
- validation results and known exclusions;
- checksums for included files.

## Reliability and observability

For a capstone, observability can remain lightweight but should still answer whether the application starts, which bundle it serves, and where it fails. Log startup, bundle validation, page-level exceptions, and coarse performance timing without recording user-entered locations or other unnecessary interaction detail.

Add a visible status block containing the model version, data-through date, and last successful release. A simple scheduled health check is optional; the project should not promise high availability on a free service.

## Rollback and recovery

Keep at least one previously validated serving bundle and deployment revision. Rollback should mean selecting the prior known-good bundle and application release, not rerunning the entire pipeline under pressure. Document bundle publication, deployment, rollback, and source-refresh recovery in `docs/runbooks/`.

## Current platform references

- [Streamlit Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit Community Cloud app management and limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
- [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- [Databricks Apps authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions)
- [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [GitHub Actions guide for Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)

## Required outputs

- tested environment setup and dependency lock strategy;
- CI checks for the current codebase;
- validated serving-bundle release process;
- public deployment with source and methodology links;
- deployment and rollback runbooks;
- documented free-tier constraints and fallback demo plan.

## Exit criteria

This stage is complete when a clean environment can test the repository, a validated bundle can be promoted without manual file editing, the public app identifies exactly what it serves, and the team can restore the prior release if a deployment fails.

