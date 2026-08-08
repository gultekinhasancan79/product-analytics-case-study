# Exposure Logging — ITT vs Treatment-on-Treated Demo

This is a separate deterministic compliance simulation designed to demonstrate why randomized **assignment** and observed **exposure** answer different causal questions.

It is intentionally separate from the main onboarding experiment so the existing case-study data are not retrofitted with an exposure mechanism that was never part of their data-generating process.

## Demo design

- **Randomized sample:** 100,000 users
- **Assignment:** 50,067 control / 49,933 treatment
- **True effect of actual exposure in the simulator:** +6.00 pp activation
- **One-sided non-compliance:** controls cannot receive treatment exposure
- **Treatment exposure probability:** 90% desktop / 60% mobile
- **Baseline activation:** 50% desktop / 40% mobile

Because device affects both baseline activation and treatment compliance, the exposed treatment subset has a different device mix from the randomized control arm.

## Readout

| Estimand / comparison | Result |
| --- | ---: |
| Treatment exposure rate | 78.1% |
| Control activation | 46.02% |
| Treatment-assigned activation | 51.00% |
| **ITT: assigned treatment - assigned control** | **+4.98 pp** |
| Exposed-treatment activation | 53.32% |
| Naive exposed-treatment - control | +7.30 pp |
| Wald / IV treatment-on-treated estimate | +6.38 pp |

## Interpretation

- **ITT** preserves randomization because users are analyzed by assigned variant regardless of whether treatment was actually seen. It answers the product-policy question: what is the effect of assigning this treatment under real delivery/compliance?
- Comparing only exposed treatment users with controls breaks the original randomized comparison. In this simulator, desktop users are more likely to be exposed and also have higher baseline activation, so the naive exposed-vs-control contrast overstates the +6 pp exposure effect.
- Under the demo's explicit one-sided non-compliance, monotonicity, and exclusion-restriction assumptions, randomized assignment can be used as an instrument. The Wald ratio `ITT / exposure-rate difference` moves the estimate back toward the simulated +6 pp treatment-on-treated effect.
- The IV result should not be copied mechanically into production analysis. Instrument validity, exposure logging quality, interference, monotonicity, and exclusion restrictions must be defended for the actual product system.

## Exposure logging requirements

A production implementation should separately log at least: assignment, experiment eligibility, exposure timestamp, treatment version, user/session identity, and outcome windows. Assignment should never be inferred from downstream treatment events.

## Reproducibility

The demo uses a fixed seed (`20260808`) and 100,000 simulated users. CI regenerates this report and fails if the committed estimand evidence drifts.
