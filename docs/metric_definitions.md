# Metric Definitions

| Field / Metric | Type | Definition |
| --- | --- | --- |
| `user_id` | string | Unique signup-level identifier. |
| `signup_date` | date | Synthetic signup date used for realistic dimensional structure. |
| `variant` | category | Randomized experiment assignment: `control` or `treatment`. |
| `acquisition_channel` | category | `organic`, `paid_search`, `partner`, or `referral`. |
| `device` | category | `desktop` or `mobile`. |
| `connected_data` | binary | User successfully connected a data source. |
| `created_dashboard` | binary | User created the first dashboard. Requires `connected_data = 1`. |
| `activated_7d` | binary | Primary metric. User completed the activation funnel within seven days. In this case study this means both data connection and first dashboard creation. |
| `retained_14d` | binary | User is active / retained at the 14-day checkpoint. |
| `support_ticket_7d` | binary | User opened a support ticket within seven days of signup. Used as a guardrail. |
| `time_to_value_hours` | numeric / null | Hours to first value for activated users; null for non-activated users. |
| `revenue_30d` | numeric | Synthetic 30-day revenue attributed to the signup. Non-negative. |

## Funnel

```text
Signup
  ↓
Connect data source
  ↓
Create first dashboard
  ↓
7-day activation
  ↓
14-day retention
```

## Metric hierarchy

- **Primary:** `activated_7d`
- **Secondary:** `retained_14d`
- **Guardrail:** `support_ticket_7d`
- **Exploratory:** `time_to_value_hours`, `revenue_30d`, device/channel segment metrics

The distinction matters because not every interesting metric should be treated as an independent confirmatory hypothesis test.
