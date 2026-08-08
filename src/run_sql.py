from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def load_database(csv_path: Path, schema_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript(schema_path.read_text(encoding="utf-8"))

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            (
                row["user_id"],
                row["signup_date"],
                row["variant"],
                row["acquisition_channel"],
                row["device"],
                int(row["connected_data"]),
                int(row["created_dashboard"]),
                int(row["activated_7d"]),
                int(row["retained_14d"]),
                int(row["support_ticket_7d"]),
                None if row["time_to_value_hours"] == "" else float(row["time_to_value_hours"]),
                float(row["revenue_30d"]),
            )
            for row in reader
        ]

    connection.executemany(
        "INSERT INTO product_users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    return connection


def run_query(
    connection: sqlite3.Connection, query_path: Path
) -> tuple[list[str], list[tuple[object, ...]]]:
    cursor = connection.execute(query_path.read_text(encoding="utf-8"))
    columns = [description[0] for description in cursor.description]
    return columns, cursor.fetchall()


def format_table(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    widths = [len(column) for column in columns]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))

    def line(values: list[object]) -> str:
        return " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(values))

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join([line(list(columns)), separator, *(line(list(row)) for row in rows)])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute the portfolio SQL against the generated dataset."
    )
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    args = parser.parse_args()

    connection = load_database(args.input, args.sql_dir / "00_schema.sql")
    for query_path in sorted(args.sql_dir.glob("[0-9][1-9]_*.sql")):
        columns, rows = run_query(connection, query_path)
        print(f"\n## {query_path.name}\n")
        print(format_table(columns, rows))

    connection.close()


if __name__ == "__main__":
    main()
