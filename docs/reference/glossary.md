# Glossary

These definitions keep project language consistent across code, documentation, and the application.

| Term | Project meaning |
|---|---|
| Analogue | A tract at a specific historical time whose standardized state resembles the selected tract's current or selected state. Similarity does not imply the same future. |
| Availability date | The earliest date a value could reasonably have been used by the model, accounting for publication lag. |
| Backtest | Evaluation that recreates predictions from past forecast origins using only information available at each origin. |
| Baseline | A simple reference method that a more complex component must be compared against. |
| Bronze | Minimally changed, versioned copy of acquired source data plus retrieval metadata. |
| Calibration | Agreement between stated predictive uncertainty and observed outcomes over repeated cases. |
| Digital Twin | In this project, a data-backed, updateable representation of a tract through time with forecast, analogue, and scenario views. It is not a real-time physical replica. |
| Forecast horizon | Time between the forecast origin and the predicted outcome, such as one, three, or five years. |
| Forecast origin | The point in time at which a prediction is considered to be made. |
| Geography vintage | The specific release of geographic boundaries and identifiers used by a dataset. |
| Gold | Analysis-ready table with an approved grain and contract, built from validated upstream data. |
| Leakage | Information used in training or evaluation that would not have been available at the stated forecast origin or improperly crosses train/test boundaries. |
| Metro context | Comparison or feature values describing the broader metropolitan market containing a tract. |
| Neighborhood state | The approved set of tract-year measurements used to describe a community at a point in time. |
| Prediction interval | A range intended to contain a future outcome at a stated frequency under the evaluation setting. |
| Scenario | A user-specified change to approved model inputs used to inspect model sensitivity, not a causal intervention estimate. |
| Serving bundle | Immutable, validated collection of compact data and model outputs read by the application. |
| Silver | Cleaned, typed, source-aligned data that retains a source-oriented structure. |
| Spatial spillover | Association between an area's outcomes and conditions in nearby or connected areas. |
| Tract-year | One Census tract observed for one calendar or reference year; the planned core analytical grain. |

