from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SequentialSimulationResult:
    trials: int
    looks: int
    final_only_false_positive_rate: float
    naive_any_look_false_positive_rate: float
    bonferroni_any_look_false_positive_rate: float
    bonferroni_alpha_per_look: float


def _two_proportion_p_value(
    control_successes: int,
    control_n: int,
    treatment_successes: int,
    treatment_n: int,
) -> float:
    control_rate = control_successes / control_n
    treatment_rate = treatment_successes / treatment_n
    pooled = (control_successes + treatment_successes) / (control_n + treatment_n)
    standard_error = math.sqrt(
        pooled * (1 - pooled) * (1 / control_n + 1 / treatment_n)
    )
    if standard_error == 0:
        return 1.0
    z_score = (treatment_rate - control_rate) / standard_error
    return math.erfc(abs(z_score) / math.sqrt(2))


def simulate_peeking_risk(
    *,
    trials: int = 1_000,
    baseline_rate: float = 0.52,
    first_look_per_arm: int = 500,
    look_step_per_arm: int = 250,
    max_per_arm: int = 5_000,
    alpha: float = 0.05,
    seed: int = 20_260_808,
) -> SequentialSimulationResult:
    if trials < 100:
        raise ValueError("trials must be at least 100")
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if first_look_per_arm < 2 or look_step_per_arm < 1:
        raise ValueError("look sizes must be positive")
    if max_per_arm < first_look_per_arm:
        raise ValueError("max_per_arm must be at least first_look_per_arm")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    looks = list(range(first_look_per_arm, max_per_arm + 1, look_step_per_arm))
    if looks[-1] != max_per_arm:
        looks.append(max_per_arm)

    bonferroni_alpha = alpha / len(looks)
    rng = random.Random(seed)

    final_only_hits = 0
    naive_any_look_hits = 0
    bonferroni_any_look_hits = 0

    for _ in range(trials):
        control_successes = 0
        treatment_successes = 0
        look_index = 0
        naive_hit = False
        bonferroni_hit = False
        final_p_value = 1.0

        for n_per_arm in range(1, max_per_arm + 1):
            control_successes += rng.random() < baseline_rate
            treatment_successes += rng.random() < baseline_rate

            if look_index < len(looks) and n_per_arm == looks[look_index]:
                p_value = _two_proportion_p_value(
                    control_successes,
                    n_per_arm,
                    treatment_successes,
                    n_per_arm,
                )
                naive_hit = naive_hit or p_value < alpha
                bonferroni_hit = bonferroni_hit or p_value < bonferroni_alpha
                if n_per_arm == max_per_arm:
                    final_p_value = p_value
                look_index += 1

        final_only_hits += final_p_value < alpha
        naive_any_look_hits += naive_hit
        bonferroni_any_look_hits += bonferroni_hit

    return SequentialSimulationResult(
        trials=trials,
        looks=len(looks),
        final_only_false_positive_rate=final_only_hits / trials,
        naive_any_look_false_positive_rate=naive_any_look_hits / trials,
        bonferroni_any_look_false_positive_rate=bonferroni_any_look_hits / trials,
        bonferroni_alpha_per_look=bonferroni_alpha,
    )


def build_report() -> str:
    result = simulate_peeking_risk()
    return "\n".join(
        [
            "# Sequential Testing / Peeking-Risk Simulation",
            "",
            "This deterministic null simulation demonstrates why repeatedly checking an ordinary fixed-horizon p-value and stopping when it first crosses 0.05 inflates the false-positive rate.",
            "",
            "## Simulation design",
            "",
            f"- **Null trials:** {result.trials:,}",
            "- **True control and treatment rate:** 52% in both arms",
            "- **Maximum sample:** 5,000 users per arm",
            "- **Looks:** every 250 users per arm, starting at 500",
            f"- **Total interim/final looks:** {result.looks}",
            "- **Nominal alpha:** 0.05",
            f"- **Bonferroni alpha per look:** {result.bonferroni_alpha_per_look:.4f}",
            "",
            "## False-positive behavior",
            "",
            "| Analysis rule | Simulated false-positive rate |",
            "| --- | ---: |",
            f"| Test only once at the final horizon | {result.final_only_false_positive_rate:.1%} |",
            f"| Naive repeated peeking; stop on any p < 0.05 | **{result.naive_any_look_false_positive_rate:.1%}** |",
            f"| Repeated looks with Bonferroni alpha allocation | {result.bonferroni_any_look_false_positive_rate:.1%} |",
            "",
            "## Interpretation",
            "",
            "- The final-horizon-only analysis stays close to the intended 5% Type-I error in this finite simulation.",
            "- Reusing an ordinary 0.05 threshold at every look dramatically inflates false positives because the stopping rule changes the sampling process.",
            "- Bonferroni controls family-wise error here but is deliberately conservative; production experimentation platforms often use pre-specified group-sequential boundaries or alpha-spending functions instead.",
            "- The lesson is procedural: define the stopping rule and sequential method **before** treatment outcomes are inspected. Do not retrofit a correction after seeing a favorable interim result.",
            "",
            "## Scope",
            "",
            "This module is an educational peeking-risk demonstration, not the stopping rule used by the onboarding case study. The case study's main decision remains a fixed-horizon analysis with a pre-specified primary metric and guardrail.",
            "",
            "## Reproducibility",
            "",
            "The simulation uses a fixed seed (`20260808`). CI regenerates this report and fails if the committed false-positive evidence drifts.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate repeated-peeking false-positive risk.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/sequential_peeking.md"))
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
