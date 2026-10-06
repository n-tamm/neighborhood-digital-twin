# Documentation

The documentation is split by purpose so planning, implementation details, and final reference material do not blur together.

## Start here

1. [Project charter](../PROJECT_CHARTER.md) — what the project is and is not.
2. [Roadmap](../ROADMAP.md) — when each capability is expected.
3. [System architecture](architecture/system_architecture.md) — how data and results move through the system.
4. [Implementation guide](implementation/README.md) — the ordered technical build plan.
5. [Repository structure](architecture/repository_structure.md) — where work belongs and why.

## Documentation areas

### `implementation/`

Numbered guides for data discovery, acquisition, geography, exploration, features, modeling, uncertainty, analogues, scenarios, evaluation, application development, deployment, integrations, and final delivery. These are living build instructions rather than retrospective reports.

### `architecture/`

Stable descriptions of system boundaries, data flow, contracts, and repository organization. Update these when the system changes, not for every implementation detail.

### `contracts/`

Human-readable specifications for important tables and interfaces. Machine-readable schemas can live beside them once implemented.

### `decisions/`

Short architecture decision records for choices that would otherwise be lost: canonical geography, target timing, model selection, scenario design, and deployment changes.

### `reference/`

Documents that become authoritative as the project matures, such as the data dictionary, model card, glossary, ethics statement, and source citations.

### `runbooks/`

Operational instructions for repeatable tasks: rebuilding data, publishing a serving bundle, deploying the app, responding to a failed job, and reproducing a release.

## Writing and maintenance rules

- Describe current behavior separately from planned behavior.
- Link to code or contracts instead of copying implementation details into several files.
- Record unresolved decisions explicitly; do not disguise them as settled design.
- Keep commands executable and update them when interfaces change.
- Include assumptions, failure modes, and validation evidence—not only the happy path.
- Prefer one authoritative document and links over duplicate versions with unclear status.

The short final capstone report will draw from these documents but should not reproduce all of them. Engineering detail belongs here so the report can stay focused on the question, evidence, results, and limitations.
