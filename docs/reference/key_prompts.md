# Key Prompt Log

This is a selective record of AI prompts that materially shaped the project, resolved a significant error, or led to an important design decision. It is not a transcript of routine editing, formatting, or minor debugging. New entries should be added only when omitting the prompt would make an important project decision harder to understand or reproduce.

Prompt text below is limited to the material instruction. Surrounding conversation is omitted when it did not affect the decision. Secrets, personal data, credentials, and private source content must never be copied here.

## KP-001: Preserve the analytical focus and interactive end product

- **Date:** 2026-10-06
- **Model:** GPT-5
- **Why retained:** This established the project's central balance between rigorous data science and a usable public application.
- **Material prompt excerpt:** “The MOST important aspects that I would want to preserve and focus on are the Data science aspects, but the end results should be a interactive application for the Neighborhood Digital twin.”
- **Resulting decision:** The project centers on longitudinal data engineering, forecasting, calibrated uncertainty, spatial context, historical analogues, and scenario sensitivity. The map-driven application is the delivery layer for those results rather than a substitute for the research.
- **Main artifacts:** `PROJECT_CHARTER.md`, `README.md`, and `docs/architecture/system_architecture.md`.

## KP-002: Require accessible, legally usable data

- **Date:** 2026-10-06
- **Model:** GPT-5
- **Why retained:** This ruled out sources that could make the capstone impossible to share, reproduce, or review.
- **Material prompt excerpt:** “All team members must be able to access the data... Faculty are not allowed to sign data usage agreements or non-disclosure agreements... Your project respects any licenses or usage agreements attached to your dataset... we cannot support projects that require a new IRB approval.”
- **Resulting decision:** Every source must pass an access, licensing, timing, geographic, and privacy review before entering the main pipeline. The core design uses aggregate public data and excludes personally identifiable, biomedical, NDA-controlled, and paid proprietary sources.
- **Main artifacts:** `DATA_SOURCES.md` and `docs/implementation/01_data_discovery_and_feasibility.md`.

## KP-003: Build a flexible production-minded repository and implementation plan

- **Date:** 2026-10-06
- **Model:** GPT-5
- **Why retained:** This prompt led to the initial repository architecture and the sequenced technical plan that future development will follow.
- **Material prompt excerpt:** “I’d like now is a good organization put into place in the repo (folders, files, etc) with a robust production grade format that will give us flexability for how we add content/procedures/etc and be well organized for the best deployment possible... add initial and robust technical implimintation documentation about each stage of the project... including the data gathering, modeling, analysis, evaluation, application, deployment, integrations, and well every deliverable needed to product the final product.”
- **Resulting decision:** The repository separates source code, application code, data zones, manifests, configurations, artifacts, reports, infrastructure, tests, and documentation. Technical work is organized as a dependency-aware guide from feasibility through capstone delivery, with explicit contracts between stages.
- **Main artifacts:** `docs/architecture/repository_structure.md`, `docs/implementation/`, and the top-level folder READMEs.

## KP-004: Make AI use and prompt retention explicit but selective

- **Date:** 2026-10-06
- **Model:** GPT-5
- **Why retained:** This set the project's disclosure and prompt-governance rules.
- **Material prompt excerpt:** “Make sure the AI use disclaimer is added in the README... include documentation that tracks key prompts. The prompts that are saved should only be those that were instrumental in creating the project, fixing significant errors, or leading to vital decision points in the project.”
- **Resulting decision:** The README contains the required assistance disclosure. Code and notebooks receive the required file-level notice, while this document records only consequential prompts and their effects.
- **Main artifacts:** `README.md`, this log, and the local `AGENTS.md` workflow rules.

## Entry criteria

Add a prompt only when at least one condition is true:

- it established or materially changed project scope, methodology, architecture, evaluation, responsible-use boundaries, or deployment;
- it led to the resolution of a significant defect whose cause or fix would otherwise be difficult to reconstruct;
- it generated a central implementation that was retained after author review;
- it was used to make a consequential decision between credible alternatives.

Do not add prompts for copyediting, formatting, routine code completion, simple test repairs, status checks, or changes that are already obvious from a small diff.

## New entry template

```text
## KP-NNN: Short decision title

- Date:
- Model:
- Why retained:
- Material prompt excerpt:
- Resulting decision or fix:
- Main artifacts:
```
