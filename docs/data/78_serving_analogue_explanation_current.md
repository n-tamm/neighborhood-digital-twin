# `serving_analogue_explanation_current`

## Purpose and grain

This Delta table explains the implemented similarity distance without generating free-form text.
Its grain is one serving release, current query tract, horizon, and match rank. It has a one-to-one
key relationship with `serving_analogue_match_current`.

## Main structure

- five `*_mean_absolute_standardized_gap` fields retain every feature-family comparison;
- the closest and second-closest families identify the strongest shared characteristics;
- the largest and second-largest family gaps identify differences that should remain visible;
- the closest and most different individual features include readable names, query value,
  candidate value, and standardized gap;
- query and candidate imputation counts disclose whether the training-fitted imputer supplied any
  explanation values; and
- serving release, source model build, and exact-tree run fields preserve lineage.

Smaller standardized gaps mean closer inputs under the implemented representation. They are not
probabilities, quality scores, causal effects, or evidence that two communities are interchangeable.

## Construction and validation

The explanation uses the same horizon-specific training fit as retrieval. Publication requires
exact key reconciliation with the match table, valid family names, nonnegative gaps, correct
closest-to-largest ordering, and imputation counts between zero and twelve.

## Sample

See [`serving_analogue_explanation_current.jsonl`](../../data/samples/serving_analogue_explanation_current.jsonl).
It contains five ranked matches for one current tract. The sample is intentionally compact and
does not replace the full 43-column Databricks contract.

## Validated release

Release `analogue-20261113T132155097077Z` contains 934,380 explanation rows, exactly one for every
published match. Job 900 confirmed comments on all 43 columns. At each horizon, 68,370 match rows
belong to 6,837 queries with at least one imputed feature; the explanation exposes this instead of
hiding the training-fitted fill. Housing structure is the closest family most often, while recent
market trajectory is the largest difference most often. These frequencies describe how the
implemented representation behaves and are not statements about causes of later HPI change.
