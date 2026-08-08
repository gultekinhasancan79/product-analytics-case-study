# Revenue Robustness Readout

Revenue is a zero-inflated, right-skewed supporting metric in this synthetic onboarding experiment. It was not the confirmatory decision metric, so this analysis is presented as robustness evidence rather than a new hypothesis test.

## Mean difference with deterministic percentile bootstrap

| Readout | Control | Treatment | Difference |
| --- | ---: | ---: | ---: |
| Mean 30-day revenue / signup | $21.42 | $22.94 | $+1.52 |

- **2,000-draw stratified percentile bootstrap 95% CI:** $+0.78 to $+2.30
- **Share of bootstrap draws with positive treatment lift:** 100.0%

## Robust location sensitivity

| Estimator | Control | Treatment | Difference |
| --- | ---: | ---: | ---: |
| 10% trimmed mean | $19.40 | $21.19 | $+1.79 |
| 5% winsorized mean | $21.15 | $22.64 | $+1.49 |

## Interpretation

- The ordinary mean difference is positive, and its deterministic percentile-bootstrap interval stays above zero in this synthetic dataset.
- The treatment-control difference remains positive under both trimmed and winsorized means, so the direction is not being driven only by a small number of large revenue observations.
- This does **not** promote revenue to a confirmatory outcome. The product decision remains anchored to the pre-specified activation metric and support-ticket guardrail.
- In a production experiment, the revenue estimand, observation window, handling of refunds/outliers, and bootstrap procedure should be frozen before treatment outcomes are inspected.

## Reproducibility

The analysis uses a fixed bootstrap seed (`20260808`) and 2,000 within-arm resamples. CI regenerates this report from the deterministic user dataset and fails if the committed evidence drifts.
