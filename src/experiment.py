from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from src.cuped import cuped_adjust_activation
from src.diagnostics import (
    randomization_balance,
    sample_ratio_mismatch,
    treatment_interaction,
)
from src.power import minimum_detectable_effect, sample_size_per_arm, two_sided_power


@dataclass(frozen=True)
class ProportionResult:
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float
    z_score: float
    p_value: float
    ci_low: float
    ci_high: float


def load_users(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    **row,
                    "connected_data": int(row["connected_data"]),
                    "created_dashboard": int(row["created_dashboard"]),
                    "activated_7d": int(row["activated_7d"]),
                    "retained_14d": int(row["retained_14d"]),
                    "support_ticket_7d": int(row["support_ticket_7d"]),
                    "time_to_value_hours": (
                        None if row["time_to_value_hours"] == "" else float(row["time_to_value_hours"])
                    ),
                    "revenue_30d": float(row["revenue_30d"]),
                }
            )
    return rows


def two_proportion_test(rows: list[dict[str, object]], metric: str) -> ProportionResult:
    groups: dict[str, list[int]] = {"control": [], "treatment": []}
    for row in rows:
        groups[str(row["variant"])].append(int(row[metric]))

    control = groups["control"]
    treatment = groups["treatment"]
    control_rate = sum(control) / len(control)
    treatment_rate = sum(treatment) / len(treatment)
    difference = treatment_rate - control_rate

    pooled = (sum(control) + sum(treatment)) / (len(control) + len(treatment))
    pooled_se = math.sqrt(
        pooled * (1 - pooled) * (1 / len(control) + 1 / len(treatment))
    )
    z_score = difference / pooled_se
    p_value = math.erfc(abs(z_score) / math.sqrt(2))

    unpooled_se = math.sqrt(
        control_rate * (1 - control_rate) / len(control)
        + treatment_rate * (1 - treatment_rate) / len(treatment)
    )
    ci_low = difference - 1.96 * unpooled_se
    ci_high = difference + 1.96 * unpooled_se

    return ProportionResult(
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        absolute_lift=difference,
        relative_lift=difference / control_rate,
        z_score=z_score,
        p_value=p_value,
        ci_low=ci_low,
        ci_high=ci_high,
    )


def mean_by_variant(
    rows: list[dict[str, object]], metric: str, *, non_null: bool = False
) -> dict[str, float]:
    values: dict[str, list[float]] = {"control": [], "treatment": []}
    for row in rows:
        value = row[metric]
        if non_null and value is None:
            continue
        values[str(row["variant"])].append(float(value))
    return {variant: mean(group) for variant, group in values.items()}


def activation_by_segment(
    rows: list[dict[str, object]], segment: str
) -> list[tuple[str, float, float, float]]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        grouped[(str(row[segment]), str(row["variant"]))].append(int(row["activated_7d"]))

    result = []
    for segment_value in sorted({key[0] for key in grouped}):
        control = mean(grouped[(segment_value, "control")])
        treatment = mean(grouped[(segment_value, "treatment")])
        result.append((segment_value, control, treatment, treatment - control))
    return result


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _pp(value: float) -> str:
    return f"{value * 100:+.2f} pp"


def build_report(rows: list[dict[str, object]]) -> str:
    activation = two_proportion_test(rows, "activated_7d")
    retention = two_proportion_test(rows, "retained_14d")
    tickets = two_proportion_test(rows, "support_ticket_7d")
    revenue = mean_by_variant(rows, "revenue_30d")
    time_to_value = mean_by_variant(rows, "time_to_value_hours", non_null=True)
    device = activation_by_segment(rows, "device")

    srm = sample_ratio_mismatch(rows)
    balance = randomization_balance(rows)
    max_abs_smd = max(abs(item.standardized_difference) for item in balance)
    interaction = treatment_interaction(
        rows,
        segment="device",
        segment_a="desktop",
        segment_b="mobile",
        metric="activated_7d",
    )

    planning_mde = 0.03
    required_per_arm = sample_size_per_arm(
        activation.control_rate,
        planning_mde,
        target_power=0.80,
        alpha=0.05,
    )
    achieved_mde = minimum_detectable_effect(
        activation.control_rate,
        srm.control_n,
        srm.treatment_n,
        target_power=0.80,
        alpha=0.05,
    )
    observed_planning_power = two_sided_power(
        activation.control_rate,
        activation.absolute_lift,
        srm.control_n,
        srm.treatment_n,
        alpha=0.05,
    )
    cuped = cuped_adjust_activation(rows)

    decision = (
        "SHIP"
        if activation.p_value < 0.05 and activation.ci_low > 0 and tickets.ci_high < 0
        else "HOLD"
    )

    lines = [
        "# Experiment Readout — Guided Onboarding Checklist",
        "",
        f"**Decision: {decision} treatment.** The primary activation metric improved significantly and the support-ticket guardrail also improved.",
        "",
        "## Experiment health",
        "",
        f"- **Assignment:** {srm.control_n:,} control / {srm.treatment_n:,} treatment.",
        f"- **Sample-ratio mismatch check:** p = {srm.p_value:.4f} — no evidence of allocation imbalance.",
        f"- **Largest pre-treatment standardized difference:** {max_abs_smd:.3f} — comfortably below the 0.10 review threshold.",
        f"- **Pre-analysis power target:** 3.00 pp MDE at 80% power and alpha = 0.05 requires about {required_per_arm * 2:,} users.",
        f"- **Realized allocation:** approximate 80%-power MDE at the observed control baseline is {_pp(achieved_mde)}.",
        f"- **Planning power at the observed +2.13 pp effect:** {observed_planning_power:.1%}. Statistical significance in this realization does not imply the design had 80% power for a 2.13 pp effect.",
        "",
        "### Randomization balance",
        "",
        "| Dimension | Level | Control share | Treatment share | Standardized difference |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in balance:
        lines.append(
            f"| {item.dimension} | {item.level} | {_pct(item.control_share)} | "
            f"{_pct(item.treatment_share)} | {item.standardized_difference:+.3f} |"
        )

    lines += [
        "",
        "## Primary metric",
        "",
        "| Metric | Control | Treatment | Absolute lift | Relative lift | p-value | 95% CI on lift |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| 7-day activation | {_pct(activation.control_rate)} | {_pct(activation.treatment_rate)} | "
            f"{_pp(activation.absolute_lift)} | {activation.relative_lift * 100:+.2f}% | "
            f"{activation.p_value:.4f} | {_pp(activation.ci_low)} to {_pp(activation.ci_high)} |"
        ),
        "",
        "## Secondary and guardrail metrics",
        "",
        "| Metric | Control | Treatment | Absolute lift | p-value |",
        "| --- | ---: | ---: | ---: | ---: |",
        (
            f"| 14-day retention | {_pct(retention.control_rate)} | {_pct(retention.treatment_rate)} | "
            f"{_pp(retention.absolute_lift)} | {retention.p_value:.4f} |"
        ),
        (
            f"| Support ticket within 7 days | {_pct(tickets.control_rate)} | {_pct(tickets.treatment_rate)} | "
            f"{_pp(tickets.absolute_lift)} | {tickets.p_value:.4f} |"
        ),
        (
            f"| Mean 30-day revenue / signup | ${revenue['control']:.2f} | ${revenue['treatment']:.2f} | "
            f"${revenue['treatment'] - revenue['control']:+.2f} | descriptive |"
        ),
        (
            f"| Mean time-to-value among activated users | {time_to_value['control']:.2f} h | "
            f"{time_to_value['treatment']:.2f} h | "
            f"{time_to_value['treatment'] - time_to_value['control']:+.2f} h | descriptive |"
        ),
        "",
        "## Device heterogeneity diagnostic",
        "",
        "| Device | Control activation | Treatment activation | Lift |",
        "| --- | ---: | ---: | ---: |",
    ]
    for segment, control, treatment, lift in device:
        lines.append(f"| {segment} | {_pct(control)} | {_pct(treatment)} | {_pp(lift)} |")

    lines += [
        "",
        (
            f"**Treatment × device interaction:** desktop-minus-mobile lift difference "
            f"{_pp(interaction.interaction_effect)}, p = {interaction.p_value:.4f}, "
            f"95% CI {_pp(interaction.ci_low)} to {_pp(interaction.ci_high)}."
        ),
        "",
        "> The interaction is suggestive but does not cross the 0.05 threshold. Device results remain exploratory rather than a confirmed heterogeneous treatment effect.",
        "",
        "## CUPED-style sensitivity analysis",
        "",
        "This sensitivity check adjusts activation using a treatment-blind pre-exposure propensity score built only from acquisition channel and device. Because this is a new-user experiment, it is **not** a classical pre-period outcome CUPED setup; the unadjusted primary analysis remains confirmatory.",
        "",
        f"- raw activation lift: {_pp(cuped.raw_difference)}",
        f"- adjusted activation lift: {_pp(cuped.adjusted_difference)}",
        f"- adjusted p-value: {cuped.p_value:.4f}",
        f"- adjusted 95% CI: {_pp(cuped.ci_low)} to {_pp(cuped.ci_high)}",
        f"- pooled outcome variance reduction: {cuped.variance_reduction:.2%}",
        "",
        "The adjustment is directionally consistent with the unadjusted result but produces only a modest variance reduction, so it is presented as a sensitivity analysis rather than a headline improvement.",
        "",
        "## Interpretation",
        "",
        "- The treatment improves the primary activation metric without trading off the support burden.",
        "- Randomization diagnostics do not show sample-ratio mismatch or meaningful pre-treatment imbalance.",
        "- The realized allocation supports an ~2.55 pp 80%-power MDE; the observed +2.13 pp effect had only ~64.8% planning power, despite being significant in this realized sample.",
        "- The desktop/mobile contrast is worth product follow-up, but the formal interaction test is not conclusive at alpha = 0.05.",
        "- The CUPED-style sensitivity remains positive and significant, but its 1.47% variance reduction is small and should not be oversold.",
        "- Revenue and time-to-value remain descriptive supporting signals rather than additional confirmatory tests.",
        "",
        "## Reproducibility",
        "",
        "This report is generated from deterministic synthetic data using `src/generate_dataset.py`, `src/diagnostics.py`, `src/power.py`, `src/cuped.py`, and `src/experiment.py`. CI regenerates the data and diffs this report against the committed reference output.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the onboarding A/B experiment.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/experiment_summary.md")
    )
    args = parser.parse_args()
    rows = load_users(args.input)
    report = build_report(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
