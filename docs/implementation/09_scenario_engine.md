# 09 — Scenario Engine

## Purpose

The scenario engine is the interactive core of the Digital Twin. It lets a user ask how the fitted model's forecast distribution responds when a small number of future assumptions change. It does not estimate what a policy intervention would cause.

## Scenario scope

Select two to four inputs that meet all of these conditions:

- available historically and aligned with forecast origins;
- used by the approved model through a documented transformation;
- understandable in units a user can change;
- supported by enough historical variation to define plausible bounds;
- not an unnecessary protected or sensitive characteristic;
- compatible with derived-variable consistency.

Likely candidates include mortgage-rate environment, income growth, population or household growth, and housing-unit or permit growth. Final inclusion depends on the data and model.

## MVP method

Use a precomputed sensitivity grid for the solo MVP:

1. define bounded values or percentiles for each supported input;
2. create valid combinations while preserving fixed observed state;
3. recompute dependent features;
4. score the approved point and uncertainty models;
5. store distribution summaries and support diagnostics;
6. interpolate only within validated grid cells in the app.

This keeps public interactions fast and reproducible. A team may add historical conditional resampling or correlated simulation later, but arbitrary independent sliders should not generate impossible states.

## Baseline and scenario flow

```text
Observed tract state
  + baseline future-driver assumptions
  -> baseline forecast distribution

Observed tract state
  + user-adjusted supported assumptions
  -> scenario forecast distribution

Displayed difference = modeled sensitivity, not treatment effect
```

The baseline assumptions must be visible. A scenario result without its reference distribution is easy to misread.

## Plausibility and support

Each input shows its units, historical range, and selected percentile. The complete scenario receives a multivariate support score based on the training distribution. Possible methods include robust Mahalanobis distance, nearest-neighbor distance, or a density estimate that works with the small scenario feature set.

Define three states:

- supported: within normal historical support;
- caution: unusual but scoreable with a visible warning;
- unsupported: refuse or clearly suppress the numerical result.

The thresholds come from training data and validation review, not the final test.

## Consistency rules

Changing income may require recomputing price-to-income or burden proxies. Changing population or households may affect per-capita fields. Scenario definitions should list every derived field that must update, which variables stay fixed, and why.

Where domain expectations are defensible, run monotonicity diagnostics. Do not force a monotonic rule merely because it sounds intuitive; the project can report a learned non-monotonic association while warning that it is not causal.

## Scenario contract

Each result should retain:

- tract, forecast origin, and horizon;
- baseline input state;
- changed inputs and units;
- model, feature, calibration, and scenario versions;
- random seed or grid identifier;
- support score and status;
- baseline and scenario distribution summaries;
- interpolation method if used;
- warning and limitation codes.

## Validation

- **Validity:** no impossible combinations or broken derived fields.
- **Continuity:** nearby input values do not create unexplained jumps.
- **Reproducibility:** fixed definitions and seeds produce the same output.
- **Historical plausibility:** permitted combinations resemble observed joint states.
- **Support:** the allowed UI range does not routinely produce unsupported states.
- **Communication:** reviewers understand that the output is sensitivity, not causality.

Compare selected scenario combinations with held-out historical transitions that had similar starting states and driver values. This is a plausibility check, not causal validation.

## Required outputs

- versioned scenario definitions and bounds;
- scenario grid or simulator;
- consistency and support rules;
- scenario validation report;
- app-ready baseline and scenario distribution contract;
- visible language for supported, caution, and unsupported states.

## Acceptance checks

- every scenario input maps to a real model feature and documented unit;
- ranges are derived from training data;
- derived values remain internally consistent;
- unsupported combinations are not presented as ordinary forecasts;
- scenario results reproduce from the same version and seed;
- the interface never describes a scenario difference as a causal effect.
