# 14. Capstone Delivery and Handoff

The final stage packages the technical work into evidence that another student, reviewer, or employer can understand and reproduce. The strongest submission should tell one consistent story across the repository, application, report, and presentation.

## Stage objective

Freeze a defensible project release, complete the course deliverables, and leave enough operational context that the work can continue after the capstone.

## Final narrative

The project story should stay centered on a clear question: can a longitudinal, multidimensional representation of neighborhoods provide useful and honest context about housing trajectories beyond a standard price-prediction dashboard?

The report should connect:

1. the real user question and limits of the term Digital Twin;
2. public-data integration and the neighborhood state representation;
3. forecast, analogue, and scenario methods;
4. time- and geography-aware evaluation;
5. what worked, what did not, and why;
6. how the application turns the analysis into an inspectable experience;
7. responsible-use boundaries and future work.

## Required project artifacts

- public repository with clear setup and contribution guidance;
- reproducible data and modeling pipeline or a documented reduced-data path;
- source registry and data dictionary;
- exploratory analysis with decisions, not just charts;
- versioned experiment results and baseline comparisons;
- model card, ethics and limitations document, and leakage audit;
- public or readily reviewable application;
- final report, presentation materials, and demonstration;
- statement of work showing team ownership if applicable;
- feedback log showing how instructor or peer feedback changed the project.

Confirm the current course checklist before release and add any format, length, disclosure, poster, gallery, or video requirements that are not already represented here.

## Course requirement crosswalk

This table is the working index from course expectations to project evidence. Update links as deliverables are created instead of collecting them during the final week.

| Requirement | Planned evidence |
|---|---|
| Git repository and README with run instructions | Root README, charter, contribution guide, and tagged release |
| Dependency file containing only required libraries | `pyproject.toml`, release lock file, and clean-environment installation check |
| Code generates results and figures | Versioned pipeline, scripts, and report artifacts without manual spreadsheet steps |
| Clean code, relative paths, and no keys | Package structure, tests, configuration, `.env.example`, and secret scan |
| Accessible, legally usable data | Data-source policy, access and terms review, and source manifests |
| Inline attribution for copied or adapted code | Source-link comments beside reused code, license review, and required notices |
| Clear project statement | `PROJECT_CHARTER.md` and final report introduction |
| Methodology and evaluation | Numbered implementation guides, experiment records, and final scorecards |
| Technical depth | Data engineering, spatial analysis, supervised ML, uncertainty, analogues, scenarios, visualization, and deployment |
| Translation for nontechnical users | Interactive application, methods page, model card, and neighborhood case study |
| Broader impacts and ethics | Ethics and limitations document plus error and coverage slices |
| At least three original visuals | Code-generated report figures selected from EDA, evaluation, maps, calibration, or analogue results |
| At least three relevant references | Prior-work response and cited methodology or comparison sources |
| Concise final report | Target fewer than 3,000 words unless the current course instruction changes |
| Statement of work | Named team ownership, contributions, and review responsibilities |
| Mentor or reviewer feedback | `docs/reference/feedback_log.md` with action or rationale |
| Demonstration artifact | Three-to-five-minute video or the currently permitted poster format |
| Required assistance disclosure | Course-compliant appendix and code-level notices, without contributor attribution |
| Gallery post | Public summary, visuals, repository, and application links |

## Reproducibility package

A reviewer should be able to:

1. create the supported environment;
2. run fast tests without downloading the full dataset;
3. inspect source definitions and data contracts;
4. reproduce at least one small end-to-end example;
5. understand how the full release bundle was produced;
6. match application output to an experiment and commit.

If full public-data refreshes are too slow for review, provide a small legally redistributable fixture and exact instructions for the full process. Never substitute an undocumented prepared file for a reproducible path.

Freeze a dependency lock file for the final environment. Keep `pyproject.toml` limited to libraries actually used by project code or required development commands.

## Final report outline

- Problem and intended users
- Prior work and project contribution
- Data, geography, and time coverage
- Pipeline and state representation
- Modeling and baselines
- Evaluation design
- Results and error analysis
- Application and scenario interpretation
- Responsible use and limitations
- Lessons, future work, and contribution statement

Keep implementation detail proportional to its importance. Put exhaustive schemas, configuration, and supplementary results in repository documentation so the report can focus on decisions and evidence.

## Presentation and demonstration

Plan a short, reliable path through the product:

1. choose a community with complete data;
2. show its historical state and metro context;
3. inspect a forecast and uncertainty range;
4. compare one or two historical analogues;
5. change one scenario input and explain the non-causal interpretation;
6. show one evaluation result and one honest limitation.

Prepare a recorded or static fallback using the same released bundle in case the public host is unavailable. Avoid a live pipeline refresh during the demonstration.

## Team handoff

For a team, each major workstream should have a primary owner and reviewer, but no component should be understood by only one person. Capture setup, recurring commands, data refresh, model training, bundle publishing, deployment, and rollback in short runbooks. Close or triage open issues before the release.

## Release checklist

- [ ] Scope matches `PROJECT_CHARTER.md`, or changes are recorded.
- [ ] Final data and model versions are frozen.
- [ ] Evaluation runs use untouched temporal and geographic test sets.
- [ ] Application numbers match the released bundle.
- [ ] Source, license, privacy, and attribution review is complete.
- [ ] Secrets, raw restricted data, and personal paths are absent from Git.
- [ ] Tests and link checks pass from a clean checkout.
- [ ] Model card and limitations match the final behavior.
- [ ] Public links work in a signed-out browser.
- [ ] Demo fallback and rollback path are ready.
- [ ] Team contribution and required assistance disclosures are complete.
- [ ] Release is tagged and the changelog or release notes explain it.

## Exit criteria

The project is ready for delivery when every central claim is tied to reproducible evidence, the application and report use the same released outputs, another person can follow the setup and methods, and known limitations are visible rather than buried.
