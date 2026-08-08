from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BINARY_FIELDS = (
    "connected_data",
    "created_dashboard",
    "activated_7d",
    "retained_14d",
    "support_ticket_7d",
)
VALID_VARIANTS = {"control", "treatment"}
VALID_DEVICES = {"desktop", "mobile"}
VALID_CHANNELS = {"organic", "paid_search", "partner", "referral"}
VALID_EVENTS = {
    "signup",
    "data_connected",
    "dashboard_created",
    "support_ticket_opened",
    "active_day_14",
    "revenue_recorded",
}


def validate_rows(rows: list[dict[str, str]], expected_rows: int | None = None) -> list[str]:
    errors: list[str] = []
    required = {
        "user_id",
        "signup_date",
        "variant",
        "acquisition_channel",
        "device",
        *BINARY_FIELDS,
        "time_to_value_hours",
        "revenue_30d",
    }

    if not rows:
        return ["dataset must contain at least one row"]

    missing = required - set(rows[0])
    if missing:
        return [f"missing required columns: {', '.join(sorted(missing))}"]

    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"expected {expected_rows} rows, found {len(rows)}")

    user_ids = [row["user_id"] for row in rows]
    if len(user_ids) != len(set(user_ids)):
        errors.append("user_id must be unique")

    for index, row in enumerate(rows, start=2):
        prefix = f"row {index}"

        if row["variant"] not in VALID_VARIANTS:
            errors.append(f"{prefix}: invalid variant {row['variant']!r}")
        if row["device"] not in VALID_DEVICES:
            errors.append(f"{prefix}: invalid device {row['device']!r}")
        if row["acquisition_channel"] not in VALID_CHANNELS:
            errors.append(f"{prefix}: invalid acquisition_channel {row['acquisition_channel']!r}")

        try:
            datetime.fromisoformat(row["signup_date"])
        except ValueError:
            errors.append(f"{prefix}: signup_date must be ISO-8601")

        for field in BINARY_FIELDS:
            if row[field] not in {"0", "1"}:
                errors.append(f"{prefix}: {field} must be 0 or 1")

        if row["activated_7d"] == "1" and (
            row["connected_data"] != "1" or row["created_dashboard"] != "1"
        ):
            errors.append(f"{prefix}: activation requires connected_data and created_dashboard")

        if row["created_dashboard"] == "1" and row["connected_data"] != "1":
            errors.append(f"{prefix}: created_dashboard requires connected_data")

        try:
            revenue = float(row["revenue_30d"])
            if revenue < 0:
                errors.append(f"{prefix}: revenue_30d must be non-negative")
        except ValueError:
            errors.append(f"{prefix}: revenue_30d must be numeric")

        ttv = row["time_to_value_hours"]
        if row["activated_7d"] == "1":
            try:
                if float(ttv) <= 0:
                    errors.append(f"{prefix}: activated users require positive time_to_value_hours")
            except ValueError:
                errors.append(f"{prefix}: activated users require numeric time_to_value_hours")
        elif ttv != "":
            errors.append(f"{prefix}: non-activated users must not have time_to_value_hours")

    return errors


def validate_events(
    users: list[dict[str, str]],
    events: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    user_lookup = {row["user_id"]: row for row in users}
    event_ids = [row["event_id"] for row in events]
    if len(event_ids) != len(set(event_ids)):
        errors.append("event_id must be unique")

    by_user: dict[str, list[dict[str, str]]] = defaultdict(list)
    for index, event in enumerate(events, start=2):
        prefix = f"event row {index}"
        if event["user_id"] not in user_lookup:
            errors.append(f"{prefix}: unknown user_id {event['user_id']!r}")
            continue
        if event["event_name"] not in VALID_EVENTS:
            errors.append(f"{prefix}: invalid event_name {event['event_name']!r}")
        try:
            datetime.fromisoformat(event["event_ts"])
        except ValueError:
            errors.append(f"{prefix}: event_ts must be ISO-8601")
        if event["event_value"]:
            try:
                if float(event["event_value"]) < 0:
                    errors.append(f"{prefix}: event_value must be non-negative")
            except ValueError:
                errors.append(f"{prefix}: event_value must be numeric when present")
        by_user[event["user_id"]].append(event)

    for user_id, user in user_lookup.items():
        user_events = by_user.get(user_id, [])
        counts = Counter(event["event_name"] for event in user_events)

        if counts["signup"] != 1:
            errors.append(f"{user_id}: expected exactly one signup event")

        expected_presence = {
            "data_connected": user["connected_data"] == "1",
            "dashboard_created": user["created_dashboard"] == "1",
            "support_ticket_opened": user["support_ticket_7d"] == "1",
            "active_day_14": user["retained_14d"] == "1",
            "revenue_recorded": float(user["revenue_30d"]) > 0,
        }
        for event_name, expected in expected_presence.items():
            actual = counts[event_name] == 1
            if actual != expected:
                errors.append(
                    f"{user_id}: {event_name} event presence does not match user-level metric"
                )
            if counts[event_name] > 1:
                errors.append(f"{user_id}: {event_name} must occur at most once")

        if counts["signup"] == 1:
            signup_ts = datetime.fromisoformat(
                next(event["event_ts"] for event in user_events if event["event_name"] == "signup")
            )
            timed = {
                event["event_name"]: datetime.fromisoformat(event["event_ts"])
                for event in user_events
                if event["event_name"] != "signup"
            }

            if "data_connected" in timed and timed["data_connected"] <= signup_ts:
                errors.append(f"{user_id}: data_connected must occur after signup")
            if (
                "dashboard_created" in timed
                and "data_connected" in timed
                and timed["dashboard_created"] <= timed["data_connected"]
            ):
                errors.append(f"{user_id}: dashboard_created must occur after data_connected")
            if "dashboard_created" in timed:
                hours = (timed["dashboard_created"] - signup_ts).total_seconds() / 3600
                if user["activated_7d"] == "1" and not (0 < hours <= 7 * 24):
                    errors.append(f"{user_id}: activated dashboard event must occur within 7 days")
            if "support_ticket_opened" in timed:
                hours = (timed["support_ticket_opened"] - signup_ts).total_seconds() / 3600
                if not (0 < hours <= 7 * 24):
                    errors.append(f"{user_id}: support ticket event must occur within 7 days")
            if "active_day_14" in timed:
                hours = (timed["active_day_14"] - signup_ts).total_seconds() / 3600
                if not (14 * 24 <= hours <= 15 * 24):
                    errors.append(f"{user_id}: day-14 activity event must occur in the day-14 window")

    return errors


def read_raw(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic data-quality checks.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument("--events", type=Path, default=Path("artifacts/events.csv"))
    parser.add_argument("--expected-rows", type=int, default=12_000)
    args = parser.parse_args()

    users = read_raw(args.input)
    errors = validate_rows(users, expected_rows=args.expected_rows)
    if args.events.exists():
        errors.extend(validate_events(users, read_raw(args.events)))

    if errors:
        print("DATA QUALITY: FAIL")
        for error in errors[:25]:
            print(f"- {error}")
        if len(errors) > 25:
            print(f"- ... and {len(errors) - 25} more")
        raise SystemExit(1)

    event_note = f", {len(read_raw(args.events))} events" if args.events.exists() else ""
    print(f"DATA QUALITY: PASS ({args.expected_rows} users{event_note})")


if __name__ == "__main__":
    main()
