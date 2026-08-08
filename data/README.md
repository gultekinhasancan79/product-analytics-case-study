# Data

No customer or production data are committed to this repository.

The analysis dataset is generated deterministically at runtime:

```bash
python -m src.generate_dataset
```

Default generation parameters:

- rows: `12,000`
- random seed: `20260808`
- output: `artifacts/users.csv`

The generator creates signup-level experiment records with randomized variant assignment plus acquisition channel, device, onboarding funnel outcomes, retention, support burden, time-to-value, and 30-day revenue.

The probability rules intentionally include a modest treatment effect. This makes it possible to demonstrate an end-to-end experimentation workflow while keeping the repository fully reproducible and free of real user data.

Generated CSV files live under `artifacts/` and are ignored by Git.
