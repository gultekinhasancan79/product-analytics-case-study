from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

EVENT_NAMES = {
    "signup",
    "data_connected",
    "dashboard_created",
    "support_ticket_opened",
    "active_day_14",
    "revenue_recorded",
}


def _event_rng(seed: int, user_id: str) -> random.Random:
    return random.Random(f"{seed}:{user_id}")


def generate_events(
    users: list[dict[str, str]], seed: int = 20_260_808
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    event_counter = 1

    def append_event(
        user_id: str,
        event_name: str,
        event_ts: datetime,
        event_value: str | float = "",
    ) -> None:
        nonlocal event_counter
        events.append(
            {
                "event_id": f"E{event_counter:08d}",
                "user_id": user_id,
                "event_name": event_name,
                "event_ts": event_ts.isoformat(timespec="seconds"),
                "event_value": event_value,
            }
        )
        event_counter += 1

    for row in users:
        user_id = row["user_id"]
        rng = _event_rng(seed, user_id)
        signup_day = datetime.fromisoformat(row["signup_date"])
        signup_ts = signup_day + timedelta(
            hours=8 + rng.random() * 10,
            minutes=rng.randint(0, 59),
        )
        append_event(user_id, "signup", signup_ts)

        connected_ts: datetime | None = None
        if row["connected_data"] == "1":
            connected_ts = signup_ts + timedelta(hours=0.5 + rng.random() * 30)
            append_event(user_id, "data_connected", connected_ts)

        if row["created_dashboard"] == "1":
            if connected_ts is None:
                raise ValueError("created_dashboard requires a data_connected event")
            dashboard_ts = connected_ts + timedelta(hours=0.5 + rng.random() * 36)
            append_event(user_id, "dashboard_created", dashboard_ts)

        if row["support_ticket_7d"] == "1":
            append_event(
                user_id,
                "support_ticket_opened",
                signup_ts + timedelta(hours=1 + rng.random() * (7 * 24 - 1)),
            )

        if row["retained_14d"] == "1":
            append_event(
                user_id,
                "active_day_14",
                signup_ts + timedelta(days=14, hours=rng.random() * 12),
            )

        revenue = float(row["revenue_30d"])
        if revenue > 0:
            append_event(
                user_id,
                "revenue_recorded",
                signup_ts + timedelta(days=30),
                f"{revenue:.2f}",
            )

    events.sort(key=lambda row: (row["event_ts"], row["event_id"]))
    for index, event in enumerate(events, start=1):
        event["event_id"] = f"E{index:08d}"
    return events


def read_users(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_events(events: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["event_id", "user_id", "event_name", "event_ts", "event_value"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic event-level fact table from the user experiment dataset."
    )
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/events.csv"))
    parser.add_argument("--seed", type=int, default=20_260_808)
    args = parser.parse_args()

    events = generate_events(read_users(args.input), seed=args.seed)
    write_events(events, args.output)
    print(f"wrote {len(events)} events to {args.output}")


if __name__ == "__main__":
    main()
