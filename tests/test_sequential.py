import unittest

from src.sequential import simulate_peeking_risk


class SequentialAnalysisTests(unittest.TestCase):
    def test_reproducible(self):
        a = simulate_peeking_risk(trials=200, seed=123)
        b = simulate_peeking_risk(trials=200, seed=123)
        self.assertEqual(a, b)

    def test_repeated_looks_change_error_rate(self):
        result = simulate_peeking_risk(trials=500, seed=20_260_808)
        self.assertGreater(result.naive_any_look_false_positive_rate, 0.10)
        self.assertGreater(
            result.naive_any_look_false_positive_rate,
            result.final_only_false_positive_rate,
        )

    def test_adjusted_threshold_is_more_conservative(self):
        result = simulate_peeking_risk(trials=500, seed=20_260_808)
        self.assertLess(
            result.bonferroni_any_look_false_positive_rate,
            result.naive_any_look_false_positive_rate,
        )


if __name__ == "__main__":
    unittest.main()
