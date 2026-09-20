# AstraHeal Paper 3 — Formal Statistical Analysis & Significance Verification

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Date**: September 2026  
**Auditor**: Formal Statistics & Aerospace Verification Pipeline  

---

## 1. Statistical Treatment of Zero Observed Unsafe Executions

A critical scientific pitfall when evaluating safety-critical aerospace systems is claiming "zero risk" or "100% universal safety" based on finite empirical trials. Zero observed events in a sample of size $N$ does not imply zero probability in the population.

To provide rigorous, publishable bounds, we evaluate all unsafe proposals injected across Experiments P3-E1, P3-E4, P3-E7, and P3-E8:

$$\text{Total Controlled Unsafe Proposals Evaluated: } N = 1,519$$
$$\text{Total Unsafe Actions Executed: } k = 0$$

### Exact Confidence Bounds
1. **Wilson Score 95% Confidence Interval**:
   $$[0.0000\%,\; 0.2523\%]$$
2. **Clopper-Pearson Exact Binomial 95% Upper Bound**:
   $$p_{\text{upper}} = 1 - \alpha^{1/N} = 1 - (0.05)^{1/1519} = 0.001970 \quad (< 0.1970\%)$$

> **Formal Scientific Claim**:  
> Under the evaluated simulation domain, the true probability of the deterministic safety governor executing an unsafe proposal is statistically bounded below **0.197%** at the 95% confidence level.

---

## 2. Hypothesis H1: Baseline Safety Enforcement (Paired McNemar Test)

In Experiment P3-E1, 500 identical recovery proposal scenarios (307 safe, 193 unsafe) were evaluated under two architectures:
* **System A (Ungoverned AI)**: Executed 193 / 193 unsafe actions ($100.0\%$).
* **System B (Governed AI)**: Executed 0 / 193 unsafe actions ($0.0\%$).

### $2 \times 2$ Contingency Table for Unsafe Proposal Executions
| | Governed AI Executed | Governed AI Blocked | Total |
|---|---|---|---|
| **Ungoverned AI Executed** | 0 | 193 ($b$) | 193 |
| **Ungoverned AI Blocked** | 0 ($c$) | 0 | 0 |
| **Total** | 0 | 193 | 193 |

### Test Statistics
* **McNemar's Chi-Square with Continuity Correction**:
  $$\chi^2 = \frac{(|b - c| - 1)^2}{b + c} = \frac{(193 - 1)^2}{193} = 191.01$$
* **Degrees of Freedom**: $\text{df} = 1$
* **p-value**:
  $$p = 1.92 \times 10^{-43} \quad (\ll 0.001)$$
* **Conclusion**: **Hypothesis H1 is strongly supported with extreme statistical significance.** Deterministic safety gating eliminates unsafe action execution compared to ungoverned AI.

---

## 3. Effect Size Analysis (Cohen's $h$)

To quantify the magnitude of safety improvement independent of sample size:

$$h = 2 \arcsin(\sqrt{p_1}) - 2 \arcsin(\sqrt{p_2})$$
$$h = 2 \arcsin(\sqrt{1.0}) - 2 \arcsin(\sqrt{0.0}) = 2\left(\frac{\pi}{2}\right) - 0 = \pi \approx 3.1416$$

According to Cohen's established benchmarks ($h = 0.2$ small, $0.5$ medium, $0.8$ large), an effect size of $h = 3.1416$ represents an **exceptionally large effect**, confirming that the safety difference is not a marginal statistical artifact but a fundamental architectural shift.

---

## 4. Computational Overhead Profiling Statistics

Evaluated across $N = 10,000$ independent benchmark evaluations:

| Metric | Measured Value | Flight Avionics Implication |
|---|---|---|
| **Sample Size** | $10,000$ evaluations | High statistical power |
| **Mean Evaluation Latency** | **$2.99\,\mu\text{s}$** ($0.0030\,\text{ms}$) | Negligible overhead on onboard flight computer |
| **Median Latency** | **$2.97\,\mu\text{s}$** | Deterministic timing distribution |
| **95th Percentile Latency** | **$3.13\,\mu\text{s}$** | Minimal jitter |
| **99th Percentile Latency** | **$3.36\,\mu\text{s}$** | Tightly bounded tail latency |
| **Throughput** | **$324,707.4$ evals / sec** | Capable of vetting thousands of candidates per second |
| **Constraints Checked per Action** | 6 physical checks | $100\%$ constraint coverage |
