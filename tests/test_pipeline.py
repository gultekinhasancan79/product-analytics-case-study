from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.data_quality import read_raw, validate_rows
from src.experiment import build_report, load_users, two_proportion_test
from src.generate_dataset import generate_users, write_csv
from src.run_sql import load_database, run_query


class ProductAnalyticsPipelineTests(unittest.TestCase):
    def _dataset(self, rows: int = 12_000) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / "users.csv"
        write_csv(generate_users(rows, seed=20_260_808), path)
        return temp, path

    def test_generator_is_deterministic(self) -> None:
        first = generate_users(20, seed=123)
        second = generate_users(20, seed=123)
        self.assertEqual(first, second)
        self.assertEqual(len({row["user_id"] for row in first}), 20)

    def test_generated_dataset_passes_quality_checks(self) -> None:
        temp, path = self._dataset(500)
        try:
            errors = validate_rows(read_raw(path), expected_rows=500)
            self.assertEqual(errors, [])
        finally:
            temp.cleanup()

    def test_quality_checks_reject_impossible_activation(self) -> None:
        row = generate_users(1, seed=42)[0]
        row["connected_data"] = 0
        row["created_dashboard"] = 0
        row["activated_7d"] = 1

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.csv"
            write_csv([row], path)
            errors = validate_rows(read_raw(path), expected_rows=1)

        self.assertTrue(any("activation requires" in error for error in errors))

    def test_primary_experiment_result_is_positive_and_significant(self) -> None:
        temp, path = self._dataset()
        try:
            rows = load_users(path)
            result = two_proportion_test(rows, "activated_7d")
        finally:
            temp.cleanup()

        self.assertAlmostEqual(result.control_rate, 0.5116201859, places=8)
        self.assertAlmostEqual(result.treatment_rate, 0.5329651941, places=8)
        self.assertGreater(result.absolute_lift, 0)
        self.assertLess(result.p_value, 0.05)
        self.assertGreater(result.ci_low, 0)

    def test_report_contains_ship_decision_and_guardrail(self) -> None:
        temp, path = self._dataset()
        try:
            report = build_report(load_users(path))
        finally:
            temp.cleanup()

        self.assertIn("Decision: SHIP treatment", report)
        self.assertIn("Support ticket within 7 days", report)
        self.assertIn("exploratory", report.lower())

    def test_sql_queries_execute_against_generated_data(self) -> None:
        temp, path = self._dataset(1000)
        try:
            sql_dir = Path(__file__).resolve().parents[1] / "sql"
            connection = load_database(path, sql_dir / "00_schema.sql")
            for query in sorted(sql_dir.glob("[0-9][1-9]_*.sql")):
                columns, rows = run_query(connection, query)
                self.assertTrue(columns)
                self.assertTrue(rows)
            connection.close()
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
