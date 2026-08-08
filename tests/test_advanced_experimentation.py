from __future__ import annotations

import unittest
from pathlib import Path

from src.cuped import cuped_adjust_activation, pre_treatment_activation_score
from src.diagnostics import minimum_detectable_effect, required_sample_size, two_sided_power
from src.execute_notebook import execute_notebook
from src.experiment import two_proportion_test
from src.generate_dataset import generate_users


class AdvancedExperimentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_users(12_000, seed=20_260_808)
        cls.primary = two_proportion_test(cls.rows, "activated_7d")
        cls.n_control = sum(row["variant"] == "control" for row in cls.rows)
        cls.n_treatment = sum(row["variant"] == "treatment" for row in cls.rows)

    def test_realized_80pct_power_mde_is_about_2_55pp(self) -> None:
        mde = minimum_detectable_effect(
            self.primary.control_rate,
            len(self.rows),
            power=0.80,
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

    def test_2pp_effect_requires_about_9800_users_per_arm(self) -> None:
        per_arm, total = required_sample_size(
            self.primary.control_rate,
            0.02,
            power=0.80,
        )
        self.assertGreater(per_arm, 9_700)
        self.assertLess(per_arm, 9_900)
        self.assertEqual(total, per_arm * 2)

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

    def test_cuped_adjustment_reduces_variance_and_keeps_positive_effect(self) -> None:
        result = cuped_adjust_activation(self.rows)
        self.assertGreater(result.variance_reduction, 0.01)
        self.assertLess(result.variance_reduction, 0.03)
        self.assertGreater(result.adjusted_difference, 0)
        self.assertLess(result.p_value, 0.05)
        self.assertGreater(result.ci_low, 0)

    def test_notebook_code_cells_execute(self) -> None:
        notebook = Path(__file__).resolve().parents[1] / "notebooks" / "advanced_experimentation.ipynb"
        self.assertEqual(execute_notebook(notebook), 3)


if __name__ == "__main__":
    unittest.main()
