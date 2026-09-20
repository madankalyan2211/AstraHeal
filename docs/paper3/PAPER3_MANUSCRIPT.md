# AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery

**Madan Kalyan Thambisetty**  
*Autonomous Systems & Aerospace Software Research*  
*AstraHeal Research Series — Paper 3*  
*Repository*: [https://github.com/madankalyan2211/AstraHeal](https://github.com/madankalyan2211/AstraHeal)  

---

## 1. Abstract

Autonomous spacecraft operating in Low Earth Orbit (LEO) and deep-space regimes must resolve critical subsystem anomalies during prolonged communication blackouts. While machine-learning planners and evidential diagnostic engines can generate high-utility recovery recommendations, purely statistical and learning-based architectures cannot offer mathematical safety guarantees: under novel compound anomalies, sensor corruption, or distribution shifts, upstream models can produce overconfident, flawed, or catastrophic actuation proposals.

In this paper, we present and evaluate the **AstraHeal Deterministic Safety Governor**, a fail-closed runtime execution gatekeeper founded on the architectural axiom: *the AI proposes; the deterministic governor disposes*. Rather than evaluating static current telemetry, the governor projects the physical consequences of proposed actions across counterfactual digital twin horizons and deterministically evaluates candidate admissibility against five hard physical invariants: battery thermal runaway barrier ($T_{\text{batt}} \le 46.0^\circ\text{C}$), avionics undervoltage floor ($V_{\text{bus}} \ge 22.0\text{V}$), PDU overcurrent limit ($I_{\text{batt}} \le 40.0\text{A}$), battery reserve floor ($\text{SoC} \ge 15\%$), and total power delivery ceiling ($P \le 880.0\text{W}$).

Across eight controlled experiments covering 1,519 evaluated unsafe proposals, the system demonstrated: (i) zero executed unsafe actions ($0.00\%$ execution rate, Clopper-Pearson 95% upper bound $< 0.1970\%$), significantly outperforming an ungoverned AI baseline (100.0% unsafe execution, McNemar $\chi^2 = 191.01, p = 1.92 \times 10^{-43}$, Cohen's $h = 3.1416$); (ii) 100.0% rejection across 400 adversarial proposals spanning 5 attack vectors despite high upstream AI confidence ($\ge 0.96$); (iii) 100.0% concurrent violation detection recall (800/800 breaches) across multi-fault compound failures without premature short-circuiting; (iv) strictly monotonic step-function transitions across 804 continuous boundary sweep points; (v) strict dominance of hard safety invariants over communication arbitration in both ground contact and blackout; and (vi) 100.0% safe-failure convergence to `NO_SAFE_ACTION_AVAILABLE` during physical dead-ends, eliminating the dangerous practice of forcing an unverified action. Microsecond profiling across 10,000 evaluations demonstrated a mean latency of $2.99\,\mu\text{s}$, establishing deterministic runtime safety assurance with negligible onboard overhead.

---

## 2. Introduction

Modern space exploration increasingly relies on high levels of onboard autonomy due to orbital geometry constraints and round-trip radio propagation delays. In Low Earth Orbit (LEO), spacecraft experience line-of-sight communication blackouts lasting up to 45 minutes per 95-minute orbit; in lunar, Martian, and Lagrange-point missions, signal latency ranges from minutes to hours. Under these conditions, time-critical subsystem anomalies—such as battery internal resistance spikes, thermal runaway initiation, and bus power shorts—can cause irreversible vehicle loss before ground flight controllers can intervene.

To mitigate this operational vulnerability, recent aerospace research has explored advanced artificial intelligence, including reinforcement learning, deep counterfactual lookahead, and evidential neural networks. These models exhibit superior adaptive flexibility compared to traditional rigid Fault Detection, Isolation, and Recovery (FDIR) rule tables. However, machine-learning models possess an inherent safety vulnerability: they are fundamentally statistical approximators. When presented with out-of-distribution (OOD) telemetry, sensor calibration drift, or multiple concurrent failures, AI planners can produce invalid or dangerous recovery commands while reporting misleadingly high confidence.

This work addresses that vulnerability by investigating the final safety barrier situated immediately prior to actuator command dispatch: **deterministic runtime safety gating**. Rather than permitting an AI model to command spacecraft avionics directly, the autonomous architecture decouples proposal generation from execution authorization. The upstream AI model is treated strictly as an unverified advisor whose proposals must be independently validated against immutable physical spacecraft invariants.

---

## 3. Motivation

In terrestrial robotics, autonomous driving, and avionics, the concept of a runtime "safety shield" or "safety monitor" has gained significant attention. However, applying runtime assurance to spacecraft electrical power and thermal systems introduces unique physical challenges:
1. **Dynamic Counterfactual Coupling**: Spacecraft health constraints are coupled through complex differential equations of electro-thermal kinetics. An action that appears safe in the current telemetry frame (e.g., re-engaging a science payload when battery temperature is nominally $30^\circ\text{C}$) can induce delayed exothermic thermal runaway several hundred seconds later. Static rule tables cannot detect this delayed catastrophe.
2. **The "Forced Recovery" Fallacy**: Many automated planners operate under the unstated assumption that a viable recovery path always exists. When severe physical hardware damage occurs (e.g., internal battery short-circuit where heat generation exceeds radiator dissipation capability), forcing an action will command dangerous reconfigurations. A flight-grade safety system must be capable of declaring `NO_SAFE_ACTION_AVAILABLE`.
3. **Communication Interaction**: Autonomous systems must balance onboard action against human-in-the-loop ground review. A safety architecture must guarantee that communication preferences never override hard physical constraints.

---

## 4. Research Questions

This paper investigates one central research question and three sub-questions:

* **Central Research Question**: *Can a deterministic safety governor reliably prevent unsafe autonomous spacecraft recovery actions proposed by an AI-based fault-management system from reaching execution, including under uncertain, incorrect, or deliberately unsafe upstream proposals?*
* **RQ1 (Constraint Coverage & Multi-Breach Recall)**: Can a deterministic governor evaluate multi-domain constraints independently while reliably detecting all concurrent breaches in compound anomalies without premature exit?
* **RQ2 (Adversarial Decoupling)**: Can the governor maintain zero unsafe executions when upstream AI proposals are accompanied by artificially high confidence scores?
* **RQ3 (Safe Failure)**: How does the system behave when all available recovery candidates violate at least one physical constraint?

---

## 5. Hypotheses

* **Hypothesis 1 (H1 — Baseline Gating Efficacy)**: A deterministic Safety Governor significantly reduces unsafe action executions compared with an otherwise identical recovery system without deterministic gating under identical proposal distributions.
* **Hypothesis 2 (H2 — Independent Constraint Verification)**: The Safety Governor correctly evaluates physical constraints independently across thermal, voltage, overcurrent, battery reserve, and power boundaries.
* **Hypothesis 3 (H3 — Adversarial Robustness)**: Upstream AI confidence or urgency scores cannot deceive or bypass the governor when evaluating flawed or deliberately adversarial proposals.
* **Hypothesis 4 (H4 — Continuous Boundary Monotonicity)**: Gating transitions are sharp, exact step functions displaying strict mathematical monotonicity near constraint boundaries.
* **Hypothesis 5 (H5 — Safety Dominance over Communication)**: Communication constraints influence action timing but never override a Level 1 hard physical safety invariant.
* **Hypothesis 6 (H6 — Safe Failure Convergence)**: When physical deficits eliminate all safe recovery options, the system safely converges to `NO_SAFE_ACTION_AVAILABLE` rather than forcing an unsafe action.

---

## 6. Contributions

The contributions of Paper 3 are:
1. **Counterfactual Consequence Gating**: Formulation of a runtime execution barrier that evaluates predicted future trajectories across digital twin lookahead branches rather than static instantaneous telemetry.
2. **AI-Independent Verification**: Empirical demonstration that safety authorization can be completely decoupled from upstream model confidence, preventing catastrophic actuation from overconfident models.
3. **Multi-Breach Compound Auditability**: Demonstration of 100.0% recall across 800 compound violations, ensuring complete incident diagnostics for ground operators.
4. **Formal Safe-Failure Protocol**: Implementation and verification of the non-forcing `NO_SAFE_ACTION_AVAILABLE` protocol across 150 physically constrained dead-end scenarios.
5. **Sub-Millisecond Avionics Feasibility**: Profiling across 10,000 evaluations establishing a mean latency of $2.99\,\mu\text{s}$ ($>320,000$ evaluations/second).

---

## 7. Related Work

### Runtime Assurance & Safety Shields
Runtime assurance architectures, such as the ASTM F3269-17 standard and Simplex architecture developed by Sha et al., establish a framework where an unverified advanced controller is paired with a certified baseline controller. Alshiekh et al. formalized "safety shields" using linear temporal logic (LTL) for discrete reinforcement learning environments. AstraHeal extends this concept to continuous, non-linear aerospace power and thermal kinetics, replacing discrete state transitions with counterfactual digital twin lookahead.

### Spacecraft Fault Detection, Isolation, and Recovery (FDIR)
Traditional aerospace practice relies on rigid hierarchical rule tables developed for missions such as Deep Space 1 (Remote Agent) and EO-1 (Autonomous Sciencecraft Experiment). While highly predictable, conventional FDIR systems rely on static thresholds on instantaneous telemetry. As demonstrated in our ablation studies, static thresholds fail to prevent unsafe actions that induce delayed downstream thermal or electrical collapse.

### Distinction from AstraHeal Papers 1 and 2
- **Paper 1** focused on counterfactual planning and alternative action generation across 15 orbital simulation experiments.
- **Paper 2** focused on evidential Dirichlet Bayesian diagnosis and out-of-distribution uncertainty quantification.
- **Paper 3** isolates the authoritative runtime safety barrier, investigating whether deterministic invariant gating can guarantee execution safety regardless of upstream diagnostic or planning fallibility.

---

## 8. Problem Formulation

Let the physical state of the spacecraft electrical power system (EPS) at time $t$ be denoted by:

$$\mathbf{s}(t) = \left[ T_{\text{batt}}(t),\; V_{\text{bus}}(t),\; I_{\text{batt}}(t),\; \text{SoC}(t),\; P_{\text{pdu}}(t) \right]^T \in \mathbb{R}^5$$

When an anomaly is detected, an upstream AI planner generates an action proposal $a \in \mathcal{A}$, where $\mathcal{A}$ is the catalog of certified flight recovery actions. Associated with proposal $a$ is an upstream confidence score $c(a) \in [0, 1]$ and an urgency ranking $u(a) \in [0, 1]$.

Executing action $a$ induces a counterfactual state trajectory over evaluation horizon $\tau \in [t, t + H]$:

$$\mathbf{s}_a(\tau) = \mathbf{f}\left(\mathbf{s}(t), a, \tau\right)$$

The runtime safety problem requires evaluating whether the projected trajectory $\mathbf{s}_a(\tau)$ remains within the safe operational polytope $\mathcal{S}_{\text{safe}} \subset \mathbb{R}^5$ for all $\tau \in [t, t + H]$:

$$\mathcal{S}_{\text{safe}} = \left\{ \mathbf{s} \;\middle|\; T_{\text{batt}} \le T_{\max},\; V_{\text{bus}} \ge V_{\min},\; I_{\text{batt}} \le I_{\max},\; \text{SoC} \ge \text{SoC}_{\min},\; P_{\text{pdu}} \le P_{\max} \right\}$$

---

## 9. Autonomous Spacecraft Fault-Recovery Architecture

The AstraHeal architecture organizes autonomous decision-making into four distinct functional stages:

$$\text{Telemetry Stream} \;\longrightarrow\; \text{Diagnosis} \;\longrightarrow\; \text{Proposal Generation} \;\longrightarrow\; \boxed{\text{Deterministic Safety Governor}} \;\longrightarrow\; \text{Execution}$$

The Safety Governor serves as the absolute boundary: no command can reach flight avionics without passing through the governor's deterministic verification gates.

---

## 10. Deterministic Safety Governor

The Safety Governor implements an immutable mapping:

$$G\left(\mathbf{s}(t), a\right) \in \{\text{APPROVED},\; \text{REJECTED}\}$$

The decision is governed by:

$$G\left(\mathbf{s}(t), a\right) = \begin{cases} \text{APPROVED}, & \text{if } \forall i \in \{1, \dots, K\}, \; C_i\left(\mathbf{s}_a(\cdot)\right) = \text{PASS} \\ \text{REJECTED}, & \text{if } \exists i \in \{1, \dots, K\}, \; C_i\left(\mathbf{s}_a(\cdot)\right) = \text{FAIL} \end{cases}$$

Crucially, the governor enforces:

$$\frac{\partial G}{\partial c(a)} = 0, \quad \frac{\partial G}{\partial u(a)} = 0$$

The authorization verdict is mathematically independent of upstream AI confidence $c(a)$ or urgency $u(a)$.

---

## 11. Safety Invariants

The five hard physical invariants enforced in AstraHeal Paper 3 are defined from physical principles of spacecraft lithium-ion cells and regulated power buses:

1. **Thermal Barrier ($T_{\text{batt}} \le 46.0^\circ\text{C}$)**: Lithium-ion pouch cells undergo solid electrolyte interphase (SEI) breakdown and exothermic electrolyte oxidation above $46.0^\circ\text{C}$, leading to self-sustaining thermal runaway.
2. **Undervoltage Floor ($V_{\text{bus}} \ge 22.0\text{V}$)**: The spacecraft avionics and onboard computer (OBC) require a regulated 28V bus; voltages collapsing below 22.0V trigger brownout reset and complete loss of attitude control.
3. **Overcurrent Ceiling ($I_{\text{batt}} \le 40.0\text{A}$)**: PDU solid-state power switches and wiring harnesses are rated for 40.0A maximum continuous current to prevent resistive trace burning.
4. **Battery Reserve Floor ($\text{SoC} \ge 15.0\%$)**: Discharging lithium-ion cells below 15% during eclipse causes copper dissolution and irreversible internal short-circuiting.
5. **Power Ceiling ($P_{\text{pdu}} \le 880.0\text{W}$)**: Derived from the simultaneous limits $V_{\min} \times I_{\max} = 22\text{V} \times 40\text{A} = 880\text{W}$.

---

## 12. Constraint Evaluation

For each candidate proposal $a$, the governor calculates continuous physical margins:

$$\Delta T = T_{\max} - \max_{\tau} T_{\text{batt}}(\tau)$$
$$\Delta V = \min_{\tau} V_{\text{bus}}(\tau) - V_{\min}$$
$$\Delta I = I_{\max} - \max_{\tau} I_{\text{batt}}(\tau)$$
$$\Delta \text{SoC} = \min_{\tau} \text{SoC}(\tau) - \text{SoC}_{\min}$$
$$\Delta P = P_{\max} - \max_{\tau} P_{\text{pdu}}(\tau)$$

An action is approved if and only if:

$$\min\left(\Delta T, \Delta V, \Delta I, \Delta \text{SoC}, \Delta P\right) \ge 0$$

---

## 13. Communication-Aware Arbitration

Paper 3 formalizes a strict two-level hierarchy between physical safety and communication availability:
* **Level 1 (Hard Safety Invariant)**: Inviolable. If an action is rejected by Level 1, it cannot be executed under any circumstances.
* **Level 2 (Communication Geometry)**: If an action is approved by Level 1:
  - If direct ground contact is active ($\text{link} = \text{IN\_CONTACT}$) and $T_{\text{crit}} > T_{\text{ops}}$, the action is deferred to Earth operators (`WAIT_FOR_GROUND`).
  - If in orbital occultation ($\text{link} = \text{BLACKOUT}$) or if failure onset is faster than ground reaction budget ($T_{\text{crit}} < T_{\text{ops}}$), immediate autonomous execution is authorized (`ACT_AUTONOMOUSLY`).

Under no circumstances can ground contact override a Level 1 rejection.

---

## 14. Fail-Closed Safety Behavior

The governor implements strict fail-closed handling for anomalous inputs:
* **Corrupted Telemetry**: If any channel contains IEEE 754 `NaN`, `Inf`, or null values, the state fails validation and the action is immediately rejected (`FAIL_CLOSED_CORRUPTED_TELEMETRY`).
* **Uncertified Actions**: If proposal $a$ specifies an action identifier outside the certified flight catalog, it is rejected (`FAIL_CLOSED_UNCERTIFIED_ACTION_TYPE`).
* **Evaluator Exceptions**: Any internal numerical error or out-of-memory event triggers immediate safe standby inhibition.

Across 7 synthetic edge cases in P3-E8 (Table 8), the system demonstrated a **100.0% fail-closed rejection rate**.

---

## 15. Experimental Methodology

The experimental suite was executed using deterministic pseudorandom generators (`np.random.default_rng`) with documented random seeds (42, 101, 777, 999, 1337, 2026). All tests executed against high-fidelity spacecraft EPS and thermal simulation dynamics.

---

## 16. Baseline System

To isolate the contribution of deterministic gating, we evaluate three system configurations under identical scenario distributions:
* **System A (AI Only)**: Upstream heuristic/ML recovery planner commanding actions directly to the digital twin.
* **System B (Heuristic Rules Only)**: Traditional aerospace FDIR checking instantaneous telemetry against static limits.
* **System C (AI + Safety Governor)**: The proposed AstraHeal architecture intercepting proposals and gating execution through counterfactual consequence evaluation.

---

## 17. Experimental Scenarios

The evaluation comprises eight empirical studies:
* **P3-E1**: Baseline Safety Enforcement (500 scenarios)
* **P3-E2**: Individual Constraint Coverage (600 evaluations across 4 canonical regimes)
* **P3-E3**: Compound Multi-Constraint Breaches (300 scenarios across double, triple, and quad combinations)
* **P3-E4**: Adversarial AI Proposal Injection (400 proposals across 5 attack vectors)
* **P3-E5**: Continuous Boundary Testing (804 points across 4 channels)
* **P3-E6**: Communication-Aware Arbitration (300 scenarios across contact and blackout)
* **P3-E7**: Physically Constrained Dead-Ends (150 scenarios, 750 candidate evaluations)
* **P3-E8**: System Ablation & Overhead Profiling (500 ablation scenarios, 10,000 latency evaluations)

Total unsafe proposals evaluated across the suite: **$N = 1,519$**.

---

## 18. Results: Baseline Safety Enforcement (P3-E1)

In Experiment P3-E1, 500 candidate proposals (307 safe, 193 unsafe) were evaluated:
* **Ungoverned AI (System A)**: Executed 193 / 193 unsafe proposals (**100.0% Unsafe Execution Rate**).
* **Governed AI (System B)**: Executed 0 / 193 unsafe proposals (**0.00% Unsafe Execution Rate**), rejecting all 193 unsafe candidates (**100.0% Rejection Rate**) while approving all 307 safe candidates (**100.0% Acceptance Rate**).
* **Governor Bypass Rate**: **0.0% (0 bypasses)**.
* **Statistical Significance**: Paired McNemar test with continuity correction yielded $\chi^2 = 191.01$ ($p = 1.92 \times 10^{-43}$), with Cohen's effect size $h = 3.1416$ ($\pi$).

---

## 19. Results: Unsafe Proposal Injection & Constraint Coverage (P3-E2 & P3-E4)

In Experiment P3-E2, 600 independent evaluations across thermal, voltage, current, SoC, power, and survival invariants achieved **100.0% accuracy** across clearly safe, near limit, exact boundary, and explicit breach regimes (Fig. 2).

In Experiment P3-E4, 400 adversarial proposals with high confidence ($\ge 0.96$) were injected across 5 attack vectors (excessive power, thermal runaway, undervoltage collapse, overcurrent surge, and NaN corruption). The Safety Governor achieved a **100.0% rejection rate (400/400 blocked)** and **0.00% unsafe executions** (Fig. 4).

---

## 20. Results: Continuous Boundary Testing (P3-E5)

Experiment P3-E5 characterized mathematical transitions across 201 finely spaced points spanning $[-5.0, +5.0]$ margin relative to each threshold (Fig. 5):
* **Thermal ($46.0^\circ\text{C}$)**: Exactly 1 transition at $46.0^\circ\text{C}$; 100% monotonic.
* **Voltage ($22.0\text{V}$)**: Exactly 1 transition at $22.0\text{V}$; 100% monotonic.
* **Current ($40.0\text{A}$)**: Exactly 1 transition at $40.0\text{A}$; 100% monotonic.
* **SoC ($0.15$)**: Exactly 1 transition at $0.15$; 100% monotonic.

Zero off-by-one errors or floating-point leakage were detected.

---

## 21. Results: Compound Constraint Evaluation (P3-E3)

Across 300 compound multi-breach proposals (double, triple, and quadruple concurrent violations), the governor achieved:
* **Compound Rejection Rate**: **100.0% (300/300)**.
* **Concurrent Violation Recall**: **100.0% (800/800 violations detected)**.

The governor avoided premature exit, logging all concurrent breaches to ensure complete diagnostic telemetry.

---

## 22. Results: Communication-Aware Safety (P3-E6)

Across 300 communication scenarios, unsafe actions were rejected in 100% of cases in both ground contact (75/75) and orbital blackout (75/75), confirming **0 hard safety bypasses** (Fig. 6). When actions were safe, the system correctly deferred 43 cases to ground operators and authorized 107 autonomous onboard executions.

---

## 23. Results: No-Safe-Action Behavior (P3-E7)

In 150 physical dead-end scenarios where severe damage eliminated all valid recovery paths, 750 candidate proposals were evaluated:
* **Candidate Actions Approved**: **0 (0.0%)**
* **Candidate Actions Rejected**: **750 (100.0%)**
* **Safe Failure Convergence (`NO_SAFE_ACTION_AVAILABLE`)**: **150 / 150 scenarios (100.0%)**
* **Forced Unsafe Actions**: **0 (0.0%)**

---

## 24. Results: Ablation Study (P3-E8)

Ablation across 500 identical scenarios (Table 7) revealed:
* **AI Only**: 176 / 176 unsafe actions executed (**100.0%**).
* **Heuristic Rules Only**: 176 / 176 unsafe actions executed (**100.0%**). Because static rules only evaluate instantaneous telemetry, they approved proposals whose delayed counterfactual consequences caused thermal runaway.
* **AI + Safety Governor**: 0 / 176 unsafe actions executed (**0.00%**).

---

## 25. Computational Overhead

Benchmarking over 10,000 evaluations demonstrated:
* **Mean Evaluation Latency**: **$2.99\,\mu\text{s}$** ($0.0030\,\text{ms}$)
* **Median Latency**: **$2.97\,\mu\text{s}$**
* **95th Percentile Latency**: **$3.13\,\mu\text{s}$**
* **Throughput**: **$324,707.4$ evaluations / second**

Safety gating introduces zero perceptible latency on modern spacecraft flight processors.

---

## 26. Failure Cases

As documented in `docs/paper3/FAILURE_CASES.md`, software autonomy cannot prevent spacecraft loss when physical deficits exceed hardware limits (e.g., $Q_{\text{exo}} > 65\text{W}$ exceeding radiator dissipation). In such regimes, the governor's contribution is refusing to command futile or damaging cycles and safely declaring `NO_SAFE_ACTION_AVAILABLE`.

---

## 27. Discussion

The empirical findings confirm that deterministic runtime gating solves the fundamental reliability gap of aerospace AI. By enforcing physical invariants across projected counterfactual horizons, the system guarantees that high AI confidence cannot command dangerous vehicle configurations.

---

## 28. Relationship to Papers 1 and 2

* **Paper 1**: Developed counterfactual lookahead planning.
* **Paper 2**: Developed evidential Dirichlet diagnosis.
* **Paper 3**: Provides the authoritative runtime safety barrier guaranteeing execution safety regardless of upstream planner or diagnostic fallibility.

---

## 29. Limitations & Scope Boundaries

1. Validated exclusively in numerical simulation and empirical battery datasets; has not flown on orbit.
2. Zero unsafe executions are certified statistically ($p < 0.197\%$ at 95% CI) within the modeled simulation domain, not as an unconstrained universal mathematical proof.
3. Software cannot prevent loss when physical damage exceeds vehicle thermal dissipation limits.

---

## 30. Reproducibility

The entire Paper 3 benchmark suite reproduces deterministically in $4.5\,\text{s}$ via:
```bash
python3 experiments/paper3/run_all_paper3.py
```
All 51 unit tests pass via `python3 -m pytest tests/ -v`.

---

## 31. Conclusion

AstraHeal Paper 3 demonstrates that an independent, deterministic runtime Safety Governor effectively prevents unsafe autonomous recovery actions from reaching execution. Across 1,519 evaluated unsafe proposals, the system maintained zero unsafe executions, blocked 100% of adversarial proposals, and safely converged to `NO_SAFE_ACTION_AVAILABLE` during physical exhaustion, establishing a rigorous foundation for safe spacecraft autonomy.

---

## 32. References

1. S. Chien et al., "Autonomous sciencecraft experiment on the EO-1 spacecraft," *IEEE Intelligent Systems*, vol. 20, no. 5, pp. 16–24, 2005.
2. N. Muscettola, P. P. Nayak, B. Pell, and B. C. Williams, "Remote agent: To boldly go where no AI has gone before," *Artificial Intelligence*, vol. 103, no. 1–2, pp. 5–47, 1998.
3. L. Sha, "Using simplicity to control complexity," *IEEE Software*, vol. 18, no. 4, pp. 20–28, 2001.
4. M. Alshiekh et al., "Safe reinforcement learning via shielding," in *Proc. AAAI Conference on Artificial Intelligence*, vol. 32, no. 1, 2018.
5. ASTM International, "Standard guide for design of runtime assurance systems for aircraft systems," *ASTM F3269-17*, 2017.
6. C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On calibration of modern neural networks," in *Proc. ICML*, pp. 1321–1330, 2017.
7. M. Sensoy, L. Kaplan, and M. Kandemir, "Evidential deep learning to quantify classification uncertainty," in *NeurIPS*, vol. 31, pp. 3179–3189, 2018.
8. M. Thambisetty, "AstraHeal: Uncertainty-Aware Counterfactual Planning for Autonomous Spacecraft Fault Recovery," *Zenodo*, Sep. 2026. doi: 10.5281/zenodo.22233081.
9. AstraHeal Research Group, "Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management," *AstraHeal Research Series*, vol. 2, 2026.
