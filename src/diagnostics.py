from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist


@dataclass(frozen=True)
class SRMResult:
    control_n: int
    treatment_n: int
    expected_treatment_share: float
    z_score: float
    p_value: float


@dataclass(frozen=True)
class BalanceResult:
    dimension: str
    level: str
    control_share: float
    treatment_share: float
    standardized_difference: float


@dataclass(frozen=True)
class InteractionResult:
    segment_a: str
    segment_b: str
    lift_a: float
    lift_b: float
    interaction_effect: float
    z_score: float
    p_value: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True)
class PowerPlan:
    baseline_rate: float
    target_mde: float
    alpha: float
    power: float
    required_per_variant: int
    required_total: int
    achieved_mde: float


def _two_sided_p(z_score: float) -> float:
    return math.erfc(abs(z_score) / math.sqrt(2))


def sample_ratio_mismatch(
    rows: list[dict[str, object]], expected_treatment_share: float = 0.5
) -> SRMResult:
    control_n = sum(str(row["variant"]) == "control" for row in rows)
    treatment_n = sum(str(row["variant"]) == "treatment" for row in rows)
    total = control_n + treatment_n
    expected = total * expected_treatment_share
    standard_error = math.sqrt(total * expected_treatment_share * (1 - expected_treatment_share))
    z_score = (treatment_n - expected) / standard_error
    return SRMResult(
        control_n=control_n,
        treatment_n=treatment_n,
        expected_treatment_share=expected_treatment_share,
        z_score=z_score,
        p_value=_two_sided_p(z_score),
    )


def _binary_smd(control_share: float, treatment_share: float) -> float:
    pooled_variance = (
        control_share * (1 - control_share)
        + treatment_share * (1 - treatment_share)
    ) / 2
    if pooled_variance == 0:
        return 0.0
    return (treatment_share - control_share) / math.sqrt(pooled_variance)


def randomization_balance(rows: list[dict[str, object]]) -> list[BalanceResult]:
    specs = [
        ("device", "desktop"),
        ("acquisition_channel", "organic"),
        ("acquisition_channel", "paid_search"),
        ("acquisition_channel", "partner"),
        ("acquisition_channel", "referral"),
    ]
    result: list[BalanceResult] = []
    control = [row for row in rows if str(row["variant"]) == "control"]
    treatment = [row for row in rows if str(row["variant"]) == "treatment"]

    for dimension, level in specs:
        control_share = sum(str(row[dimension]) == level for row in control) / len(control)
        treatment_share = sum(str(row[dimension]) == level for row in treatment) / len(treatment)
        result.append(
            BalanceResult(
                dimension=dimension,
                level=level,
                control_share=control_share,
                treatment_share=treatment_share,
                standardized_difference=_binary_smd(control_share, treatment_share),
            )
        )
    return result


def treatment_interaction(
    rows: list[dict[str, object]],
    *,
    segment: str,
    segment_a: str,
    segment_b: str,
    metric: str,
) -> InteractionResult:
    cells: dict[tuple[str, str], tuple[float, int]] = {}
    for segment_value in (segment_a, segment_b):
        for variant in ("control", "treatment"):
            group = [
                row
                for row in rows
                if str(row[segment]) == segment_value and str(row["variant"]) == variant
            ]
            rate = sum(int(row[metric]) for row in group) / len(group)
            cells[(segment_value, variant)] = (rate, len(group))

    a_control, a_control_n = cells[(segment_a, "control")]
    a_treatment, a_treatment_n = cells[(segment_a, "treatment")]
    b_control, b_control_n = cells[(segment_b, "control")]
    b_treatment, b_treatment_n = cells[(segment_b, "treatment")]

    lift_a = a_treatment - a_control
    lift_b = b_treatment - b_control
    interaction_effect = lift_a - lift_b

    variance = (
        a_treatment * (1 - a_treatment) / a_treatment_n
        + a_control * (1 - a_control) / a_control_n
        + b_treatment * (1 - b_treatment) / b_treatment_n
        + b_control * (1 - b_control) / b_control_n
    )
    standard_error = math.sqrt(variance)
    z_score = interaction_effect / standard_error
    ci_low = interaction_effect - 1.96 * standard_error
    ci_high = interaction_effect + 1.96 * standard_error

    return InteractionResult(
        segment_a=segment_a,
        segment_b=segment_b,
        lift_a=lift_a,
        lift_b=lift_b,
        interaction_effect=interaction_effect,
        z_score=z_score,
        p_value=_two_sided_p(z_score),
        ci_low=ci_low,
        ci_high=ci_high,
    )


def required_sample_size(
    baseline_rate: float,
    absolute_mde: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
) -> tuple[int, int]:
    treatment_rate = baseline_rate + absolute_mde
    if not (0 < baseline_rate < 1 and 0 < treatment_rate < 1):
        raise ValueError("baseline_rate and baseline_rate + absolute_mde must be in (0, 1)")
    if absolute_mde <= 0:
        raise ValueError("absolute_mde must be positive")

    normal = NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha / 2)
    z_power = normal.inv_cdf(power)
    pooled = (baseline_rate + treatment_rate) / 2

    numerator = (
        z_alpha * math.sqrt(2 * pooled * (1 - pooled))
        + z_power
        * math.sqrt(
            baseline_rate * (1 - baseline_rate)
            + treatment_rate * (1 - treatment_rate)
        )
    ) ** 2
    per_variant = math.ceil(numerator / (absolute_mde**2))
    return per_variant, per_variant * 2


def minimum_detectable_effect(
    baseline_rate: float,
    total_sample_size: int,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    if total_sample_size < 4:
        raise ValueError("total_sample_size must be at least 4")

    low, high = 1e-6, min(0.25, 0.999 - baseline_rate)
    for _ in range(80):
        mid = (low + high) / 2
        _, required_total = required_sample_size(
            baseline_rate, mid, alpha=alpha, power=power
        )
        if required_total > total_sample_size:
            low = mid
        else:
            high = mid
    return high


def power_plan(
    baseline_rate: float,
    total_sample_size: int,
    *,
    target_mde: float = 0.03,
    alpha: float = 0.05,
    power: float = 0.80,
) -> PowerPlan:
    required_per_variant, required_total = required_sample_size(
        baseline_rate, target_mde, alpha=alpha, power=power
    )
    return PowerPlan(
        baseline_rate=baseline_rate,
        target_mde=target_mde,
        alpha=alpha,
        power=power,
        required_per_variant=required_per_variant,
        required_total=required_total,
        achieved_mde=minimum_detectable_effect(
            baseline_rate, total_sample_size, alpha=alpha, power=power
        ),
    )
