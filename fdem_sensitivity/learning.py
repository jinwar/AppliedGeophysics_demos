NOTES = r'''
### Week 5 · FDEM: configuration, depth sensitivity, and interpretation
1. **Predict:** keep the earth fixed and switch HCP ↔ VCP. Explain the change using the depth kernels.
2. **Explore:** change spacing. Compare deeper weighting with the larger induction number.
3. **Test the approximation:** increase frequency over a conductive earth. Does apparent
   conductivity remain equal to the actual conductivity of a homogeneous earth?
4. **Challenge:** hide the earth and interpret both in-phase and quadrature. Try several starting
   models; similar fits can imply different earths. Reveal only after recording your prediction.
5. **Design:** choose a second spacing or orientation that could distinguish competing models.

### Full forward response
The empymod solver calculates the **secondary magnetic field** of infinitesimal magnetic dipoles
above two horizontal isotropic layers. Both coils are 0.1 m above ground, separated along x.
**HCP** means horizontal coil planes (vertical z magnetic moments). **VCP** means vertical coil
planes (horizontal y moments, perpendicular to the line joining coils). The primary component
for both configurations is Hₚ = −m/(4πs³). Responses are Hₛ/Hₚ × 10⁶ ppm, using exp(+iωt):
real = in-phase, imaginary = quadrature. Both components are fitted together.

### Low-induction-number (LIN) teaching overlay
The apparent conductivity conversion is σₐ = 4 Im(Hₛ/Hₚ)/(ω μ₀ s²).
It is **not a full nonlinear inversion**; it can be biased at higher induction number,
for height above ground, and over layered earth. β = s √(ω μ₀ σ/2) should be much smaller
than one for LIN assumptions. The displayed β uses the trial model and highest frequency.

The separate depth kernels assume zero coil height and LIN. With u = z/s, cumulative
sensitivity below z is R_HCP = 1/√(1+4u²), R_VCP = √(1+4u²)−2u.
Depth weighting is −dR/dz, integrating to one over the half-space. For a two-layer earth,
σₐ ≈ σ₁[1−R(h)] + σ₂R(h). These kernels show why geometry matters; they do not become
frequency-dependent merely because the full response does. They are not used as the forward solver.

### Limits and uncertainty
Point dipoles, flat isotropic nonmagnetic layers; no finite-coil integration, topography,
induced polarization, or instrument drift. Displacement currents are neglected (quasistatic EM). Air resistivity is 2 × 10¹⁴ Ω m.
Independent Gaussian noise is added to both components, with standard deviation equal to the
larger of the selected relative level and 0.1% of the global peak response. At 0% random noise
is off, but the floor is retained for fitting weights. Challenge exports omit the true earth
and clean responses. Browser challenge mode is a teaching aid, not secure exam concealment.

### Essential Python
```python
from shared.em_model import Earth
from fdem_sensitivity.model import Acquisition, forward
inphase_and_quadrature_ppm = forward(Earth(.01, .1, 20), Acquisition(spacing=10))
```
Solver: [empymod](https://empymod.emsig.xyz/), pinned NumPy-only 1.10.6 core with documented
compatibility edits. Sensitivity plots use central finite differences of the full response.
'''
