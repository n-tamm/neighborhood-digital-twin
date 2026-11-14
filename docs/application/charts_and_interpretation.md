# Application Charts and Interpretation

## Map: selected tract and historical matches

The map places the selected current tract in teal and historical matches in gold, with rank labels
for the matches. Marker locations are centers of simplified display bounds. The map answers
"where are these examples?" It does not show the exact tract boundary, prove spatial proximity,
or contribute to the similarity distance.

The same map appears once as page context and again inside the analogue investigation. Distinct
Streamlit keys prevent the two components from conflicting during one render.

## Housing composition

The stacked bar divides current housing units into single-family, multifamily, mobile-home, and
other structure shares. It is paired with occupancy and owner-occupancy cards. Its main purpose is
to show how much of the tract's broader housing stock resembles the single-family market covered
by FHFA; it should not be read as a quality score.

## Observed FHFA HPI history

The line chart uses only observations marked available. Missing annual values are not interpolated
or filled. HPI is an index of single-family price movement, not a dollar-valued home estimate.
Comparing index levels between unrelated tracts is less useful than reading change through time.

## Feature-family gap chart

Five bars show the mean absolute standardized gap between the query and one match for community
scale, occupancy and tenure, housing structure, affordability, and recent market trajectory.
Smaller is more alike under the approved representation. The chart explains why a candidate was
retrieved; it does not measure social similarity, total lived experience, or causal influence.

## Historical outcome trajectory

The trajectory aligns the matched tract at year zero and shows observed cumulative FHFA HPI
change afterward. A missing intermediate year remains a visible break. The selected path gives a
concrete answer to "what happened next in this earlier example?" It is descriptive evidence and
must not be labeled as the selected tract's predicted path.

## Shared visual rules

- Teal identifies the current selection or primary observed series; gold identifies historical
  analogue evidence; orange flags the largest explanatory gap.
- Red-to-green good/bad scales are avoided because the project does not rank community quality.
- Every percentage states whether it is a share or a percentage change in surrounding text.
- Important charts have nearby definitions and limitations rather than relying only on tooltips.
- Forecast intervals and drivers will get their own visual semantics after the serving contract is
  approved; they will not reuse analogue-range styling.
