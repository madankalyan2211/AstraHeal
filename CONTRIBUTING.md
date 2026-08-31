# Contributing to AstraHeal

Thank you for your interest in contributing to AstraHeal. As a research-grade open-source project, we adhere to strict scientific rigor, deterministic reproducibility, and software reliability standards.

## Code Standards
1. **Deterministic Testing**: All new features must include unit tests under `tests/` with fixed random seeds.
2. **Safety Invariants**: No modification may bypass or weaken the Deterministic Safety Governor.
3. **No Fabricated Data**: Experiments must report measured metrics and ground-truth telemetry only.
4. **Formatting**: Follow PEP 8 style guidelines with type annotations.

## Submitting Pull Requests
1. Fork the repository and create a feature branch.
2. Run `pytest tests/ -v` to ensure all 35 tests pass cleanly.
3. Run `python run_all_experiments.py` to ensure experiments reproduce expected benchmark results.
4. Submit a detailed pull request describing the methodology and empirical validation.
