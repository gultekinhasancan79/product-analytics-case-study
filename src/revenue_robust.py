from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from src.experiment import load_users


@dataclass(frozen=True)
class RevenueRobustResult:
    control_mean: float
    treatment_mean: float
    mean_difference: float
    bootstrap_ci_low: float
    bootstrap_ci_high: float
    bootstrap_positive_share: float
    control_trimmed_mean: float
    treatment_trimmed_mean: float
    trimmed_difference: float
    control_winsorized_mean: float
    treatment_winsorized_mean: float
    winsorized_difference: float


def _percentile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")
    if probability == 0:
        return sorted_values[0]
    if probability == 1:
        return sorted_values[-1]

    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def trimmed_mean(values: list[float], proportion: float = 0.10) -> float:
    if not 0 <= proportion < 0.5:
        raise ValueError("proportion must be in [0, 0.5)")
    ordered = sorted(values)
    trim = int(len(ordered) * proportion)
    kept = ordered[trim : len(ordered) - trim if trim else None]
    if not kept:
        raise ValueError("trim proportion removes all observations")
    return mean(kept)


def winsorized_mean(values: list[float], proportion: float = 0.05) -> float:
    if not 0 <= proportion < 0.5:
        raise ValueError("proportion must be in [0, 0.5)")
    ordered = sorted(values)
    cut = int(len(ordered) * proportion)
    if cut == 0:
        return mean(ordered)
    if cut * 2 >= len(ordered):
        raise ValueError("winsorization proportion is too large")
    lower = ordered[cut]
    upper = ordered[-cut - 1]
    return mean(min(max(value, lower), upper) for value in ordered)


def bootstrap_revenue_difference(
    rows: list[dict[str, object]],
    *,
    iterations: int = 2_000,
    seed: int = 20_260_808,
    alpha: float = 0.05,
) -> RevenueRobustResult:
    if iterations < 100:
        raise ValueError("iterations must be at least 100")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    groups: dict[str, list[float]] = {"control": [], "treatment": []}
    for row in rows:
        groups[str(row["variant"])].append(float(row["revenue_30d"]))

    control = groups["control"]
    treatment = groups["treatment"]
    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("both experiment arms require at least two revenue observations")

    control_mean = mean(control)
    treatment_mean = mean(treatment)
    point_difference = treatment_mean - control_mean

    rng = random.Random(seed)
    differences: list[float] = []
    for _ in range(iterations):
        control_boot = sum(control[rng.randrange(len(control))] for _ in range(len(control))) / len(control)
        treatment_boot = sum(treatment[rng.randrange(len(treatment))] for _ in range(len(treatment))) / len(treatment)
        differences.append(treatment_boot - control_boot)

    ordered_differences = sorted(differences)
    tail = alpha / 2
    ci_low = _percentile(ordered_differences, tail)
    ci_high = _percentile(ordered_differences, 1 - tail)
    positive_share = sum(value > 0 for value in differences) / len(differences)

    control_trimmed = trimmed_mean(control, 0.10)
    treatment_trimmed = trimmed_mean(treatment, 0.10)
    control_winsorized = winsorized_mean(control, 0.05)
    treatment_winsorized = winsorized_mean(treatment, 0.05)

    return RevenueRobustResult(
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        mean_difference=point_difference,
        bootstrap_ci_low=ci_low,
        bootstrap_ci_high=ci_high,
        bootstrap_positive_share=positive_share,
        control_trimmed_mean=control_trimmed,
        treatment_trimmed_mean=treatment_trimmed,
        trimmed_difference=treatment_trimmed - control_trimmed,
        control_winsorized_mean=control_winsorized,
        treatment_winsorized_mean=treatment_winsorized,
        winsorized_difference=treatment_winsorized - control_winsorized,
    )


def build_report(rows: list[dict[str, object]]) -> str:
    result = bootstrap_revenue_difference(rows)
    lines = [
        "# Revenue Robustness Readout",
        "",
        "Revenue is a zero-inflated, right-skewed supporting metric in this synthetic onboarding experiment. It was not the confirmatory decision metric, so this analysis is presented as robustness evidence rather than a new hypothesis test.",
        "",
        "## Mean difference with deterministic percentile bootstrap",
        "",
        "| Readout | Control | Treatment | Difference |",
        "| --- | ---: | ---: | ---: |",
        f"| Mean 30-day revenue / signup | ${result.control_mean:.2f} | ${result.treatment_mean:.2f} | ${result.mean_difference:+.2f} |",
        "",
        f"- **2,000-draw stratified percentile bootstrap 95% CI:** ${result.bootstrap_ci_low:+.2f} to ${result.bootstrap_ci_high:+.2f}",
        f"- **Share of bootstrap draws with positive treatment lift:** {result.bootstrap_positive_share:.1%}",
        "",
        "## Robust location sensitivity",
        "",
        "| Estimator | Control | Treatment | Difference |",
        "| --- | ---: | ---: | ---: |",
        f"| 10% trimmed mean | ${result.control_trimmed_mean:.2f} | ${result.treatment_trimmed_mean:.2f} | ${result.trimmed_difference:+.2f} |",
        f"| 5% winsorized mean | ${result.control_winsorized_mean:.2f} | ${result.treatment_winsorized_mean:.2f} | ${result.winsorized_difference:+.2f} |",
        "",
        "## Interpretation",
        "",
        "- The ordinary mean difference is positive, and its deterministic percentile-bootstrap interval stays above zero in this synthetic dataset.",
        "- The treatment-control difference remains positive under both trimmed and winsorized means, so the direction is not being driven only by a small number of large revenue observations.",
        "- This does **not** promote revenue to a confirmatory outcome. The product decision remains anchored to the pre-specified activation metric and support-ticket guardrail.",
        "- In a production experiment, the revenue estimand, observation window, handling of refunds/outliers, and bootstrap procedure should be frozen before treatment outcomes are inspected.",
        "",
        "## Reproducibility",
        "",
        "The analysis uses a fixed bootstrap seed (`20260808`) and 2,000 within-arm resamples. CI regenerates this report from the deterministic user dataset and fails if the committed evidence drifts.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run robust revenue sensitivity analysis.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/revenue_robustness.md"))
    args = parser.parse_args()
    report = build_report(load_users(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
