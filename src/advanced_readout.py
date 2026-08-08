from __future__ import annotations

import argparse
from pathlib import Path

from src.cuped import cuped_adjust_activation
from src.diagnostics import minimum_detectable_effect, required_sample_size, two_sided_power
from src.experiment import load_users, two_proportion_test


def build_advanced_report(rows: list[dict[str, object]]) -> str:
    primary = two_proportion_test(rows, "activated_7d")
    n_control = sum(str(row["variant"]) == "control" for row in rows)
    n_treatment = sum(str(row["variant"]) == "treatment" for row in rows)

    mde = minimum_detectable_effect(primary.control_rate, len(rows), power=0.80)
    observed_power = two_sided_power(
        primary.control_rate,
        primary.absolute_lift,
        n_control,
        n_treatment,
    )
    sample_for_2pp, _ = required_sample_size(
        primary.control_rate,
        0.02,
        power=0.80,
    )
    cuped = cuped_adjust_activation(rows)

    return "\n".join(
        [
            "# Advanced Experimentation Readout",
            "",
            "## Power and MDE",
            "",
            f"- Allocation: **{n_control:,} control / {n_treatment:,} treatment**",
            f"- Control activation baseline: **{primary.control_rate:.2%}**",
            f"- Observed raw lift: **{primary.absolute_lift * 100:+.2f} pp**",
            f"- 80% power MDE at alpha=0.05: **{mde * 100:.2f} pp**",
            f"- Approximate planning power at the observed lift: **{observed_power:.1%}**",
            f"- Balanced sample needed for an 80%-powered +2.00 pp effect: **{sample_for_2pp:,} users / arm**",
            "",
            "The observed +2.13 pp lift is smaller than the design's approximately +2.55 pp 80%-power MDE. A significant realization is still possible below the MDE; the implication is that this sample would not detect an effect of this size with 80% probability across repeated experiments.",
            "",
            "## CUPED-style sensitivity analysis",
            "",
            "This new-user onboarding experiment does not have a genuine pre-period activation outcome. The adjustment therefore uses a treatment-blind activation propensity constructed only from **acquisition channel and device**, both known before exposure.",
            "",
            f"- CUPED theta: **{cuped.theta:.4f}**",
            f"- Pre-treatment score mean: **{cuped.control_score_mean:.5f} control / {cuped.treatment_score_mean:.5f} treatment**",
            f"- Pooled outcome variance reduction: **{cuped.variance_reduction:.2%}**",
            f"- Raw activation lift: **{cuped.raw_difference * 100:+.2f} pp**",
            f"- Adjusted activation lift: **{cuped.adjusted_difference * 100:+.2f} pp**",
            f"- Adjusted 95% CI: **{cuped.ci_low * 100:+.2f} to {cuped.ci_high * 100:+.2f} pp**",
            f"- Adjusted p-value: **{cuped.p_value:.4f}**",
            "",
            "The adjusted result is a **post-hoc sensitivity analysis**, not a replacement for the pre-specified unadjusted primary analysis. In a production experiment, the covariate definition and adjustment method should be frozen before treatment outcomes are read.",
            "",
            "## Decision discipline",
            "",
            "- Keep the unadjusted 7-day activation analysis as the confirmatory decision statistic.",
            "- Use MDE and power before launch to decide whether the planned sample can resolve the business-relevant effect size.",
            "- Treat the CUPED-style result as evidence about estimator precision and robustness, not as a second chance to manufacture significance.",
            "- For a future experiment with established users, prefer a true pre-period behavioral covariate when applying classical CUPED.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the advanced experimentation readout.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/users.csv"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/advanced_experimentation.md"),
    )
    args = parser.parse_args()
    report = build_advanced_report(load_users(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
