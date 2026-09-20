# AstraHeal Paper 4: Research Highlights & Verified Findings

**Paper Title**: AstraHeal: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions  
**Research Series Contribution**: VALIDATE (completing PLAN $\rightarrow$ UNDERSTAND $\rightarrow$ CONSTRAIN $\rightarrow$ VALIDATE)  
**Total Evaluated Scenarios**: 1,320 closed-loop spacecraft missions  
**Total Autonomous Closed-Loop Cycles**: >18,000 cycles  
**Platform**: Physics-grounded 12U CubeSat Electrical Power System digital twin in 550 km Sun-Synchronous Orbit  

---

### 1. Zero Unsafe Action Executions Across 1,320 Benchmark Missions (0.00% Violation)
Across 1,320 multi-cycle missions evaluated across eight distinct experimental campaigns—encompassing cascading faults, up to 10 repeated recovery cycles, $\pm 20\%$ physical parameter perturbations, continuous sensor noise, and multi-orbit flights—**exactly zero unsafe actions were executed** ($0.00\%$). The exact Clopper-Pearson 95% confidence upper bound on unsafe execution probability is established at **$< 0.2791\%$**.

### 2. Over 40,000 Unsafe Proposals Intercepted by the Deterministic Safety Governor
The four-tier deterministic Safety Governor intercepted and rejected **40,711 unsafe candidate action proposals** (8,132 in P4-E1, 32,579 in P4-E6 compound faults) that would have violated immutable physical invariants (core thermal ceiling $T \le 46.0^\circ\text{C}$, undervoltage floor $V_{\text{bus}} \ge 22.0\,\text{V}$, or overcurrent limit $I_{\text{batt}} \le 40.0\,\text{A}$).

### 3. Stability Maintained Across Up to 10 Repeated Recovery Cycles
In Experiment P4-E2 (120 runs across target cycle counts $k \in \{1, 2, 3, 5, 8, 10\}$), the integrated system maintained **100.0% survival** across all cycle counts up to $k=10$ with zero hard safety violations, proving that multi-cycle recovery does not induce state divergence or runaway instability.

### 4. Robust Tolerance Across $\pm 20\%$ Physical Parameter Perturbations
In Experiment P4-E3 (225 simulation runs sweeping thermal mass $C_{\text{th}}$, radiator coupling $h_{\text{rad}}$, cell resistance $R_0$, solar conversion efficiency $\eta_{\text{solar}}$, and payload power demand $P_{\text{load}}$ across $\pm 20\%$), AstraHeal achieved **100.0% mission survival** (225/225) with zero unsafe actions executed, confirming robust stability under substantial sim-to-real model mismatch.

### 5. Monotonic Evidential Uncertainty Scaling Under Telemetry Corruption
In Experiment P4-E4 (225 runs across nine Gaussian noise scales $\sigma \in [0.005, 0.080]$), Dirichlet epistemic uncertainty scaled monotonically from $0.8327$ to $0.9988$. Rather than making overconfident erroneous decisions, elevated uncertainty safely triggered conservative safe-hold behaviors, guaranteeing zero unsafe executions ($0.00\%$).

### 6. 170.6% Scientific Payload Utility Advantage from Counterfactual Lookahead
In Experiment P4-E8 (standardized 50-scenario ablation benchmark across 300 runs), Full AstraHeal delivered $574.0\,\text{Wh}$ nominal payload ($100.0\%$ availability), whereas ablating counterfactual lookahead planning reduced delivered payload to $212.1\,\text{Wh}$ ($36.95\%$ nominal utility). This $+361.9\,\text{Wh}$ advantage is statistically decisive (paired Student-t $t(49) = 21.09, p = 3.10 \times 10^{-26}$, Cohen's $d = 2.98$).

### 7. Explicit Characterization of Physical Failure Boundaries Under Severe Cascades
In Experiment P4-E6 (150 compound concurrent cascading fault scenarios), 100 scenarios experienced physical bus collapse due to simultaneous thermal runaway and battery capacity degradation exceeding physical dissipation capacity. AstraHeal's governor maintained the safety invariant ($0$ unsafe actions executed), providing authentic evidence without masking physical limitations.
