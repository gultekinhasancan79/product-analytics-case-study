# Experiment Design

## Business question

Does a guided onboarding checklist increase the probability that a newly signed-up user reaches activation within seven days, without increasing early support burden?

## Hypothesis

- **Null:** the treatment and control activation rates are equal.
- **Alternative:** the activation rates differ.

The primary test is two-sided. A product decision can still use directionality after the statistical result is observed, but the inferential test itself does not assume treatment must win.

## Randomization

The synthetic generator assigns users independently to control or treatment with approximately 50/50 probability.

The user/signup is the unit of randomization and the unit of analysis. No repeated-user observations are introduced in the experiment table. A separate event fact table is generated for funnel and timing analysis, but those events remain linked to the same randomized user.

## Pre-analysis power plan

The planning target is:

- **baseline activation:** approximately 51%,
- **minimum detectable effect:** 3.0 percentage points absolute,
- **alpha:** 0.05, two-sided,
- **power:** 80%,
- **allocation:** 50/50.

At the realized control baseline, detecting a 3.0 pp lift requires approximately **8,694 total users** under the normal approximation. The case study uses 12,000 users, corresponding to an approximate 80%-power MDE of **2.55 pp** at that baseline.

The power calculation is implemented in `src/diagnostics.py` rather than being a hand-written portfolio claim.

## Experiment integrity checks

Outcome analysis is preceded by two diagnostics:

1. **Sample-ratio mismatch (SRM):** compares observed treatment/control counts with the planned 50/50 allocation.
2. **Randomization balance:** reports standardized differences for pre-treatment device and acquisition-channel dimensions.

The balance review threshold is `|standardized difference| < 0.10`. A breach would trigger investigation before interpreting treatment effects.

## Metrics

### Primary

**7-day activation** — user connected a data source and created the first dashboard within the activation window.

### Secondary

**14-day retention** — user returned / remained active at the 14-day checkpoint.

### Guardrail

**Support ticket within 7 days** — proxy for onboarding confusion or operational burden.

### Exploratory

- mean time-to-value among activated users,
- mean 30-day revenue per signup,
- activation by device,
- activation / revenue by acquisition channel,
- event-based funnel conversion,
- weekly signup-cohort diagnostics.

## Statistical method

The primary, retention, and support-ticket comparisons use a two-sample proportion z-test.

For the primary metric, the repository reports:

- control and treatment rates,
- absolute percentage-point lift,
- relative lift,
- two-sided p-value,
- and an unpooled 95% confidence interval for the absolute lift.

The decision threshold for the primary metric is `alpha = 0.05`.

## Decision rule used in the case study

The generated report marks the treatment **SHIP** when:

1. the primary activation p-value is below 0.05,
2. the primary confidence interval is entirely above zero,
3. and the support-ticket guardrail confidence interval is entirely below zero.

This is intentionally stricter than using the primary p-value alone.

## Heterogeneous treatment effects

The device split is explicitly exploratory. The repository calculates a formal **difference-in-differences interaction contrast** between desktop and mobile treatment lifts, with a normal-approximation confidence interval and p-value.

This avoids the common mistake of declaring subgroup heterogeneity merely because one subgroup is individually significant and another is not.

## Multiplicity and interpretation

The primary activation metric is the confirmatory outcome.

Retention and support tickets provide important supporting evidence, while revenue, time-to-value, channel cuts, cohort cuts, and event-latency analysis are treated as descriptive / exploratory. Exploratory results should not be promoted to additional causal claims without a dedicated analysis plan and appropriate multiplicity control.

## Synthetic-data disclosure

The experiment data are synthetic and generated from known probability rules. A positive treatment effect is intentionally embedded so the repository can demonstrate a complete experiment-analysis workflow.

This project demonstrates method and implementation, not evidence about a real product or real users.
