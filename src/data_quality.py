from __future__ import annotations

import argparse
import csv
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


def validate_rows(rows: list[dict[str, str]], expected_rows: int | None = None) -> list[str]:
    errors: list[str] = []

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


def read_raw(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic data-quality checks.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument("--expected-rows", type=int, default=12_000)
    args = parser.parse_args()

    errors = validate_rows(read_raw(args.input), expected_rows=args.expected_rows)
    if errors:
        print("DATA QUALITY: FAIL")
        for error in errors[:25]:
            print(f"- {error}")
        if len(errors) > 25:
            print(f"- ... and {len(errors) - 25} more")
        raise SystemExit(1)

    print(f"DATA QUALITY: PASS ({args.expected_rows} rows)")


if __name__ == "__main__":
    main()
