#!/usr/bin/env python3
"""AstraHeal Paper 3 — Master Reproducibility Benchmark Runner.

Sequentially executes the complete Paper 3 experimental suite:
1. EXP-P3-01: Baseline Safety Enforcement (Ungoverned vs Governed AI)
2. EXP-P3-02: Individual Constraint Coverage (4 Canonical States)
3. EXP-P3-03: Compound Multi-Constraint Breaches (Double, Triple, Quad)
4. EXP-P3-04: Adversarial AI Proposal Injection (5 Attack Modes)
5. EXP-P3-05: Continuous Boundary Testing (201-Point Fine Sweeps)
6. EXP-P3-06: Communication-Aware Safety Arbitration
7. EXP-P3-07: Physically Constrained No-Safe-Action Scenarios
8. EXP-P3-08: Safety Governor Ablation, Fail-Closed & Profiling
9. Phase 9: Formal Statistical Significance Analysis & Confidence Bounds
10. Phase 10: Publication Figure Generation & PDF Compilation
"""

import importlib
import os
import sys
import time
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

exp01 = importlib.import_module("experiments.paper3.01_baseline_safety_enforcement")
exp02 = importlib.import_module("experiments.paper3.02_constraint_coverage")
exp03 = importlib.import_module("experiments.paper3.03_compound_constraint_violations")
exp04 = importlib.import_module("experiments.paper3.04_unsafe_ai_proposals")
exp05 = importlib.import_module("experiments.paper3.05_boundary_testing")
exp06 = importlib.import_module("experiments.paper3.06_communication_aware_safety")
exp07 = importlib.import_module("experiments.paper3.07_no_safe_action")
exp08 = importlib.import_module("experiments.paper3.08_safety_governor_ablation")
stats = importlib.import_module("experiments.paper3.compute_statistics")


def main():
    start_total = time.time()
    print("=" * 80)
    print("ASTRAHEAL PAPER 3: MASTER REPRODUCIBILITY BENCHMARK RUNNER")
    print("Title: AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft")
    print("=" * 80)

    stages = [
        ("P3-E1: Baseline Safety Enforcement", exp01.run_experiment),
        ("P3-E2: Individual Constraint Coverage", exp02.run_experiment),
        ("P3-E3: Compound Constraint Violations", exp03.run_experiment),
        ("P3-E4: Adversarial Proposal Injection", exp04.run_experiment),
        ("P3-E5: Continuous Boundary Sweeps", exp05.run_experiment),
        ("P3-E6: Communication-Aware Arbitration", exp06.run_experiment),
        ("P3-E7: No-Safe-Action Dead-Ends", exp07.run_experiment),
        ("P3-E8: Ablation, Fail-Closed & Profiling", exp08.run_experiment),
        ("Phase 9: Statistical Significance & Wilson Bounds", stats.run_statistical_analysis),
    ]

    for stage_idx, (stage_name, runner_fn) in enumerate(stages, 1):
        t0 = time.time()
        print(f"\n[{stage_idx}/{len(stages)}] Executing {stage_name}...")
        runner_fn()
        elapsed = time.time() - t0
        print(f"  -> Completed in {elapsed:.2f}s")

    # If figure generator and PDF compiler exist, execute them
    try:
        fig_gen = importlib.import_module("scripts.paper3.generate_paper3_figures")
        print("\nExecuting Publication Figure Generator...")
        fig_gen.generate_all_figures()
    except ImportError:
        pass

    try:
        pdf_gen = importlib.import_module("scripts.paper3.generate_paper3_pdf")
        print("\nCompiling Publication PDF Manuscript...")
        pdf_out = str(REPO_ROOT / "docs" / "paper3" / "latex" / "PAPER3.pdf")
        pdf_gen.build_pdf(pdf_out)
    except ImportError:
        pass

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"ALL PAPER 3 EXPERIMENTS COMPLETED DETERMINISTICALLY IN {total_time:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()
