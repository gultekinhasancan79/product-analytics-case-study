<h1 align="center">Product Analytics Case Study</h1>

<p align="center">
  Reproducible product experimentation, event analytics, statistical diagnostics, robust inference, and decision-ready communication.
</p>

<p align="center">
  <a href="https://github.com/gultekinhasancan79/product-analytics-case-study/actions/workflows/ci.yml"><img src="https://github.com/gultekinhasancan79/product-analytics-case-study/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SQL-Executable%20in%20CI-336791?logo=postgresql&logoColor=white" alt="SQL">
  <img src="https://img.shields.io/badge/A%2FB%20Testing-Power%20%2B%20SRM-7C3AED" alt="A/B Testing">
  <img src="https://img.shields.io/badge/Event%20Model-41k%2B%20Events-0F766E" alt="Event model">
  <img src="https://img.shields.io/badge/Notebook-Executed%20in%20CI-F37626?logo=jupyter&logoColor=white" alt="Notebook executed in CI">
  <img src="https://img.shields.io/badge/Data-Synthetic%20%26%20Deterministic-2ea44f" alt="Synthetic deterministic data">
</p>

---

## Executive Summary

This repository is an end-to-end **product analytics and experimentation portfolio case study** built around a fictional B2B SaaS onboarding experiment.

The product question is:

> Does a guided onboarding checklist increase seven-day activation without increasing support burden?

The core analysis uses **12,000 randomized signups** and a deterministic **41,209-row product-event fact table**. Every headline result is generated from source and checked in CI.

### Product decision

**Ship the treatment**, while keeping subgroup, revenue, variance-reduction, sequential-testing, and compliance analyses in their appropriate supporting roles.

| Metric | Control | Treatment | Lift | Statistical read |
| --- | ---: | ---: | ---: | --- |
| **7-day activation — primary** | 51.16% | 53.30% | **+2.13 pp** | p = 0.0193 · 95% CI +0.35 to +3.92 pp |
| 14-day retention | 39.34% | 42.52% | **+3.18 pp** | p = 0.0004 |
| Support ticket within 7 days — guardrail | 9.94% | 8.53% | **-1.41 pp** | p = 0.0077 |
| Mean 30-day revenue / signup | $21.42 | $22.94 | +$1.52 | supporting / robust analysis below |
| Mean time-to-value among activated users | 20.15 h | 17.77 h | -2.38 h | descriptive |

<p align="center">
  <img src="assets/activation_result.svg" alt="7-day activation result" width="760">
</p>

---

## Experiment Integrity & Planning

Outcome interpretation starts only after assignment and design checks:

- **6,024 control / 5,976 treatment**
- **SRM p = 0.6613** — no evidence of sample-ratio mismatch
- **max pre-treatment |SMD| = 0.028** — below the 0.10 review threshold
- **planning target:** 3.0 pp MDE · 80% power · two-sided alpha 0.05
- **required sample for that target:** about 8,694 users total
- **realized 80%-power MDE:** about **2.55 pp**
- **planning power at the observed +2.13 pp effect:** about **64.8%**

The distinction matters: one realized sample can be statistically significant even when the design did not have 80% power for an effect of exactly that size.

See [`docs/experiment_design.md`](docs/experiment_design.md) and [`docs/v2_methodology.md`](docs/v2_methodology.md).

---

## Advanced Experimentation Evidence

### Treatment × device interaction

Desktop shows a larger point estimate than mobile, but the project does not infer heterogeneity from separate subgroup p-values.

**Desktop-minus-mobile treatment-lift interaction:** **+3.28 pp · p = 0.0773 · 95% CI -0.36 to +6.93 pp**.

That is suggestive rather than conclusive at alpha = 0.05.

### CUPED-style sensitivity

A treatment-blind pre-exposure propensity score uses only acquisition channel and device. Because these are new users, there is no genuine pre-period activation outcome; this is deliberately described as **CUPED-style sensitivity**, not classical pre-period CUPED.

| Readout | Result |
| --- | ---: |
| Raw activation lift | +2.13 pp |
| Adjusted activation lift | +2.30 pp |
| Adjusted p-value | 0.0109 |
| Adjusted 95% CI | +0.53 to +4.08 pp |
| Outcome variance reduction | 1.47% |

The unadjusted primary analysis remains confirmatory.

### Robust revenue inference

Revenue is zero-inflated and right-skewed, so the repository does not rely only on a normal-theory mean comparison.

| Revenue readout | Result |
| --- | ---: |
| Mean treatment-control difference | **+$1.52 / signup** |
| 2,000-draw percentile-bootstrap 95% CI | **+$0.78 to +$2.30** |
| Bootstrap draws with positive lift | 100.0% |
| 10% trimmed-mean difference | +$1.79 |
| 5% winsorized-mean difference | +$1.49 |

Revenue remains a supporting metric rather than a retroactively promoted primary outcome. Full evidence: [`reports/revenue_robustness.md`](reports/revenue_robustness.md).

### Sequential testing / peeking risk

A separate deterministic **null simulation** shows why repeatedly using the same fixed-horizon `p < 0.05` rule while peeking can inflate Type-I error.

| Rule | Simulated false-positive rate |
| --- | ---: |
| Final-horizon test only | 4.4% |
| Naive repeated looks at p < 0.05 | **23.5%** |
| Repeated looks with conservative Bonferroni allocation | 1.1% |

This is an educational design-discipline simulation; it is **not** a stopping rule retrofitted onto the onboarding experiment. Full evidence: [`reports/sequential_peeking.md`](reports/sequential_peeking.md).

### Exposure logging — ITT vs treatment-on-treated

A separate 100,000-user compliance simulation demonstrates why randomized **assignment** and observed **exposure** are different analysis objects.

| Estimand / comparison | Result |
| --- | ---: |
| Treatment exposure rate | 78.1% |
| **ITT: assigned treatment - assigned control** | **+4.98 pp** |
| Naive exposed-treatment - control | +7.30 pp |
| Wald / IV treatment-on-treated estimate | +6.38 pp |
| True simulated exposure effect | +6.00 pp |

Device affects both compliance and baseline activation, so conditioning on observed exposure changes the population mix and breaks the original randomized comparison. The IV/Wald example is reported only under its explicit one-sided non-compliance, monotonicity, and exclusion-restriction assumptions.

Full evidence: [`reports/exposure_itt_tot.md`](reports/exposure_itt_tot.md).

---

## Event Analytics & SQL

The project contains both randomized-user outcomes and a linked product-event table.

```text
product_users                         product_events
─────────────                         ──────────────
user_id  ───────────────────────────▶ user_id
variant                               event_id
device                                event_name
acquisition_channel                   event_ts
activated_7d                          event_value
retained_14d
support_ticket_7d
revenue_30d
```

The SQL layer is executable in CI and covers:

- activation funnel readouts,
- experiment KPI tables,
- device and acquisition-channel diagnostics,
- event-based funnel conversion,
- weekly signup cohorts,
- and latency from signup to dashboard creation.

The data-quality layer validates user/event IDs, domains, funnel invariants, event ordering, referential integrity, outcome windows, and reconciliation between event presence and user-level metrics.

---

## Executable Reviewer Notebook

[`notebooks/experiment_walkthrough.ipynb`](notebooks/experiment_walkthrough.ipynb) gives a compact reviewer path through:

- the primary treatment effect,
- SRM and pre-treatment balance,
- device interaction inference,
- MDE and planning power,
- required sample size,
- and CUPED-style sensitivity.

The notebook imports the same tested repository modules instead of duplicating formulas. CI executes every code cell through `src/execute_notebook.py`.

---

## Reproducible Evidence

| Artifact | Purpose |
| --- | --- |
| [`reports/experiment_summary.md`](reports/experiment_summary.md) | Primary decision, integrity, power, interaction, CUPED |
| [`reports/revenue_robustness.md`](reports/revenue_robustness.md) | Bootstrap + trimmed/winsorized revenue sensitivity |
| [`reports/sequential_peeking.md`](reports/sequential_peeking.md) | Repeated-look Type-I error simulation |
| [`reports/exposure_itt_tot.md`](reports/exposure_itt_tot.md) | Assignment, exposure, ITT and treatment-on-treated demo |
| [`notebooks/experiment_walkthrough.ipynb`](notebooks/experiment_walkthrough.ipynb) | Reviewer-oriented executable walkthrough |

---

## Repository Structure

```text
.
├── .github/workflows/ci.yml
├── assets/
│   └── activation_result.svg
├── docs/
│   ├── analysis_checklist.md
│   ├── experiment_design.md
│   ├── metric_definitions.md
│   └── v2_methodology.md
├── notebooks/
│   └── experiment_walkthrough.ipynb
├── reports/
│   ├── experiment_summary.md
│   ├── exposure_itt_tot.md
│   ├── revenue_robustness.md
│   └── sequential_peeking.md
├── sql/
│   ├── 00_schema.sql
│   ├── 01_activation_funnel.sql
│   ├── 02_experiment_readout.sql
│   ├── 03_device_diagnostics.sql
│   ├── 04_channel_diagnostics.sql
│   ├── 05_event_funnel.sql
│   ├── 06_weekly_cohort.sql
│   └── 07_event_latency.sql
├── src/
│   ├── cuped.py
│   ├── data_quality.py
│   ├── diagnostics.py
│   ├── execute_notebook.py
│   ├── experiment.py
│   ├── exposure_demo.py
│   ├── generate_dataset.py
│   ├── generate_events.py
│   ├── power.py
│   ├── revenue_robust.py
│   ├── run_sql.py
│   └── sequential.py
└── tests/
    ├── test_advanced_experimentation.py
    ├── test_exposure_demo.py
    ├── test_notebook.py
    ├── test_pipeline.py
    ├── test_revenue_robust.py
    └── test_sequential.py
```

---

## Reproduce Locally

Requires Python 3.11+ and no third-party runtime packages.

```bash
python -m src.generate_dataset
python -m src.generate_events
python -m src.data_quality
python -m src.power --baseline 0.5116201859 --n-control 6024 --n-treatment 5976 --effect 0.0213450082
python -m src.cuped
python -m src.execute_notebook
python -m src.experiment
python -m src.revenue_robust
python -m src.sequential
python -m src.exposure_demo
python -m src.run_sql
python -m unittest discover -s tests -v
```

Generated data and temporary outputs live under `artifacts/` and are excluded from version control.

---

## What CI Proves

Every pull request:

1. compiles the Python sources,
2. regenerates the 12,000-user experiment,
3. regenerates the 41,209-row event fact table,
4. validates user and event contracts,
5. smoke-tests power and CUPED paths,
6. executes the reviewer notebook,
7. regenerates and diffs the primary experiment report,
8. regenerates and diffs the revenue robustness report,
9. regenerates and diffs the sequential-testing simulation,
10. regenerates and diffs the exposure / ITT report,
11. executes every analytical SQL query,
12. and runs the full behavioral/statistical test suite.

This keeps the portfolio narrative, notebooks, reports, and source code on the same tested path.

---

## Methodological Discipline & Limitations

This is a **synthetic case study**, not evidence from a production experiment. Treatment effects are intentionally present so the repository can demonstrate an end-to-end analytics workflow.

Key boundaries are explicit:

- the unadjusted seven-day activation test is the primary confirmatory analysis,
- support tickets are the guardrail,
- revenue and time-to-value are supporting outcomes,
- device heterogeneity remains exploratory because the interaction is inconclusive at alpha 0.05,
- CUPED-style adjustment is a sensitivity demonstration rather than genuine pre-period CUPED,
- the sequential module is a separate null simulation rather than a retroactive stopping rule,
- and the exposure / ITT module is a separate compliance simulation rather than fabricated telemetry for the main experiment.

A production system would additionally need instrumentation QA, exposure logging, identity resolution, late-event handling, experiment governance, multiplicity policy, and a pre-registered stopping rule.

---

## Next Extension

The next distinct case-study direction is **retention / lifecycle analytics** rather than adding more methods to this single onboarding experiment.

## License

MIT
