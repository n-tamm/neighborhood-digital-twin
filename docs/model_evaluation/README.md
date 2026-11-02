# Model Evaluation Documentation

This folder documents the implemented evaluation rendering workflow and each of its seven current
figures. The forecast figures use validation data only. The similarity figure reports
unsupervised representation diagnostics. None is a locked-test or application-release result.

## Reading order

1. Read [Evaluation workflow](workflow.md) to understand run lineage and publication.
2. Review overall error and baseline skill in Figures 1-2.
3. Review bias, tail error, temporal stability, transfer, and housing composition in Figures 3,
   7, 4, and 5.
4. Review Figure 6 separately as a similarity representation diagnostic.

## Figure documentation

| Figure | Documentation | Decision supported |
|---:|---|---|
| 1 | [Forecast MAE by horizon](figures/01_forecast_mae_by_horizon.md) | Which method has the lowest average absolute validation error? |
| 2 | [Forecast skill versus zero](figures/02_forecast_skill_vs_zero.md) | Does a method improve on a transparent reference? |
| 3 | [Forecast bias and tail error](figures/03_forecast_bias_and_tail_error.md) | Does average accuracy hide systematic or large misses? |
| 4 | [Geographic transfer](figures/04_forecast_geographic_transfer.md) | Does performance change in held-out states? |
| 5 | [Housing-composition performance](figures/05_forecast_housing_composition.md) | Does error vary where FHFA represents less of the housing stock? |
| 6 | [Similarity representation diagnostics](figures/06_similarity_representation_diagnostics.md) | How do raw and PCA retrieval behave and agree? |
| 7 | [Forecast temporal stability](figures/07_forecast_temporal_stability.md) | Is a result consistent across independent validation origins? |

Metric definitions and overall model findings are maintained in the
[forecast evaluation guide](../forecasting/evaluation_and_results.md) and
[similarity evaluation guide](../similarity/evaluation_and_results.md).
