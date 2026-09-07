#!/usr/bin/env python3
"""AstraHeal Paper 2 — Master Research Benchmark Runner.

Sequentially executes the complete Paper 2 experimental suite:
1. EXP-P2-01: Known-Fault Diagnosis Benchmark
2. EXP-P2-02: Epistemic vs Aleatoric Uncertainty Disentanglement
3. EXP-P2-03: Out-Of-Distribution & Compound Failure Detection
4. EXP-P2-04: Telemetry Noise Robustness Sweep
5. EXP-P2-05: Systematic Component Ablation
6. Phase 9: Formal Statistical Significance Analysis
7. Phase 15: Academic Paper PDF Compilation
"""

import os
import sys
import time
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import importlib

exp01 = importlib.import_module("experiments.paper2.01_known_fault_diagnosis")
exp02 = importlib.import_module("experiments.paper2.02_uncertainty_analysis")
exp03 = importlib.import_module("experiments.paper2.03_ood_detection")
exp04 = importlib.import_module("experiments.paper2.04_noise_robustness")
exp05 = importlib.import_module("experiments.paper2.05_ablation")
stats = importlib.import_module("experiments.paper2.compute_statistics")
pdf_gen = importlib.import_module("scripts.paper2.generate_paper2_pdf")


def main():
    start_total = time.time()
    print("=" * 80)
    print("ASTRAHEAL PAPER 2: MASTER REPRODUCIBILITY BENCHMARK RUNNER")
    print("Title: Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft")
    print("=" * 80)

    stages = [
        ("EXP-P2-01: Known-Fault Diagnosis", exp01.run_experiment),
        ("EXP-P2-02: Uncertainty Disentanglement", exp02.run_experiment),
        ("EXP-P2-03: OOD & Compound Detection", exp03.run_experiment),
        ("EXP-P2-04: Noise Robustness Sweep", exp04.run_experiment),
        ("EXP-P2-05: Component Ablation Study", exp05.run_experiment),
        ("Phase 9: Statistical Significance", stats.run_statistical_analysis),
    ]

    for stage_idx, (stage_name, runner_fn) in enumerate(stages, 1):
        t0 = time.time()
        print(f"\n[{stage_idx}/{len(stages) + 1}] Executing {stage_name}...")
        runner_fn()
        elapsed = time.time() - t0
        print(f"  -> Completed in {elapsed:.2f}s")

    # Final PDF Recompilation
    print(f"\n[{len(stages) + 1}/{len(stages) + 1}] Compiling Publication PDF Manuscript...")
    t0 = time.time()
    pdf_out = str(REPO_ROOT / "docs" / "paper2" / "latex" / "PAPER2.pdf")
    pdf_gen.build_pdf(pdf_out)
    print(f"  -> PDF generated in {time.time() - t0:.2f}s at: {pdf_out}")

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"ALL PAPER 2 EXPERIMENTS COMPLETED DETERMINISTICALLY IN {total_time:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()
