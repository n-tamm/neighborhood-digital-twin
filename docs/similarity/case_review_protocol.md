# Historical Analogue Case Review Protocol

## Purpose

Distance alone cannot establish that two communities are meaningfully similar. This review asks
whether the current matches are understandable in the features used by the model, whether any
important difference is being hidden by the overall distance, and whether the result would be
responsible to show in the application.

The review is a model-development activity. It does not label a community as good, bad,
improving, or declining, and it does not treat later FHFA performance as a causal consequence of
the matched characteristics.

## Case selection

Cases are selected in code rather than chosen from attractive examples. The representative set
contains one deterministic query for every available combination of:

- one- or three-year horizon;
- Census region; and
- geographic-development or held-out-state role.

The diagnostic set adds up to two queries per horizon with the lowest standardized-versus-PCA
overlap and up to two with the largest mean match distance. Any query whose top ten repeats a
physical candidate tract at multiple years is also included. A case can carry more than one
selection reason.

The query's later outcome is not used to select representative or diagnostic cases. This prevents
the casebook from being built around unusually successful or unsuccessful outcomes.

## Evidence shown for each case

Each reviewed match retains:

- query and candidate tract, location, and year;
- representation, rank, and distance;
- candidate age and later observed FHFA outcome;
- the governed feature order;
- query and candidate feature arrays after the historical transformations;
- absolute standardized differences for all twelve features;
- mean standardized gap for each of the five feature families;
- the closest feature and largest feature difference; and
- model, schema, and run lineage.

These diagnostics explain the information the retrieval system actually used. They do not add
amenities, public health, school quality, race, crime, or other unmodeled concepts to the meaning
of a match.

## Human review questions

For every selected query, reviewers should record:

1. Do the top matches share the housing composition, affordability, tenure, scale, and market
   pattern suggested by the model?
2. Is one family creating a plausible match while another contains a material contradiction?
3. Does the same physical community appear more than once at different years?
4. Is the candidate old enough that period conditions may weaken the comparison?
5. Would the FHFA outcome be representative for the query and candidate housing stocks?
6. Do standardized and PCA matches tell a similar story? If not, which differences explain the
   disagreement?
7. Would the application need a warning, or should this match be withheld?

Review notes should distinguish an understandable but imperfect match from a model defect. A
cross-state result is not automatically implausible; the purpose of national retrieval is to find
similar conditions beyond nearby markets.

## Repeated-community decision

The development unit is a tract-year state, so one physical tract may be eligible at several
historical years. This can be analytically useful when the same place passed through a similar
state more than once, but repeated tracts can reduce the diversity of the top ten and make the
historical outcome summary overly dependent on one community.

The audit therefore measures distinct physical tracts in every top ten and compares the current
tract-year rule with a unique-candidate-tract rule. No uniqueness rule should change silently. The
eventual application policy must state whether it returns historical states or distinct
communities.

## Completion standard

Case review is complete when representative and diagnostic cases have recorded evidence, obvious
mismatches are explained or corrected, repeat-community behavior is resolved or explicitly
accepted, and the findings are consistent with the quantitative stability results. Human review
supports the representation decision; it does not replace reproducible evaluation.
