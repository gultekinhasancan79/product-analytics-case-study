# Data

No customer or production data are committed to this repository.

Two deterministic analytical datasets are generated at runtime:

```bash
python -m src.generate_dataset
python -m src.generate_events
```

## User experiment table

Default parameters:

- rows: `12,000`
- random seed: `20260808`
- output: `artifacts/users.csv`

This table contains the randomized experiment assignment, pre-treatment dimensions, onboarding outcomes, retention, support burden, time-to-value, and 30-day revenue.

## Event fact table

Default output: `artifacts/events.csv`.

For the default 12,000-user dataset the deterministic generator produces **41,209 product events** across signup, data connection, dashboard creation, support, retention, and revenue lifecycle events.

The event table exists to demonstrate event-based funnel, cohort, and timing SQL rather than relying only on pre-aggregated user outcome columns.

## Synthetic-data disclosure

The probability rules intentionally include a modest treatment effect. Event timestamps are then generated deterministically to be consistent with the user-level outcomes.

This makes it possible to demonstrate an end-to-end experimentation and product-analytics workflow while keeping the repository reproducible and free of real user data.

Generated CSV files live under `artifacts/` and are ignored by Git.
