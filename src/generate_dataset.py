from __future__ import annotations

import argparse
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

CHANNELS = ("organic", "paid_search", "partner", "referral")
CHANNEL_WEIGHTS = (0.36, 0.29, 0.18, 0.17)
START_DATE = date(2026, 6, 1)


def _weighted_channel(rng: random.Random) -> str:
    draw = rng.random()
    cumulative = 0.0
    for channel, weight in zip(CHANNELS, CHANNEL_WEIGHTS):
        cumulative += weight
        if draw < cumulative:
            return channel
    return CHANNELS[-1]


def generate_users(n: int = 12_000, seed: int = 20_260_808) -> list[dict[str, object]]:
    """Generate a deterministic synthetic onboarding experiment dataset."""
    rng = random.Random(seed)
    rows: list[dict[str, object]] = []

    for i in range(1, n + 1):
        variant = "treatment" if rng.random() < 0.5 else "control"
        channel = _weighted_channel(rng)
        device = "desktop" if rng.random() < 0.62 else "mobile"

        p_connect = (
            0.70
            + {"organic": 0.02, "paid_search": -0.03, "partner": 0.04, "referral": 0.03}[channel]
            + (0.03 if device == "desktop" else -0.03)
            + (0.025 if variant == "treatment" else 0.0)
        )
        connected_data = rng.random() < p_connect

        p_dashboard = (
            0.68
            + {"organic": 0.00, "paid_search": -0.02, "partner": 0.03, "referral": 0.02}[channel]
            + (0.04 if device == "desktop" else -0.04)
            + (0.03 if variant == "treatment" else 0.0)
        )
        created_dashboard = connected_data and rng.random() < p_dashboard
        activated_7d = created_dashboard

        p_retention = (
            0.22
            + (0.34 if activated_7d else 0.0)
            + {"organic": 0.02, "paid_search": -0.02, "partner": 0.01, "referral": 0.03}[channel]
            + (0.008 if variant == "treatment" else 0.0)
        )
        retained_14d = rng.random() < min(max(p_retention, 0.01), 0.95)

        p_ticket = (
            0.095
            + (0.02 if device == "mobile" else -0.01)
            + (0.01 if not activated_7d else -0.01)
            - (0.004 if variant == "treatment" else 0.0)
        )
        support_ticket_7d = rng.random() < max(p_ticket, 0.01)

        if activated_7d:
            base_ttv = 19.0 if variant == "control" else 16.5
            base_ttv += 3.0 if device == "mobile" else -1.5
            time_to_value_hours = max(0.5, rng.lognormvariate(math.log(base_ttv), 0.35))
        else:
            time_to_value_hours = None

        if retained_14d:
            revenue_30d = max(0.0, rng.gauss(44.0, 12.0))
        elif activated_7d:
            revenue_30d = max(0.0, rng.gauss(18.0, 8.0))
        else:
            revenue_30d = max(0.0, rng.gauss(4.0, 3.0)) if rng.random() < 0.15 else 0.0

        rows.append(
            {
                "user_id": f"U{i:06d}",
                "signup_date": (START_DATE + timedelta(days=(i - 1) % 28)).isoformat(),
                "variant": variant,
                "acquisition_channel": channel,
                "device": device,
                "connected_data": int(connected_data),
                "created_dashboard": int(created_dashboard),
                "activated_7d": int(activated_7d),
                "retained_14d": int(retained_14d),
                "support_ticket_7d": int(support_ticket_7d),
                "time_to_value_hours": "" if time_to_value_hours is None else f"{time_to_value_hours:.3f}",
                "revenue_30d": f"{revenue_30d:.2f}",
            }
        )

    return rows


def write_csv(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic onboarding experiment dataset.")
    parser.add_argument("--rows", type=int, default=12_000)
    parser.add_argument("--seed", type=int, default=20_260_808)
    parser.add_argument("--output", type=Path, default=Path("artifacts/users.csv"))
    args = parser.parse_args()
    rows = generate_users(args.rows, args.seed)
    write_csv(rows, args.output)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
