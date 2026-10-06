# Responsible Use, Ethics, and Limitations

Neighborhood data is not neutral. Measurements reflect government definitions, survey design, reporting practices, market access, policy, and a long history of unequal investment. This document defines the project's initial boundaries and should be updated when actual data and model results reveal new risks.

## Intended contribution

The project is intended to help users understand how tract-level housing, demographic, economic, and spatial indicators have changed; examine transparent forecasts with uncertainty; compare historical analogues; and explore bounded model sensitivity. It provides context for inquiry, not a decision or verdict about a place.

## Prohibited and unsupported uses

The system should not be used to:

- screen tenants, borrowers, insurance applicants, or job candidates;
- automate lending, insurance, appraisal, policing, or resource-allocation decisions;
- identify the “best” or “worst” neighborhoods through one composite score;
- target or exclude people based on protected characteristics or proxies;
- provide individual financial, legal, real-estate, or safety advice;
- claim that changing a scenario input will cause the displayed outcome;
- infer an individual's traits from neighborhood aggregates.

## Main limitations

### Geographic units are imperfect

Census tracts are statistical areas, not necessarily the neighborhoods people recognize. Boundaries change, experiences vary within a tract, and results can change with geographic aggregation. Crosswalks reduce but do not eliminate this problem.

### Public estimates contain uncertainty and delay

ACS estimates have margins of error, many sources are released well after their reference period, and administrative coverage can differ by place. A recent-looking application may still depend on older observations.

### Housing measures are incomplete

Repeat-sales indexes, transaction prices, rents, permits, and assessed values describe different parts of a market. No one source fully represents housing quality, informal arrangements, displacement, or the lived cost of remaining in a community.

### Prediction is not causation

Forecasts learn associations present in historical data. Scenario outputs show how the fitted model responds to controlled input changes; they do not estimate the effect of a policy, development, or household decision without a separate causal design.

### Historical patterns can encode inequity

Past housing and lending outcomes reflect segregation, redlining, exclusionary zoning, disinvestment, and unequal access to credit. Predictive success can reproduce those patterns. Demographic features must have a stated analytical purpose, and performance should be examined across community contexts.

### Shocks and local knowledge matter

Interest-rate shifts, disasters, plant closures, major developments, policy changes, and data revisions can make historical relationships unreliable. Local conditions not captured by national public data may dominate the outcome.

## Product safeguards

- Use descriptive labels rather than good/bad or desirable/undesirable categories.
- Show the data-through date, uncertainty, coverage, and quality flags with results.
- Separate observed, estimated, forecast, and scenario values visually and in text.
- Suppress outputs that fail minimum coverage or model-support rules.
- Keep protected-class context available for equity analysis without turning it into a neighborhood score.
- Explain analogue similarity and show a range of subsequent outcomes.
- Provide direct links to methodology, sources, and the model card.
- Collect no personally identifiable information for the core product.

## Review questions before release

- Who could be helped or harmed by this view?
- Does the map or wording invite a ranking that the analysis does not support?
- Are uncertainty and missingness as visible as the central prediction?
- Are error and interval coverage materially different across community contexts?
- Could a demographic variable or close proxy be removed without weakening the research purpose?
- Would a user reasonably mistake sensitivity for causality?
- Is any data license, aggregation level, or small-cell output inconsistent with public release?
- Can a person challenge or understand the basis of the displayed result?

## Open issues log

| Date | Issue | Evidence | Decision | Owner | Revisit by |
|---|---|---|---|---|---|
| TBD | Define minimum coverage and suppression rules | Pending discovery and EDA | Open | TBD | Before application release |

