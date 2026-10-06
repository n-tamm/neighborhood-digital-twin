# Key Prompt Log

This log is intentionally sparse. It preserves only unusually strong, self-contained prompts that directly shaped the project's central research or product design and are useful enough to revisit later. Most prompts do not belong here, even when they led to a repository change.

## KP-001: Define the data-science-centered Neighborhood Digital Twin

- **Date:** 2026-10-06
- **Model:** GPT-5
- **Why this qualifies:** This prompt defines the analytical focus, user experience, scope boundaries, possible extensions, and intended audiences in one place. It remains useful when deciding whether later features belong in the project.
- **Resulting decisions:** Data science remains the center of the capstone; the main product is a map-driven interactive application; forecasts include uncertainty; historical analogues connect recommendation and prediction; scenarios are sensitivity analyses rather than causal estimates; AI remains optional and grounded in project outputs.
- **Main artifacts:** `PROJECT_CHARTER.md`, `ROADMAP.md`, `README.md`, and the technical implementation guide.

### Prompt

> Just so you know the MOST important aspects that I would want to preserve and focus on are the Data science aspects, but the end results should be a interactive application for the Neighborhood Digital twin. I don't like the name you gave it and here is my slack post in case it helps you:
>
> Hi everyone, I’ve been working through ideas for the data science capstone and wanted to propose the idea of building a Neighborhood Housing Intelligence / Digital Twin platform using public U.S. data.
>
> The general idea would be to combine housing, demographic, economic, geographic, development, environmental, and any other potentially relevant data to build a longitudinal representation of communities and how they change over time. House price prediction models are pretty common, so the goal would be a more holistic and interactive application where someone can select a community and explore where it has been, what it looks like today, what trajectory it appears to be following, and what plausible future states might look like.
>
> There are several data science specific directions that seem feasible. One would be forecasting housing-market trajectories over 1, 3, and 5 year horizons, ideally with uncertainty ranges rather than just point predictions. Another would be creating multidimensional representations or embeddings of communities so the system could answer questions like “What communities historically looked most like this one today, and what happened to them afterward?” Sort of a combination of recommendation and prediction applications. Clustering could also identify different types of community trajectories, while spatial modeling could capture the influence of neighboring areas and broader metro conditions.
>
> The Digital Twin application piece is probably what I’m most interested in as the centerpiece of the application. A user could select an area, see its current modeled state, and then explore scenarios involving any potentially viable data influencing a community's trajectory. The application could show how the model’s expected distribution of outcomes changes under those scenarios, while being careful to frame these as model sensitivity/scenario analysis rather than causal claims. One of the main challenges here would be finding enough, but also not too many features, as data could be as narrow as just development information or as broad as all housing, public health, environmental, consumer, business, political, or other data available.
>
> I also think there are some interesting ways this could connect to real decisions without making the project exclusively about investment. For a prospective home purchaser/consumer, it could provide context around affordability, historical analogues, downside uncertainty, housing supply/demand, and expected community trajectory. For existing residents and communities, it could show affordability pressure, demographic/economic change, housing availability, and development patterns. For planners or developers, it could help explore supply/demand conditions, construction, growth, and areas undergoing significant transitions.
>
> Ideally the end result might be some interactive UI for the Digital Twin that would ideally be map-driven: select a Census tract/community, explore historical trends and forecasts, compare areas, view similar historical communities, inspect model drivers, and enter the Digital Twin/scenario environment. If scope allows, there could also be an AI layer that lets someone ask questions naturally—e.g. “Why is the model showing more downside uncertainty here?” or “Find communities similar to this one but with better affordability.” The AI would query the actual analytical models/data rather than being the source of the analysis itself.
>
> From the capstone perspective, I like the idea because it potentially touches a lot of areas while still contributing to one cohesive end product: data engineering and public-data integration, geospatial analytics, supervised ML, forecasting, uncertainty estimation, clustering/embeddings, spatial modeling, visualization, simulation, explainability, AI/RAG, APIs, application deployment, and MLOps.
>
> The scope is definitely much larger than what all needs to be implemented, so part of the project would be determining which pieces produce the strongest final application. The core would likely be the public-data pipeline + neighborhood model + forecasting + interactive UI with great visualizations, with historical information, Digital Twin simulation, and AI functionality added where feasible.
>
> If anyone likes the subject or the idea about the application but with other subjects, just let me know as I'm open to other ideas as well. Also, in case it helps coordinate anything, I'm based in Michigan, so Eastern time zone for me.

## Admission standard

A future prompt belongs here only when all of these are true:

1. It is unusually thoughtful, substantive, and mostly self-contained.
2. It directly shapes a central research question, methodology, architecture, product direction, or resolution of a major technical failure.
3. Its influence persists across several parts of the project rather than one small edit.
4. Rereading the original prompt later would provide more value than reading the resulting documentation or Git diff alone.

Do not record routine implementation requests, repository housekeeping, writing edits, course rules, disclosure instructions, status questions, ordinary debugging, or prompts whose effect is already obvious from a small change. When uncertain, leave the prompt out. The expected final log is only a handful of entries across the entire project.
