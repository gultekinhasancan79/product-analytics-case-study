from __future__ import annotations

import unittest

from src.generate_dataset import generate_users
from src.revenue_robust import (
    bootstrap_revenue_difference,
    trimmed_mean,
    winsorized_mean,
)


class RevenueRobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_users(12_000, seed=20_260_808)

    def test_bootstrap_is_deterministic_for_fixed_seed(self) -> None:
        first = bootstrap_revenue_difference(self.rows, iterations=200, seed=123)
        second = bootstrap_revenue_difference(self.rows, iterations=200, seed=123)
        self.assertEqual(first, second)

    def test_revenue_bootstrap_interval_is_positive(self) -> None:
        result = bootstrap_revenue_difference(self.rows, iterations=500, seed=20_260_808)
        self.assertGreater(result.mean_difference, 1.0)
        self.assertLess(result.mean_difference, 2.0)
        self.assertGreater(result.bootstrap_ci_low, 0)
        self.assertGreater(result.bootstrap_ci_high, result.bootstrap_ci_low)
        self.assertGreater(result.bootstrap_positive_share, 0.95)

    def test_robust_estimators_preserve_positive_direction(self) -> None:
        control = [float(row["revenue_30d"]) for row in self.rows if row["variant"] == "control"]
        treatment = [float(row["revenue_30d"]) for row in self.rows if row["variant"] == "treatment"]
        self.assertGreater(trimmed_mean(treatment) - trimmed_mean(control), 0)
        self.assertGreater(winsorized_mean(treatment) - winsorized_mean(control), 0)

    def test_trimmed_mean_reduces_single_extreme_outlier_influence(self) -> None:
        baseline = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 1000.0]
        self.assertLess(trimmed_mean(baseline, 0.10), sum(baseline) / len(baseline))


if __name__ == "__main__":
    unittest.main()
