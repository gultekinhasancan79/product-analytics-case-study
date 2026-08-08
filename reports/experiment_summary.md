# Experiment Readout — Guided Onboarding Checklist

**Decision: SHIP treatment.** The primary activation metric improved significantly and the support-ticket guardrail also improved.

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

## Exploratory device diagnostic

| Device | Control activation | Treatment activation | Lift |
| --- | ---: | ---: | ---: |
| desktop | 54.64% | 58.15% | +3.51 pp |
| mobile | 45.68% | 45.90% | +0.23 pp |

> Segment results are exploratory. The experiment was powered for the overall primary metric, not for interaction effects between treatment and device.

## Interpretation

- The treatment improves the primary activation metric without trading off the support burden.
- The retention lift is directionally consistent with the activation result and statistically strong in this synthetic experiment.
- Faster time-to-value and higher 30-day revenue are useful supporting signals, but are treated as descriptive rather than additional confirmatory tests.
- The desktop/mobile split suggests a follow-up usability investigation on mobile before assuming the same mechanism drives both segments.

## Reproducibility

This report is generated from the deterministic synthetic dataset using `src/generate_dataset.py` and `src/experiment.py`. CI regenerates the data and diffs this report against the committed reference output.
