# V2 Methodology Upgrade

This iteration closes several gaps that are common in portfolio experiment analyses.

## What changed

1. **Experiment integrity before outcomes**
   - sample-ratio mismatch check,
   - standardized pre-treatment balance diagnostics.

2. **Pre-analysis planning**
   - two-sided sample-size calculation,
   - minimum detectable effect calculation,
   - explicit alpha / power assumptions.

3. **Heterogeneity analysis**
   - formal desktop-vs-mobile treatment interaction contrast,
   - confidence interval and p-value,
   - subgroup findings remain exploratory when the interaction is inconclusive.

4. **Event-level product model**
   - deterministic event fact table linked to randomized users,
   - funnel, cohort, and event-latency SQL.

5. **Stronger data quality**
   - event referential integrity,
   - event cardinality and ordering,
   - activation/support time windows,
   - reconciliation between events and user-level outcomes.

The goal is to demonstrate the workflow expected around a real experiment: validate assignment, understand power, estimate the primary effect, treat subgroup analysis carefully, and make both user-level and event-level evidence reproducible.
