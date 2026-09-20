# AstraHeal Paper 4 — Formal Statistical Analysis & Empirical Verification

**Date**: 2026-09-13  
**Status**: VERIFIED  
**Methodology**: Clopper-Pearson Exact Binomial Bounds, Paired McNemar $\chi^2$ Tests with Continuity Correction, Student-t Paired Tests, Cohen's $d$ and $h$ Effect Sizes  

---

## 1. Safety Invariant Enforcement & Exact Confidence Bounds

In mission-critical autonomous aerospace software, observing zero unsafe action executions does not imply zero mathematical risk. We compute the **exact Clopper-Pearson 95% confidence upper bound** on the probability of an unsafe execution reaching the spacecraft actuators:

$$\theta_{\text{unsafe}} \le 1 - \alpha^{1/N}$$

* **Total Evaluated Missions ($N$) Across All 8 Experiments**: 1320
* **Observed Executed Unsafe Actions**: 0 ($0.00\%$)
* **Exact Clopper-Pearson 95% Upper Bound**: $< 0.2791\%$
* **Total Recorded Governor Rejections**: 40,711 unsafe proposals deterministically intercepted

### P4-E1 Sequential Fault Recovery Sub-Cohort
* **Cohort Size**: 100 multi-cycle sequential missions
* **Observed Unsafe Executions**: 0 ($0.00\%$)
* **Sub-Cohort 95% Upper Bound**: $< 3.6217\%$
* **Governor Rejections in P4-E1**: 8,132

---

## 2. Mission Payload Delivery Significance (Counterfactual Planning Contribution)

Paired comparison of delivered payload utility ($N=50$ identical seeds) between Full AstraHeal and Ablation without Counterfactual Lookahead Planning:

* **Full AstraHeal Mean Payload**: 574.0 Wh ($100.0\%$ nominal)
* **No Lookahead Mean Payload**: 212.1 Wh ($36.95\%$ nominal)
* **Delivered Utility Advantage**: $+361.9$ Wh ($+170.6\%$ increase)
* **Paired Student-t Statistic**: $t(49) = 21.09$
* **Statistical Significance**: $p = 3.10e-26$ ($p < 10^{-15}$, Extremely Significant)
* **Cohen's $d$ Effect Size**: $d = 2.98$ (Huge Effect Size, $d > 0.8$ threshold)

---

## 3. Architecture Survival Proportions (McNemar Paired Tests)

Paired survival comparison of identical scenario seeds between Full AstraHeal and comparative baselines:

| Comparison Architecture | AstraHeal Wins ($b$) | Baseline Wins ($c$) | McNemar $\chi^2$ | $p$-value | Cohen's $h$ | Significance |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| BASELINE_PASSIVE | 0 | 0 | 0.00 | 1.00e+00 | 0.0000 | p = 1.0000 |
| BASELINE_BLIND_SAFE_MODE | 0 | 0 | 0.00 | 1.00e+00 | 0.0000 | p = 1.0000 |
| ABLATION_NO_GOVERNOR | 0 | 0 | 0.00 | 1.00e+00 | 0.0000 | p = 1.0000 |
| ABLATION_NO_LOOKAHEAD | 0 | 0 | 0.00 | 1.00e+00 | 0.0000 | p = 1.0000 |
| ABLATION_NO_UNCERTAINTY | 0 | 0 | 0.00 | 1.00e+00 | 0.0000 | p = 1.0000 |
