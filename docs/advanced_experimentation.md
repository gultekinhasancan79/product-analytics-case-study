# Advanced Experimentation Methods

This document describes the planning and variance-reduction extensions used in the onboarding experiment case study.

## 1. Power and minimum detectable effect

The repository uses a normal approximation for a two-sided two-proportion z-test. Given a control baseline, treatment effect, arm sizes, and alpha, the planner estimates the probability that the treatment-minus-control difference crosses the two-sided null critical boundary under the alternative.

The calculator supports three related questions:

- **Power:** if the true absolute lift is a specified size, how often would this design reject the null?
- **MDE:** for fixed sample sizes, what is the smallest positive lift that reaches the target power?
- **Required sample:** for a target lift, how many users per arm are needed to reach the target power?

For the current synthetic experiment:

- control: 6,024 users,
- treatment: 5,976 users,
- control activation: 51.16%,
- observed lift: +2.13 pp,
- 80% power MDE: approximately +2.55 pp,
- planning power at the observed lift: approximately 64.8%,
- balanced sample for an 80%-powered +2.00 pp effect: approximately 9,792 users per arm.

### Important interpretation

MDE is not a significance threshold. An experiment can produce a statistically significant result for an effect smaller than its 80%-power MDE; it simply would not do so with 80% probability across repeated samples when that smaller effect is the truth.

Power and MDE should therefore be used **before launch** to align the sample plan with the smallest effect worth making a product decision on.

Implementation: [`src/power.py`](../src/power.py).

## 2. CUPED-style covariate adjustment

Classical CUPED often uses a pre-period version of the outcome because a strongly correlated pre-treatment measure can reduce outcome variance without introducing treatment information.

This case study is a **new-user onboarding experiment**. New signups do not have a genuine pre-period activation outcome, so inventing one would be methodologically misleading.

Instead, the repository demonstrates the same covariate-adjustment mechanics with a treatment-blind activation propensity derived only from fields known before exposure:

- acquisition channel,
- device.

The score intentionally excludes randomized variant and all post-exposure outcomes.

For outcome `Y` and pre-treatment score `X`, the adjustment is:

```text
theta = Cov(Y, X) / Var(X)
Y_adjusted = Y - theta * (X - mean(X))
```

The treatment effect is then estimated as the difference in adjusted means.

### Current result

- pooled outcome variance reduction: 1.47%,
- raw lift: +2.13 pp,
- adjusted lift: +2.30 pp,
- adjusted 95% CI: +0.53 to +4.08 pp,
- adjusted p-value: 0.0109.

The variance reduction is intentionally modest because device and acquisition channel are only weak predictors of individual activation. A real pre-period behavioral measure for established users could be substantially more predictive.

Implementation: [`src/cuped.py`](../src/cuped.py).

## 3. Decision discipline

The original unadjusted activation test remains the **confirmatory primary analysis**. The CUPED-style result was added after the core case study was defined, so it is presented as a sensitivity/precision demonstration rather than a replacement decision statistic.

In a real experiment, the following should be frozen before reading treatment outcomes:

- primary metric,
- alpha and sidedness,
- target power / MDE,
- sample-size or stopping rule,
- covariate definition,
- adjustment method,
- guardrails,
- planned segment analyses.

## 4. Reproducibility

`src/advanced_readout.py` regenerates the advanced report from the same deterministic dataset as the primary analysis. CI diffs the generated output against `reports/advanced_experimentation.md`.

The Jupyter walkthrough in `notebooks/advanced_experimentation.ipynb` uses only repository modules and the Python standard library. CI parses and executes each code cell through `src/execute_notebook.py`, so the notebook cannot silently drift away from the tested code path.
