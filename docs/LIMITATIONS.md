# AstraHeal System Limitations & Scientific Scope

1. **Subsystem Scope**: Focuses primarily on Electrical Power Systems (EPS), battery electro-thermal degradation, and power bus load distribution. Detailed 6-DOF orbital attitude dynamics and chemical propulsion are abstract.
2. **Thermal Node Granularity**: Employs a lumped single-node thermal capacitance model ($C_{th} = 4500\text{ J/K}$) rather than a multi-node finite element mesh.
3. **Planar Orbital Mechanics**: Assumes circular Low Earth Orbit without J2 gravitational nodal regression or seasonal beta-angle precession.
4. **Offline Uncertainty Priors**: Physics prior centroids and diagonal variances in the evidential engine are calibrated analytically rather than fitted to terabyte-scale flight archives.
