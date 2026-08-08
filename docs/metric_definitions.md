# Metric Definitions

## User-level experiment table

| Field / Metric | Type | Definition |
| --- | --- | --- |
| `user_id` | string | Unique signup-level identifier. |
| `signup_date` | date | Synthetic signup date used for cohort structure. |
| `variant` | category | Randomized experiment assignment: `control` or `treatment`. |
| `acquisition_channel` | category | `organic`, `paid_search`, `partner`, or `referral`. |
| `device` | category | `desktop` or `mobile`. |
| `connected_data` | binary | User successfully connected a data source. |
| `created_dashboard` | binary | User created the first dashboard. Requires `connected_data = 1`. |
| `activated_7d` | binary | Primary metric. User completed the activation funnel within seven days. |
| `retained_14d` | binary | User is active / retained at the 14-day checkpoint. |
| `support_ticket_7d` | binary | User opened a support ticket within seven days of signup. Used as a guardrail. |
| `time_to_value_hours` | numeric / null | Hours to first value for activated users; null for non-activated users. |
| `revenue_30d` | numeric | Synthetic 30-day revenue attributed to the signup. Non-negative. |

## Event fact table

The repository also generates `artifacts/events.csv` so SQL can operate on an event-style product analytics model instead of only pre-aggregated user flags.

| Field | Type | Definition |
| --- | --- | --- |
| `event_id` | string | Unique deterministic event identifier. |
| `user_id` | string | Foreign key to the randomized signup/user. |
| `event_name` | category | Product lifecycle event. |
| `event_ts` | timestamp | Deterministic ISO-8601 event timestamp. |
| `event_value` | numeric / null | Optional numeric value, used for revenue events. |

Generated event names:

- `signup`
- `data_connected`
- `dashboard_created`
- `support_ticket_opened`
- `active_day_14`
- `revenue_recorded`

The data-quality layer checks referential integrity, event cardinality, event ordering, seven-day support/activation windows, and agreement between event presence and the user-level outcome table.

## Funnel

```text
signup event
  ↓
data_connected event
  ↓
dashboard_created event
  ↓
7-day activation
  ↓
active_day_14 event / retention
```

## Metric hierarchy

- **Primary:** `activated_7d`
- **Secondary:** `retained_14d`
- **Guardrail:** `support_ticket_7d`
- **Exploratory:** `time_to_value_hours`, `revenue_30d`, event funnel, cohort, device/channel and event-latency diagnostics

The distinction matters because not every interesting metric should be treated as an independent confirmatory hypothesis test.
