from __future__ import annotations

import unittest

from src.cuped import cuped_adjust_activation, pre_treatment_activation_score
from src.experiment import two_proportion_test
from src.generate_dataset import generate_users
from src.power import minimum_detectable_effect, sample_size_per_arm, two_sided_power


class AdvancedExperimentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_users(12_000, seed=20_260_808)
        cls.primary = two_proportion_test(cls.rows, "activated_7d")
        cls.n_control = sum(row["variant"] == "control" for row in cls.rows)
        cls.n_treatment = sum(row["variant"] == "treatment" for row in cls.rows)

    def test_power_increases_with_sample_size(self) -> None:
        small = two_sided_power(0.51, 0.025, 2_000, 2_000)
        large = two_sided_power(0.51, 0.025, 8_000, 8_000)
        self.assertGreater(large, small)

    def test_current_80pct_power_mde_is_about_2_55pp(self) -> None:
        mde = minimum_detectable_effect(
            self.primary.control_rate,
            self.n_control,
            self.n_treatment,
            target_power=0.80,
        )
        self.assertGreater(mde, 0.025)
        self.assertLess(mde, 0.026)

    def test_observed_effect_has_about_65pct_planning_power(self) -> None:
        observed_power = two_sided_power(
            self.primary.control_rate,
            self.primary.absolute_lift,
            self.n_control,
            self.n_treatment,
        )
        self.assertGreater(observed_power, 0.64)
        self.assertLess(observed_power, 0.66)

    def test_sample_size_planner_reaches_target(self) -> None:
        n = sample_size_per_arm(0.51, 0.02, target_power=0.80)
        self.assertGreater(n, 1_000)
        self.assertGreaterEqual(two_sided_power(0.51, 0.02, n, n), 0.80)
        self.assertLess(two_sided_power(0.51, 0.02, n - 1, n - 1), 0.80)

    def test_pre_treatment_score_is_variant_blind(self) -> None:
        control = {
            "variant": "control",
            "acquisition_channel": "organic",
            "device": "desktop",
        }
        treatment = {**control, "variant": "treatment"}
        self.assertEqual(
            pre_treatment_activation_score(control),
            pre_treatment_activation_score(treatment),
        )

    def test_cuped_adjustment_is_a_small_positive_sensitivity_gain(self) -> None:
        result = cuped_adjust_activation(self.rows)
        self.assertGreater(result.variance_reduction, 0.01)
        self.assertLess(result.variance_reduction, 0.03)
        self.assertGreater(result.adjusted_difference, 0)
        self.assertLess(result.p_value, 0.05)
        self.assertGreater(result.ci_low, 0)
        self.assertGreater(result.adjusted_difference, result.raw_difference)


if __name__ == "__main__":
    unittest.main()
