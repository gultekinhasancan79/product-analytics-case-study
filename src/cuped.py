from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from statistics import mean, variance
from pathlib import Path

from src.experiment import load_users

_CHANNEL_CONNECT = {
    "organic": 0.02,
    "paid_search": -0.03,
    "partner": 0.04,
    "referral": 0.03,
}
_CHANNEL_DASHBOARD = {
    "organic": 0.00,
    "paid_search": -0.02,
    "partner": 0.03,
    "referral": 0.02,
}


@dataclass(frozen=True)
class CupedResult:
    theta: float
    control_score_mean: float
    treatment_score_mean: float
    raw_difference: float
    adjusted_difference: float
    adjusted_standard_error: float
    p_value: float
    ci_low: float
    ci_high: float
    variance_reduction: float


def pre_treatment_activation_score(row: dict[str, object]) -> float:
    """Build a treatment-blind activation propensity from pre-exposure fields.

    This score deliberately excludes the randomized variant and all post-exposure
    outcomes. In a real production experiment it would be preferable to freeze
    this score before launch rather than reconstruct it after the fact.
    """
    channel = str(row["acquisition_channel"])
    device = str(row["device"])
    connect = (
        0.70
        + _CHANNEL_CONNECT[channel]
        + (0.03 if device == "desktop" else -0.03)
    )
    dashboard = (
        0.68
        + _CHANNEL_DASHBOARD[channel]
        + (0.04 if device == "desktop" else -0.04)
    )
    return connect * dashboard


def _sample_covariance(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("covariance requires equal-length samples with at least two rows")
    x_mean = mean(xs)
    y_mean = mean(ys)
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / (len(xs) - 1)


def cuped_adjust_activation(rows: list[dict[str, object]]) -> CupedResult:
    """Apply a CUPED-style adjustment to the binary activation outcome.

    Classical CUPED commonly uses a pre-period version of the outcome. This
    onboarding experiment has new users, so no genuine pre-period activation
    measure exists. Instead, the demonstration uses a treatment-blind score
    constructed only from pre-exposure device and acquisition-channel fields.
    The unadjusted primary analysis remains the confirmatory result.
    """
    if len(rows) < 4:
        raise ValueError("CUPED adjustment requires at least four rows")

    scores = [pre_treatment_activation_score(row) for row in rows]
    outcomes = [float(row["activated_7d"]) for row in rows]
    score_variance = variance(scores)
    if score_variance == 0:
        raise ValueError("pre-treatment covariate has zero variance")

    theta = _sample_covariance(scores, outcomes) / score_variance
    score_mean = mean(scores)
    adjusted = [
        outcome - theta * (score - score_mean)
        for outcome, score in zip(outcomes, scores)
    ]

    raw_control = [
        outcome for outcome, row in zip(outcomes, rows) if row["variant"] == "control"
    ]
    raw_treatment = [
        outcome for outcome, row in zip(outcomes, rows) if row["variant"] == "treatment"
    ]
    adjusted_control = [
        value for value, row in zip(adjusted, rows) if row["variant"] == "control"
    ]
    adjusted_treatment = [
        value for value, row in zip(adjusted, rows) if row["variant"] == "treatment"
    ]
    control_scores = [
        score for score, row in zip(scores, rows) if row["variant"] == "control"
    ]
    treatment_scores = [
        score for score, row in zip(scores, rows) if row["variant"] == "treatment"
    ]

    raw_difference = mean(raw_treatment) - mean(raw_control)
    adjusted_difference = mean(adjusted_treatment) - mean(adjusted_control)
    adjusted_se = math.sqrt(
        variance(adjusted_control) / len(adjusted_control)
        + variance(adjusted_treatment) / len(adjusted_treatment)
    )
    z_score = adjusted_difference / adjusted_se
    p_value = math.erfc(abs(z_score) / math.sqrt(2))
    critical = 1.96 * adjusted_se

    raw_variance = variance(outcomes)
    adjusted_variance = variance(adjusted)
    variance_reduction = 1 - adjusted_variance / raw_variance

    return CupedResult(
        theta=theta,
        control_score_mean=mean(control_scores),
        treatment_score_mean=mean(treatment_scores),
        raw_difference=raw_difference,
        adjusted_difference=adjusted_difference,
        adjusted_standard_error=adjusted_se,
        p_value=p_value,
        ci_low=adjusted_difference - critical,
        ci_high=adjusted_difference + critical,
        variance_reduction=variance_reduction,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CUPED-style activation adjustment.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    args = parser.parse_args()

    result = cuped_adjust_activation(load_users(args.input))
    print(f"theta: {result.theta:.4f}")
    print(
        "pre-treatment score balance: "
        f"{result.control_score_mean:.5f} control / "
        f"{result.treatment_score_mean:.5f} treatment"
    )
    print(f"raw lift: {result.raw_difference * 100:+.2f} pp")
    print(f"adjusted lift: {result.adjusted_difference * 100:+.2f} pp")
    print(
        "adjusted 95% CI: "
        f"{result.ci_low * 100:+.2f} to {result.ci_high * 100:+.2f} pp"
    )
    print(f"adjusted p-value: {result.p_value:.4f}")
    print(f"pooled outcome variance reduction: {result.variance_reduction:.2%}")


if __name__ == "__main__":
    main()
