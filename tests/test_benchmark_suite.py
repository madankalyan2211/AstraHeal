"""Unit tests for Stage 11 Research Benchmark Suite."""

import pytest
from evaluation.scenarios import BenchmarkScenarioGenerator, BenchmarkScenarioSpec
from evaluation.metrics import BenchmarkMetricsCalculator, ComparativeScenarioMetrics
from evaluation.benchmark import TriSystemBenchmarkRunner


def test_scenario_suite_generation():
    """Verify standard benchmark suite generates diverse scenarios."""
    suite = BenchmarkScenarioGenerator.get_full_evaluation_suite()
    assert len(suite) == 8
    categories = set(s.category for s in suite)
    assert "NOMINAL" in categories
    assert "KNOWN" in categories
    assert "COMPOUND_OOD" in categories


def test_benchmark_metrics_aggregation():
    """Verify aggregate summary statistics computation."""
    results = [
        ComparativeScenarioMetrics(
            system_name="ASTRAHEAL",
            scenario_id="S1",
            scenario_name="Test 1",
            survived=True,
            hard_constraint_violations_count=0,
            max_battery_temp_c=25.0,
            min_bus_voltage_v=26.0,
            min_soc=0.8,
            final_soc=0.9,
            payload_availability_pct=80.0,
            energy_margin_wh=500.0,
            autonomous_actions_executed=1
        ),
        ComparativeScenarioMetrics(
            system_name="ASTRAHEAL",
            scenario_id="S2",
            scenario_name="Test 2",
            survived=False,
            hard_constraint_violations_count=5,
            max_battery_temp_c=50.0,
            min_bus_voltage_v=20.0,
            min_soc=0.1,
            final_soc=0.1,
            payload_availability_pct=0.0,
            energy_margin_wh=0.0,
            autonomous_actions_executed=1
        )
    ]
    summary = BenchmarkMetricsCalculator.aggregate_suite("ASTRAHEAL", results)
    assert summary.total_scenarios == 2
    assert summary.survival_rate_pct == 50.0
    assert summary.total_hard_violations == 5
    assert summary.mean_payload_availability_pct == 40.0


def test_tri_system_single_scenario_execution():
    """Verify single scenario execution across Baseline A, Baseline B, and AstraHeal."""
    runner = TriSystemBenchmarkRunner(simulation_step_sec=20.0)
    spec = BenchmarkScenarioSpec(
        scenario_id="TEST-SCEN",
        name="Quick Test Scenario",
        category="KNOWN",
        orbit_duration_sec=300.0,
        faults=[]
    )
    res_a = runner.run_single_scenario("BASELINE_A", spec)
    res_b = runner.run_single_scenario("BASELINE_B", spec)
    res_astra = runner.run_single_scenario("ASTRAHEAL", spec)

    assert res_a.system_name == "BASELINE_A"
    assert res_b.system_name == "BASELINE_B"
    assert res_astra.system_name == "ASTRAHEAL"
