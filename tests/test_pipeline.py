from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.data_quality import read_raw, validate_events, validate_rows
from src.diagnostics import (
    power_plan,
    randomization_balance,
    sample_ratio_mismatch,
    treatment_interaction,
)
from src.experiment import build_report, load_users, two_proportion_test
from src.generate_dataset import generate_users, write_csv
from src.generate_events import generate_events, write_events
from src.run_sql import load_database, run_query


class ProductAnalyticsPipelineTests(unittest.TestCase):
    def _dataset(
        self, rows: int = 12_000
    ) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temp = tempfile.TemporaryDirectory()
        users_path = Path(temp.name) / "users.csv"
        events_path = Path(temp.name) / "events.csv"
        write_csv(generate_users(rows, seed=20_260_808), users_path)
        raw_users = read_raw(users_path)
        write_events(generate_events(raw_users, seed=20_260_808), events_path)
        return temp, users_path, events_path

    def test_generator_is_deterministic(self) -> None:
        first = generate_users(20, seed=123)
        second = generate_users(20, seed=123)
        self.assertEqual(first, second)
        self.assertEqual(len({row["user_id"] for row in first}), 20)

    def test_event_generator_is_deterministic(self) -> None:
        temp, users_path, _ = self._dataset(50)
        try:
            users = read_raw(users_path)
            first = generate_events(users, seed=123)
            second = generate_events(users, seed=123)
            self.assertEqual(first, second)
            self.assertEqual(len({row["event_id"] for row in first}), len(first))
        finally:
            temp.cleanup()

    def test_generated_datasets_pass_quality_checks(self) -> None:
        temp, users_path, events_path = self._dataset(500)
        try:
            users = read_raw(users_path)
            errors = validate_rows(users, expected_rows=500)
            errors += validate_events(users, read_raw(events_path))
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
        temp, users_path, _ = self._dataset()
        try:
            rows = load_users(users_path)
            result = two_proportion_test(rows, "activated_7d")
        finally:
            temp.cleanup()

        self.assertAlmostEqual(result.control_rate, 0.5116201859, places=8)
        self.assertAlmostEqual(result.treatment_rate, 0.5329651941, places=8)
        self.assertGreater(result.absolute_lift, 0)
        self.assertLess(result.p_value, 0.05)
        self.assertGreater(result.ci_low, 0)

    def test_srm_and_randomization_balance_are_healthy(self) -> None:
        temp, users_path, _ = self._dataset()
        try:
            rows = load_users(users_path)
            srm = sample_ratio_mismatch(rows)
            balance = randomization_balance(rows)
        finally:
            temp.cleanup()

        self.assertGreater(srm.p_value, 0.05)
        self.assertLess(max(abs(item.standardized_difference) for item in balance), 0.10)

    def test_power_plan_and_realized_mde(self) -> None:
        temp, users_path, _ = self._dataset()
        try:
            rows = load_users(users_path)
            activation = two_proportion_test(rows, "activated_7d")
            plan = power_plan(activation.control_rate, len(rows), target_mde=0.03)
        finally:
            temp.cleanup()

        self.assertLessEqual(plan.required_total, 12_000)
        self.assertGreater(plan.achieved_mde, 0.02)
        self.assertLess(plan.achieved_mde, 0.03)

    def test_device_interaction_is_reported_but_not_confirmed(self) -> None:
        temp, users_path, _ = self._dataset()
        try:
            rows = load_users(users_path)
            interaction = treatment_interaction(
                rows,
                segment="device",
                segment_a="desktop",
                segment_b="mobile",
                metric="activated_7d",
            )
        finally:
            temp.cleanup()

        self.assertGreater(interaction.interaction_effect, 0)
        self.assertGreater(interaction.p_value, 0.05)
        self.assertLess(interaction.p_value, 0.10)
        self.assertLess(interaction.ci_low, 0)
        self.assertGreater(interaction.ci_high, 0)

    def test_report_contains_health_power_and_interaction_sections(self) -> None:
        temp, users_path, _ = self._dataset()
        try:
            report = build_report(load_users(users_path))
        finally:
            temp.cleanup()

        self.assertIn("Decision: SHIP treatment", report)
        self.assertIn("Sample-ratio mismatch check", report)
        self.assertIn("Pre-analysis power target", report)
        self.assertIn("Treatment × device interaction", report)

    def test_sql_queries_execute_against_generated_data(self) -> None:
        temp, users_path, events_path = self._dataset(1000)
        try:
            sql_dir = Path(__file__).resolve().parents[1] / "sql"
            connection = load_database(
                users_path,
                sql_dir / "00_schema.sql",
                events_path=events_path,
            )
            for query in sorted(sql_dir.glob("[0-9][1-9]_*.sql")):
                columns, rows = run_query(connection, query)
                self.assertTrue(columns)
                self.assertTrue(rows)
            connection.close()
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
