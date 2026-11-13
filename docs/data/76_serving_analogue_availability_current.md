# `serving_analogue_availability_current`

## Purpose and grain

This Delta table makes missing results explicit. Its grain is one serving release, current-profile
tract, and supported horizon. It includes both eligible and ineligible tracts, so the application
can keep a community profile visible and explain why analogues are absent.

## Important fields

- `analogue_available` is true only when the release contains a complete approved top ten.
- `availability_reason` is `available` or records the first applicable data/model limitation.
- current ACS, FHFA, and similarity flags preserve the underlying coverage context.
- `target_representativeness_band` groups the current single-family share as high, mixed, limited,
  or unknown.
- `target_scope_note` provides an application-ready explanation of what the FHFA outcome does and
  does not represent.
- the release, current-profile build, model-readiness build, and tree-run fields preserve lineage.

## Application rule

Read this table before requesting a summary or matches. If `analogue_available` is false, show the
recorded reason and do not silently substitute a different horizon, tract, or method.

## Sample

See [`serving_analogue_availability_current.jsonl`](../../data/samples/serving_analogue_availability_current.jsonl).
It includes one example of each current availability reason.
