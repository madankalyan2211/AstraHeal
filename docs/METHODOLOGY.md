# AstraHeal Research Methodology

## 1. Physics-Informed Digital Twin Formulation

### A. Orbital Irradiance & Eclipse
Low Earth Orbit (LEO) period $T$ for semi-major axis $a = R_E + h$ ($h = 550\text{km}$):
$$T = 2\pi \sqrt{\frac{a^3}{\mu_E}} \approx 5740\text{ seconds } (\sim 95.6\text{ min})$$

Eclipse fraction is modeled geometrically with smooth penumbra transitions ($20\text{s}$).

### B. Thevenin 1-RC Battery Equivalent Circuit
Terminal voltage $V_t$ under load current $I$:
$$V_t = V_{oc}(SoC) - I R_0 - V_{pol}$$
$$\frac{dV_{pol}}{dt} = \frac{I}{C_p} - \frac{V_{pol}}{R_p C_p}$$

Thermal balance with Joule heating, polarization loss, Arrhenius acceleration ($T > 45^\circ\text{C}$), and radiator sink dissipation:
$$C_{th} \frac{dT}{dt} = I^2 R_0 + \frac{V_{pol}^2}{R_p} + \dot{Q}_{exo} - h_{rad}(T - T_{sink})$$

## 2. Uncertainty Quantification Methodology

### A. Epistemic Uncertainty (Out-of-Distribution Distance)
$$D_M(\mathbf{x}, \mu_k) = \sqrt{(\mathbf{x} - \mu_k)^T \Sigma_k^{-1} (\mathbf{x} - \mu_k)}$$
$$u_{epistemic} = \sigma\left(\alpha \cdot (\min_{k} D_M - D_{threshold})\right)$$

### B. Aleatoric Uncertainty (Predictive Shannon Entropy)
$$u_{aleatoric} = \frac{-\sum_{k=1}^K p_k \log_2(p_k)}{\log_2(K)}$$

## 3. Safety-Gated Recovery Planning

Candidates $a \in \mathcal{A}$ are simulated forward in cloned digital twins over lookahead horizon $H$.
- Hard constraint filter:
  $$\text{Governor}(a) = \begin{cases} \text{APPROVED} & \text{if } \max(T) \le 46^\circ\text{C} \land \min(V) \ge 22\text{V} \land \max(I) \le 40\text{A} \land \min(SoC) \ge 0.15 \\ \text{REJECTED} & \text{otherwise} \end{cases}$$
- Soft multi-objective ranking on approved candidates:
  $$\text{Score}(a) = w_{surv} S_{surv} + w_{pay} S_{pay} + w_{eng} S_{eng} + w_{rev} S_{rev} - w_{dis} C_{dis}$$
