<h1 align="center">Product Analytics Case Study</h1>

<p align="center">
  Experiment design, SQL analysis, statistical inference, data-quality checks, and a decision-ready product readout.
</p>

<p align="center">
  <a href="https://github.com/gultekinhasancan79/product-analytics-case-study/actions/workflows/ci.yml"><img src="https://github.com/gultekinhasancan79/product-analytics-case-study/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SQL-Executable%20in%20CI-336791?logo=postgresql&logoColor=white" alt="SQL">
  <img src="https://img.shields.io/badge/A%2FB%20Testing-Product%20Experiment-7C3AED" alt="A/B Testing">
  <img src="https://img.shields.io/badge/Data-Synthetic%20%26%20Deterministic-2ea44f" alt="Synthetic deterministic data">
  <img src="https://img.shields.io/badge/License-MIT-2ea44f" alt="MIT License">
</p>

---

## Executive Summary

This repository is an end-to-end **product analytics case study** built around a fictional SaaS onboarding experiment.

The product team is testing a **guided onboarding checklist** against the existing onboarding flow. The business question is straightforward:

> Does guided onboarding increase the share of new users who reach activation within seven days, without increasing support burden?

The analysis uses a deterministic synthetic dataset of **12,000 randomized signups** so every result can be regenerated and reviewed from source.

### Decision

**Ship the treatment**, then investigate the weaker mobile response before assuming the same mechanism works equally well across devices.

| Metric | Control | Treatment | Lift | Statistical read |
| --- | ---: | ---: | ---: | --- |
| **7-day activation — primary** | 51.16% | 53.30% | **+2.13 pp** | p = 0.0193; 95% CI +0.35 to +3.92 pp |
| 14-day retention | 39.34% | 42.52% | **+3.18 pp** | p = 0.0004 |
| Support ticket within 7 days — guardrail | 9.94% | 8.53% | **-1.41 pp** | p = 0.0077 |
| Mean 30-day revenue / signup | $21.42 | $22.94 | +$1.52 | descriptive |
| Mean time-to-value among activated users | 20.15 h | 17.77 h | -2.38 h | descriptive |

<p align="center">
  <img src="assets/activation_result.svg" alt="7-day activation result" width="760">
</p>

The primary result corresponds to a **+4.17% relative lift** in activation. The support-ticket guardrail moves in the favorable direction rather than revealing an onboarding-cost tradeoff.

---

## Product & Experiment Context

### Product

A fictional B2B analytics product where new users typically need to:

1. connect a data source,
2. create their first dashboard,
3. reach a useful first outcome,
4. and return after onboarding.

### Treatment

The treatment adds a guided checklist that makes the critical setup steps explicit and keeps onboarding progress visible.

### Experiment design

- **Unit of randomization:** signup / user
- **Allocation:** approximately 50/50 control vs treatment
- **Primary metric:** 7-day activation
- **Secondary metric:** 14-day retention
- **Guardrail:** support ticket within seven days
- **Exploratory metrics:** time-to-value, 30-day revenue, device/channel diagnostics
- **Primary statistical test:** two-sided two-proportion z-test, alpha = 0.05
- **Data:** deterministic synthetic data; no real customer information

See [`docs/experiment_design.md`](docs/experiment_design.md) for the analysis contract and [`docs/metric_definitions.md`](docs/metric_definitions.md) for metric definitions.

---

## Key Diagnostic

The overall treatment wins, but the device split is not uniform:

| Device | Control activation | Treatment activation | Lift |
| --- | ---: | ---: | ---: |
| Desktop | 54.64% | 58.15% | **+3.51 pp** |
| Mobile | 45.68% | 45.90% | **+0.23 pp** |

This is deliberately treated as **exploratory**, not as proof of a treatment-by-device interaction. The experiment is powered around the overall primary metric, not subgroup effects.

A sensible product follow-up would be a mobile onboarding usability investigation before designing a second targeted experiment.

---

## Analysis Layers

### Python

The Python pipeline covers:

- deterministic experiment-data generation,
- data-quality validation,
- primary/secondary/guardrail metric calculation,
- two-proportion hypothesis tests,
- confidence intervals,
- segment diagnostics,
- and reproducible Markdown report generation.

The implementation intentionally uses the Python standard library so the statistical logic is visible instead of being hidden behind a large analytics framework.

### SQL

The SQL layer contains executable queries for:

- activation funnel readouts,
- experiment-level KPI tables,
- device diagnostics,
- and acquisition-channel diagnostics.

CI loads the generated dataset into an in-memory relational database and executes every analytical SQL file. The queries use conservative SQL constructs that translate naturally to PostgreSQL-style analytics work.

### Data Quality

Before analysis, the pipeline checks invariants including:

- unique `user_id`,
- valid experiment variants and dimensions,
- binary metric domains,
- no dashboard creation without a connected data source,
- no activation without the required funnel steps,
- valid time-to-value semantics,
- and non-negative revenue.

---

## Repository Structure

```text
.
├── .github/workflows/ci.yml
├── assets/
│   └── activation_result.svg
├── data/
│   └── README.md
├── docs/
│   ├── experiment_design.md
│   └── metric_definitions.md
├── reports/
│   └── experiment_summary.md
├── sql/
│   ├── 00_schema.sql
│   ├── 01_activation_funnel.sql
│   ├── 02_experiment_readout.sql
│   ├── 03_device_diagnostics.sql
│   └── 04_channel_diagnostics.sql
├── src/
│   ├── data_quality.py
│   ├── experiment.py
│   ├── generate_dataset.py
│   └── run_sql.py
└── tests/
    └── test_pipeline.py
```

---

## Reproduce the Case Study

Requires Python 3.11+ and no third-party Python packages.

```bash
python -m src.generate_dataset
python -m src.data_quality
python -m src.experiment
python -m src.run_sql
python -m unittest discover -s tests -v
```

Generated data and temporary outputs are written under `artifacts/` and are intentionally excluded from version control.

The committed [`reports/experiment_summary.md`](reports/experiment_summary.md) is a reproducibility target: CI regenerates the report from seed and fails if the output drifts.

---

## What CI Proves

Every pull request regenerates the 12,000-row experiment and then:

1. runs data-quality checks,
2. regenerates the statistical readout,
3. diffs the generated report against the committed reference report,
4. executes every analytical SQL query,
5. and runs the unit-test suite.

This prevents the portfolio narrative from silently diverging from the code or generated evidence.

---

## Limitations

This is a **synthetic case study**, not evidence from a live production experiment. The data-generating process intentionally contains a treatment effect so the repository can demonstrate the complete analytics workflow.

The project therefore demonstrates analytical method, reproducibility, SQL/Python implementation, interpretation, and communication — not a claim about real customer behavior.

Exploratory segment results should not be promoted to causal subgroup conclusions without an interaction test and appropriate statistical power.

---

## Next Extensions

- add a pre-experiment power / minimum-detectable-effect calculator,
- add CUPED-style variance reduction with a simulated pre-period covariate,
- model experiment exposure/event-level data rather than only user-level outcomes,
- add a notebook-oriented walkthrough for exploratory analysis,
- and add a second case study focused on product funnel / retention analysis rather than experimentation.

## License

MIT
