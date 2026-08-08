# Experiment Design

## Business question

Does a guided onboarding checklist increase the probability that a newly signed-up user reaches activation within seven days, without increasing early support burden?

## Hypothesis

- **Null:** the treatment and control activation rates are equal.
- **Alternative:** the activation rates differ.

The primary test is two-sided. A product decision can still use directionality after the statistical result is observed, but the inferential test itself does not assume treatment must win.

## Randomization

The synthetic generator assigns users independently to control or treatment with approximately 50/50 probability.

The user/signup is the unit of randomization and the unit of analysis. No repeated-user observations are introduced.

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
- activation / revenue by acquisition channel.

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

## Multiplicity and interpretation

The primary activation metric is the confirmatory outcome.

Retention and support tickets provide important supporting evidence, while revenue, time-to-value, and segment cuts are treated as descriptive / exploratory. Device and channel cuts should not be interpreted as confirmed heterogeneous treatment effects without dedicated interaction tests and adequate power.

## Synthetic-data disclosure

The experiment data are synthetic and generated from known probability rules. A positive treatment effect is intentionally embedded so the repository can demonstrate a complete experiment-analysis workflow.

This project demonstrates method and implementation, not evidence about a real product or real users.
