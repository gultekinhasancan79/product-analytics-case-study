import unittest

from src.exposure_demo import analyze_exposure, generate_exposure_demo


class ExposureTests(unittest.TestCase):
    def test_reproducible(self):
        first = generate_exposure_demo(500, seed=123)
        second = generate_exposure_demo(500, seed=123)
        self.assertEqual(first, second)

    def test_assignment_difference_is_positive(self):
        result = analyze_exposure(generate_exposure_demo(50_000, seed=20_260_808))
        self.assertGreater(result.itt_effect, 0.03)
        self.assertLess(result.itt_effect, 0.07)
        self.assertGreater(result.treatment_exposure_rate, 0.70)
        self.assertLess(result.treatment_exposure_rate, 0.85)

    def test_exposed_subset_difference_is_larger(self):
        result = analyze_exposure(generate_exposure_demo(50_000, seed=20_260_808))
        self.assertGreater(result.naive_exposed_vs_control_effect, result.itt_effect)

    def test_ratio_estimate_is_near_simulated_effect(self):
        result = analyze_exposure(generate_exposure_demo(100_000, seed=20_260_808))
        self.assertGreater(result.wald_treatment_on_treated_effect, 0.05)
        self.assertLess(result.wald_treatment_on_treated_effect, 0.08)


if __name__ == "__main__":
    unittest.main()
