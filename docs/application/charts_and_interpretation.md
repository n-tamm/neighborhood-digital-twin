# Application Charts and Interpretation

## Local neighborhood context map

The main map draws the selected 2020 Census tract as a teal polygon within nearby tract outlines
and places a dark point at its center. The point remains visible at a wider zoom; the boundary
shows the tract's actual footprint after the user zooms in. The surrounding outlines use stronger
contrast over an OpenStreetMap basemap so the selected tract remains legible without hiding the
local street and place context.

The geometry comes from the simplified Census display-geometry pipeline rather than a bounding
rectangle. The context window is based on an expanded display extent and is capped at the nearest
80 tract centers so dense urban areas cannot return an unbounded payload.

The surrounding polygons answer "where is this tract relative to the local tract pattern?" They
are display context, not a claim that every visible tract is adjacent. Geometry is simplified and
must not be used for parcel boundaries, distance, adjacency, or similarity inputs.

## National historical-analogue map

The analogue map uses two coordinated layers. Numbered gold points keep every match visible at the
national extent, while lightly filled gold polygons reveal the exact tract footprints as the user
zooms closer. The selected neighborhood uses the same point-plus-polygon treatment in navy and
teal. Hovering provides place, historical year, and similarity distance.

Selecting a numbered map point or a county row updates the same selected-match state as the
dropdown. The footprint comparison, feature-gap explanation, and observed later trajectory below
the map therefore stay synchronized. At a national scale, tract shapes remain too small to inspect
directly, which is why the selected-match section also provides locally fitted footprint maps.

The maps are implemented with Plotly's documented
[`scattermap`](https://plotly.com/python/reference/scattermap/) and
[`choroplethmap`](https://plotly.com/python/reference/choroplethmap/) layers over
[OpenStreetMap](https://www.openstreetmap.org/) tiles. No mapping code was copied from another
application.

## Footprint comparison

When a historical match is selected, two local maps show the current and matched tract outlines
side by side. Each panel fits its own boundary so narrow or unusually shaped tracts remain
readable. Because independent zoom can make screen size misleading, the interface also reports
land area in square miles and explicitly tells the user to compare that value rather than apparent
panel size.

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

- Teal and navy identify the current selection or primary observed series; gold identifies
  historical analogue evidence; orange flags the largest explanatory gap.
- Red-to-green good/bad scales are avoided because the project does not rank community quality.
- Every percentage states whether it is a share or a percentage change in surrounding text.
- Important charts have nearby definitions and limitations rather than relying only on tooltips.
- Simplified geometry supports orientation and visual comparison only; it never changes a model
  feature, match rank, or forecast.
- Forecast intervals and drivers will get their own visual semantics after the serving contract is
  approved; they will not reuse analogue-range styling.
