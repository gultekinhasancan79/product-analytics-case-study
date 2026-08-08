# Advanced Experimentation Methods

This document extends the experiment-health layer with power-at-effect interpretation and a CUPED-style variance-reduction sensitivity analysis.

## 1. Power and minimum detectable effect

`src/diagnostics.py` already treats power as a pre-analysis design question:

- **Required sample size:** users needed for a chosen baseline, MDE, alpha, and target power.
- **Realized MDE:** smallest effect the realized sample would detect with the target power under the normal approximation.
- **Power at a specified effect:** probability of crossing the two-sided critical boundary if that effect is the truth.

For the current deterministic experiment:

- control: 6,024 users,
- treatment: 5,976 users,
- control activation: 51.16%,
- observed lift: +2.13 pp,
- 80% power MDE: approximately +2.55 pp,
- planning power at the observed lift: approximately 64.8%,
- balanced sample for an 80%-powered +2.00 pp effect: approximately 9,792 users per arm.

### Important interpretation

MDE is not a significance threshold. A sample can produce a statistically significant estimate for an effect smaller than its 80%-power MDE. The correct interpretation is that repeated experiments with that smaller true effect would not achieve significance 80% of the time.

Power and MDE therefore belong primarily **before launch**, when the team decides which effect size is worth detecting and whether the planned sample can resolve it.

## 2. CUPED-style covariate adjustment

Classical CUPED often uses a pre-period version of the outcome because a strongly correlated pre-treatment measure can reduce variance without introducing treatment information.

This case study is a **new-user onboarding experiment**. New signups do not have a genuine pre-period activation outcome, so inventing one would be methodologically misleading.

Instead, the repository demonstrates the same adjustment mechanics with a treatment-blind activation propensity derived only from fields known before exposure:

- acquisition channel,
- device.

The score excludes randomized variant and all post-exposure outcomes.

For outcome `Y` and pre-treatment score `X`:

```text
theta = Cov(Y, X) / Var(X)
Y_adjusted = Y - theta * (X - mean(X))
```

The treatment effect is then the difference in adjusted means.

### Current result

- pooled outcome variance reduction: 1.47%,
- raw activation lift: +2.13 pp,
- adjusted lift: +2.30 pp,
- adjusted 95% CI: +0.53 to +4.08 pp,
- adjusted p-value: 0.0109.

The variance reduction is intentionally modest because device and acquisition channel are weak predictors of individual activation. In an established-user experiment, a genuine pre-period behavioral metric can be substantially more predictive.

## 3. Decision discipline

The original unadjusted activation test remains the **confirmatory primary analysis**. The CUPED-style result is presented as a sensitivity/precision demonstration rather than a replacement decision statistic.

In a production experiment, freeze these choices before reading treatment outcomes:

- primary metric,
- alpha and sidedness,
- target power / MDE,
- sample-size or stopping rule,
- covariate definition,
- adjustment method,
- guardrails,
- planned segment analyses.

## 4. Reproducibility

`src/advanced_readout.py` regenerates the advanced report from the same deterministic user dataset used by the primary experiment. CI diffs the result against `reports/advanced_experimentation.md`.

The Jupyter walkthrough in `notebooks/advanced_experimentation.ipynb` uses only repository modules and the Python standard library. CI parses and executes every code cell through `src/execute_notebook.py`, keeping the notebook on the tested code path without adding a notebook runtime dependency to the project.
