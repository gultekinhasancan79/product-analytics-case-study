# Sequential Testing / Peeking-Risk Simulation

This deterministic null simulation demonstrates why repeatedly checking an ordinary fixed-horizon p-value and stopping when it first crosses 0.05 inflates the false-positive rate.

## Simulation design

- **Null trials:** 1,000
- **True control and treatment rate:** 52% in both arms
- **Maximum sample:** 5,000 users per arm
- **Looks:** every 250 users per arm, starting at 500
- **Total interim/final looks:** 19
- **Nominal alpha:** 0.05
- **Bonferroni alpha per look:** 0.0026

## False-positive behavior

| Analysis rule | Simulated false-positive rate |
| --- | ---: |
| Test only once at the final horizon | 4.4% |
| Naive repeated peeking; stop on any p < 0.05 | **23.5%** |
| Repeated looks with Bonferroni alpha allocation | 1.1% |

## Interpretation

- The final-horizon-only analysis stays close to the intended 5% Type-I error in this finite simulation.
- Reusing an ordinary 0.05 threshold at every look dramatically inflates false positives because the stopping rule changes the sampling process.
- Bonferroni controls family-wise error here but is deliberately conservative; production experimentation platforms often use pre-specified group-sequential boundaries or alpha-spending functions instead.
- The lesson is procedural: define the stopping rule and sequential method **before** treatment outcomes are inspected. Do not retrofit a correction after seeing a favorable interim result.

## Scope

This module is an educational peeking-risk demonstration, not the stopping rule used by the onboarding case study. The case study's main decision remains a fixed-horizon analysis with a pre-specified primary metric and guardrail.

## Reproducibility

The simulation uses a fixed seed (`20260808`). CI regenerates this report and fails if the committed false-positive evidence drifts.
