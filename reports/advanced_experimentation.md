# Advanced Experimentation Readout

## Power and MDE

- Allocation: **6,024 control / 5,976 treatment**
- Control activation baseline: **51.16%**
- Observed raw lift: **+2.13 pp**
- 80% power MDE at alpha=0.05: **2.55 pp**
- Approximate planning power at the observed lift: **64.8%**
- Balanced sample needed for an 80%-powered +2.00 pp effect: **9,792 users / arm**

The observed +2.13 pp lift is smaller than the design's approximately +2.55 pp 80%-power MDE. A significant realization is still possible below the MDE; the implication is that this sample would not detect an effect of this size with 80% probability across repeated experiments.

## CUPED-style sensitivity analysis

This new-user onboarding experiment does not have a genuine pre-period activation outcome. The adjustment therefore uses a treatment-blind activation propensity constructed only from **acquisition channel and device**, both known before exposure.

- CUPED theta: **1.0594**
- Pre-treatment score mean: **0.49821 control / 0.49662 treatment**
- Pooled outcome variance reduction: **1.47%**
- Raw activation lift: **+2.13 pp**
- Adjusted activation lift: **+2.30 pp**
- Adjusted 95% CI: **+0.53 to +4.08 pp**
- Adjusted p-value: **0.0109**

The adjusted result is a **post-hoc sensitivity analysis**, not a replacement for the pre-specified unadjusted primary analysis. In a production experiment, the covariate definition and adjustment method should be frozen before treatment outcomes are read.

## Decision discipline

- Keep the unadjusted 7-day activation analysis as the confirmatory decision statistic.
- Use MDE and power before launch to decide whether the planned sample can resolve the business-relevant effect size.
- Treat the CUPED-style result as evidence about estimator precision and robustness, not as a second chance to manufacture significance.
- For a future experiment with established users, prefer a true pre-period behavioral covariate when applying classical CUPED.
