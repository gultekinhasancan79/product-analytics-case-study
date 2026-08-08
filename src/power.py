from __future__ import annotations

import argparse
from dataclasses import dataclass
from statistics import NormalDist

_NORMAL = NormalDist()


@dataclass(frozen=True)
class PowerPlan:
    baseline_rate: float
    n_control: int
    n_treatment: int
    alpha: float
    target_power: float
    minimum_detectable_effect: float


def _validate_inputs(
    baseline_rate: float,
    n_control: int,
    n_treatment: int,
    alpha: float,
) -> None:
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if n_control < 2 or n_treatment < 2:
        raise ValueError("both arms require at least two observations")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")


def two_sided_power(
    baseline_rate: float,
    absolute_effect: float,
    n_control: int,
    n_treatment: int,
    *,
    alpha: float = 0.05,
) -> float:
    """Approximate power for a two-sided two-proportion z-test.

    The approximation models the treatment-minus-control rate difference under
    the alternative and evaluates the probability of crossing the two-sided
    null critical boundary. It is intended for experiment planning, not as a
    replacement for the analysis of observed outcomes.
    """
    _validate_inputs(baseline_rate, n_control, n_treatment, alpha)
    treatment_rate = baseline_rate + absolute_effect
    if not 0 < treatment_rate < 1:
        raise ValueError("baseline_rate + absolute_effect must be between 0 and 1")

    pooled_rate = (
        n_control * baseline_rate + n_treatment * treatment_rate
    ) / (n_control + n_treatment)
    null_se = (
        pooled_rate
        * (1 - pooled_rate)
        * (1 / n_control + 1 / n_treatment)
    ) ** 0.5
    alternative_se = (
        baseline_rate * (1 - baseline_rate) / n_control
        + treatment_rate * (1 - treatment_rate) / n_treatment
    ) ** 0.5

    critical = _NORMAL.inv_cdf(1 - alpha / 2) * null_se
    upper_tail = 1 - _NORMAL.cdf((critical - absolute_effect) / alternative_se)
    lower_tail = _NORMAL.cdf((-critical - absolute_effect) / alternative_se)
    return min(max(upper_tail + lower_tail, 0.0), 1.0)


def minimum_detectable_effect(
    baseline_rate: float,
    n_control: int,
    n_treatment: int,
    *,
    target_power: float = 0.80,
    alpha: float = 0.05,
) -> float:
    """Return the smallest positive absolute lift reaching target power."""
    _validate_inputs(baseline_rate, n_control, n_treatment, alpha)
    if not 0 < target_power < 1:
        raise ValueError("target_power must be between 0 and 1")

    lower = 0.0
    upper = min(1 - baseline_rate - 1e-9, 0.50)
    if two_sided_power(
        baseline_rate, upper, n_control, n_treatment, alpha=alpha
    ) < target_power:
        raise ValueError("target power is not reachable within the valid rate range")

    for _ in range(80):
        midpoint = (lower + upper) / 2
        power = two_sided_power(
            baseline_rate, midpoint, n_control, n_treatment, alpha=alpha
        )
        if power >= target_power:
            upper = midpoint
        else:
            lower = midpoint
    return upper


def sample_size_per_arm(
    baseline_rate: float,
    absolute_effect: float,
    *,
    target_power: float = 0.80,
    alpha: float = 0.05,
    max_per_arm: int = 10_000_000,
) -> int:
    """Return the smallest balanced per-arm sample reaching target power."""
    if not 0 < target_power < 1:
        raise ValueError("target_power must be between 0 and 1")
    if absolute_effect <= 0:
        raise ValueError("absolute_effect must be positive")

    lower, upper = 2, 4
    while upper <= max_per_arm and two_sided_power(
        baseline_rate, absolute_effect, upper, upper, alpha=alpha
    ) < target_power:
        lower = upper
        upper *= 2
    if upper > max_per_arm:
        raise ValueError("required sample exceeds max_per_arm")

    while lower + 1 < upper:
        midpoint = (lower + upper) // 2
        if two_sided_power(
            baseline_rate, absolute_effect, midpoint, midpoint, alpha=alpha
        ) >= target_power:
            upper = midpoint
        else:
            lower = midpoint
    return upper


def build_plan(
    baseline_rate: float,
    n_control: int,
    n_treatment: int,
    *,
    target_power: float = 0.80,
    alpha: float = 0.05,
) -> PowerPlan:
    return PowerPlan(
        baseline_rate=baseline_rate,
        n_control=n_control,
        n_treatment=n_treatment,
        alpha=alpha,
        target_power=target_power,
        minimum_detectable_effect=minimum_detectable_effect(
            baseline_rate,
            n_control,
            n_treatment,
            target_power=target_power,
            alpha=alpha,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan a binary A/B experiment.")
    parser.add_argument("--baseline", type=float, required=True)
    parser.add_argument("--n-control", type=int, required=True)
    parser.add_argument("--n-treatment", type=int, required=True)
    parser.add_argument("--effect", type=float)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    plan = build_plan(
        args.baseline,
        args.n_control,
        args.n_treatment,
        target_power=args.power,
        alpha=args.alpha,
    )
    print(f"baseline: {plan.baseline_rate:.4%}")
    print(f"allocation: {plan.n_control} control / {plan.n_treatment} treatment")
    print(f"target power: {plan.target_power:.0%} at alpha={plan.alpha:.3f}")
    print(f"MDE: {plan.minimum_detectable_effect * 100:.2f} pp")
    if args.effect is not None:
        observed_power = two_sided_power(
            args.baseline,
            args.effect,
            args.n_control,
            args.n_treatment,
            alpha=args.alpha,
        )
        print(f"power at {args.effect * 100:.2f} pp: {observed_power:.1%}")


if __name__ == "__main__":
    main()
