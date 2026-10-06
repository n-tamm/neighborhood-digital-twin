# GitHub Project Configuration

This folder holds repository automation and collaboration templates that GitHub reads directly. Workflows belong in `workflows/`; pull-request and future issue templates belong at this level or in `ISSUE_TEMPLATE/`.

Keep cloud deployment definitions that are not GitHub-specific in `infrastructure/`. Never place credentials in a workflow file. Use repository or environment secrets and request only the permissions a job needs.

The initial CI workflow deliberately runs fast checks only. Full data ingestion, spatial processing, model training, and release-bundle publication require separate workflows with explicit data access and approval gates.

