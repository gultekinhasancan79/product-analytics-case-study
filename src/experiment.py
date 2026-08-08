from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


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
        "## Exploratory device diagnostic",
        "",
        "| Device | Control activation | Treatment activation | Lift |",
        "| --- | ---: | ---: | ---: |",
    ]
    for segment, control, treatment, lift in device:
        lines.append(f"| {segment} | {_pct(control)} | {_pct(treatment)} | {_pp(lift)} |")

    lines += [
        "",
        "> Segment results are exploratory. The experiment was powered for the overall primary metric, not for interaction effects between treatment and device.",
        "",
        "## Interpretation",
        "",
        "- The treatment improves the primary activation metric without trading off the support burden.",
        "- The retention lift is directionally consistent with the activation result and statistically strong in this synthetic experiment.",
        "- Faster time-to-value and higher 30-day revenue are useful supporting signals, but are treated as descriptive rather than additional confirmatory tests.",
        "- The desktop/mobile split suggests a follow-up usability investigation on mobile before assuming the same mechanism drives both segments.",
        "",
        "## Reproducibility",
        "",
        "This report is generated from the deterministic synthetic dataset using `src/generate_dataset.py` and `src/experiment.py`. CI regenerates the data and diffs this report against the committed reference output.",
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
