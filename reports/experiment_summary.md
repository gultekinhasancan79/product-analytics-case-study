# Experiment Readout — Guided Onboarding Checklist

**Decision: SHIP treatment.** The primary activation metric improved significantly and the support-ticket guardrail also improved.

## Experiment health

- **Assignment:** 6,024 control / 5,976 treatment.
- **Sample-ratio mismatch check:** p = 0.6613 — no evidence of allocation imbalance.
- **Largest pre-treatment standardized difference:** 0.028 — comfortably below the 0.10 review threshold.
- **Pre-analysis power target:** 3.00 pp MDE at 80% power and alpha = 0.05 requires about 8,694 users.
- **Realized allocation:** approximate 80%-power MDE at the observed control baseline is +2.55 pp.
- **Planning power at the observed +2.13 pp effect:** 64.8%. Statistical significance in this realization does not imply the design had 80% power for a 2.13 pp effect.

### Randomization balance

| Dimension | Level | Control share | Treatment share | Standardized difference |
| --- | --- | ---: | ---: | ---: |
| device | desktop | 61.22% | 60.37% | -0.017 |
| acquisition_channel | organic | 35.26% | 35.56% | +0.006 |
| acquisition_channel | paid_search | 29.18% | 30.02% | +0.018 |
| acquisition_channel | partner | 18.54% | 17.47% | -0.028 |
| acquisition_channel | referral | 17.02% | 16.95% | -0.002 |

## Primary metric

| Metric | Control | Treatment | Absolute lift | Relative lift | p-value | 95% CI on lift |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 7-day activation | 51.16% | 53.30% | +2.13 pp | +4.17% | 0.0193 | +0.35 pp to +3.92 pp |

## Secondary and guardrail metrics

| Metric | Control | Treatment | Absolute lift | p-value |
| --- | ---: | ---: | ---: | ---: |
| 14-day retention | 39.34% | 42.52% | +3.18 pp | 0.0004 |
| Support ticket within 7 days | 9.94% | 8.53% | -1.41 pp | 0.0077 |
| Mean 30-day revenue / signup | $21.42 | $22.94 | $+1.52 | descriptive |
| Mean time-to-value among activated users | 20.15 h | 17.77 h | -2.38 h | descriptive |

## Device heterogeneity diagnostic

| Device | Control activation | Treatment activation | Lift |
| --- | ---: | ---: | ---: |
| desktop | 54.64% | 58.15% | +3.51 pp |
| mobile | 45.68% | 45.90% | +0.23 pp |

**Treatment × device interaction:** desktop-minus-mobile lift difference +3.28 pp, p = 0.0773, 95% CI -0.36 pp to +6.93 pp.

> The interaction is suggestive but does not cross the 0.05 threshold. Device results remain exploratory rather than a confirmed heterogeneous treatment effect.

## CUPED-style sensitivity analysis

This sensitivity check adjusts activation using a treatment-blind pre-exposure propensity score built only from acquisition channel and device. Because this is a new-user experiment, it is **not** a classical pre-period outcome CUPED setup; the unadjusted primary analysis remains confirmatory.

- raw activation lift: +2.13 pp
- adjusted activation lift: +2.30 pp
- adjusted p-value: 0.0109
- adjusted 95% CI: +0.53 pp to +4.08 pp
- pooled outcome variance reduction: 1.47%

The adjustment is directionally consistent with the unadjusted result but produces only a modest variance reduction, so it is presented as a sensitivity analysis rather than a headline improvement.

## Interpretation

- The treatment improves the primary activation metric without trading off the support burden.
- Randomization diagnostics do not show sample-ratio mismatch or meaningful pre-treatment imbalance.
- The realized allocation supports an ~2.55 pp 80%-power MDE; the observed +2.13 pp effect had only ~64.8% planning power, despite being significant in this realized sample.
- The desktop/mobile contrast is worth product follow-up, but the formal interaction test is not conclusive at alpha = 0.05.
- The CUPED-style sensitivity remains positive and significant, but its 1.47% variance reduction is small and should not be oversold.
- Revenue and time-to-value remain descriptive supporting signals rather than additional confirmatory tests.

## Reproducibility

This report is generated from deterministic synthetic data using `src/generate_dataset.py`, `src/diagnostics.py`, `src/power.py`, `src/cuped.py`, and `src/experiment.py`. CI regenerates the data and diffs this report against the committed reference output.
