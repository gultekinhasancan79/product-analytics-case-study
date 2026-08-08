from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExposureRow:
    assignment: str
    device: str
    exposed: bool
    activated: bool


@dataclass(frozen=True)
class ExposureAnalysis:
    control_n: int
    treatment_n: int
    treatment_exposure_rate: float
    control_activation_rate: float
    treatment_assignment_activation_rate: float
    itt_effect: float
    exposed_treatment_activation_rate: float
    naive_exposed_vs_control_effect: float
    wald_treatment_on_treated_effect: float


def generate_exposure_demo(
    n: int = 100_000,
    *,
    seed: int = 20_260_808,
    exposure_effect: float = 0.06,
) -> list[ExposureRow]:
    """Generate a randomized assignment / imperfect exposure demonstration.

    Assignment is randomized. Exposure is only possible in treatment and is more
    likely on desktop. Device also affects baseline activation, so conditioning on
    observed exposure changes the device mix and makes a naive exposed-vs-control
    comparison non-randomized.
    """
    if n < 100:
        raise ValueError("n must be at least 100")
    if not 0 <= exposure_effect <= 0.25:
        raise ValueError("exposure_effect must be between 0 and 0.25")

    rng = random.Random(seed)
    rows: list[ExposureRow] = []

    for _ in range(n):
        assignment = "treatment" if rng.random() < 0.5 else "control"
        device = "desktop" if rng.random() < 0.60 else "mobile"
        baseline_activation = 0.50 if device == "desktop" else 0.40

        if assignment == "treatment":
            exposure_probability = 0.90 if device == "desktop" else 0.60
            exposed = rng.random() < exposure_probability
        else:
            exposed = False

        activation_probability = baseline_activation + (exposure_effect if exposed else 0.0)
        activated = rng.random() < activation_probability
        rows.append(
            ExposureRow(
                assignment=assignment,
                device=device,
                exposed=exposed,
                activated=activated,
            )
        )

    return rows


def _activation_rate(rows: list[ExposureRow]) -> float:
    if not rows:
        raise ValueError("activation rate requires at least one row")
    return sum(row.activated for row in rows) / len(rows)


def analyze_exposure(rows: list[ExposureRow]) -> ExposureAnalysis:
    control = [row for row in rows if row.assignment == "control"]
    treatment = [row for row in rows if row.assignment == "treatment"]
    exposed_treatment = [row for row in treatment if row.exposed]

    if not control or not treatment or not exposed_treatment:
        raise ValueError("analysis requires control, treatment, and exposed treatment rows")

    control_rate = _activation_rate(control)
    treatment_rate = _activation_rate(treatment)
    exposed_rate = len(exposed_treatment) / len(treatment)
    exposed_activation = _activation_rate(exposed_treatment)

    itt_effect = treatment_rate - control_rate
    naive_effect = exposed_activation - control_rate

    # With one-sided non-compliance, randomized assignment as the instrument,
    # no control exposure, monotonicity, and exclusion restriction, the Wald
    # ratio estimates the local average treatment effect among compliers.
    wald_effect = itt_effect / exposed_rate

    return ExposureAnalysis(
        control_n=len(control),
        treatment_n=len(treatment),
        treatment_exposure_rate=exposed_rate,
        control_activation_rate=control_rate,
        treatment_assignment_activation_rate=treatment_rate,
        itt_effect=itt_effect,
        exposed_treatment_activation_rate=exposed_activation,
        naive_exposed_vs_control_effect=naive_effect,
        wald_treatment_on_treated_effect=wald_effect,
    )


def build_report() -> str:
    result = analyze_exposure(generate_exposure_demo())
    return "\n".join(
        [
            "# Exposure Logging — ITT vs Treatment-on-Treated Demo",
            "",
            "This is a separate deterministic compliance simulation designed to demonstrate why randomized **assignment** and observed **exposure** answer different causal questions.",
            "",
            "It is intentionally separate from the main onboarding experiment so the existing case-study data are not retrofitted with an exposure mechanism that was never part of their data-generating process.",
            "",
            "## Demo design",
            "",
            f"- **Randomized sample:** {result.control_n + result.treatment_n:,} users",
            f"- **Assignment:** {result.control_n:,} control / {result.treatment_n:,} treatment",
            "- **True effect of actual exposure in the simulator:** +6.00 pp activation",
            "- **One-sided non-compliance:** controls cannot receive treatment exposure",
            "- **Treatment exposure probability:** 90% desktop / 60% mobile",
            "- **Baseline activation:** 50% desktop / 40% mobile",
            "",
            "Because device affects both baseline activation and treatment compliance, the exposed treatment subset has a different device mix from the randomized control arm.",
            "",
            "## Readout",
            "",
            "| Estimand / comparison | Result |",
            "| --- | ---: |",
            f"| Treatment exposure rate | {result.treatment_exposure_rate:.1%} |",
            f"| Control activation | {result.control_activation_rate:.2%} |",
            f"| Treatment-assigned activation | {result.treatment_assignment_activation_rate:.2%} |",
            f"| **ITT: assigned treatment - assigned control** | **{result.itt_effect * 100:+.2f} pp** |",
            f"| Exposed-treatment activation | {result.exposed_treatment_activation_rate:.2%} |",
            f"| Naive exposed-treatment - control | {result.naive_exposed_vs_control_effect * 100:+.2f} pp |",
            f"| Wald / IV treatment-on-treated estimate | {result.wald_treatment_on_treated_effect * 100:+.2f} pp |",
            "",
            "## Interpretation",
            "",
            "- **ITT** preserves randomization because users are analyzed by assigned variant regardless of whether treatment was actually seen. It answers the product-policy question: what is the effect of assigning this treatment under real delivery/compliance?",
            "- Comparing only exposed treatment users with controls breaks the original randomized comparison. In this simulator, desktop users are more likely to be exposed and also have higher baseline activation, so the naive exposed-vs-control contrast overstates the +6 pp exposure effect.",
            "- Under the demo's explicit one-sided non-compliance, monotonicity, and exclusion-restriction assumptions, randomized assignment can be used as an instrument. The Wald ratio `ITT / exposure-rate difference` moves the estimate back toward the simulated +6 pp treatment-on-treated effect.",
            "- The IV result should not be copied mechanically into production analysis. Instrument validity, exposure logging quality, interference, monotonicity, and exclusion restrictions must be defended for the actual product system.",
            "",
            "## Exposure logging requirements",
            "",
            "A production implementation should separately log at least: assignment, experiment eligibility, exposure timestamp, treatment version, user/session identity, and outcome windows. Assignment should never be inferred from downstream treatment events.",
            "",
            "## Reproducibility",
            "",
            "The demo uses a fixed seed (`20260808`) and 100,000 simulated users. CI regenerates this report and fails if the committed estimand evidence drifts.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Demonstrate ITT and exposure-based estimands.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/exposure_itt_tot.md"))
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
