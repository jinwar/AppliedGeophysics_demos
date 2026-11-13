NOTES = r'''
### Weeks 3–4 · TDEM: diffusion, acquisition, and interpretation
1. **Predict:** compare a conductive and resistive basement. Which gates change most?
2. **Explore:** increase loop size or current. Separate stronger signal from improved resolution.
3. **Acquire less:** remove early or late gates, add noise, and refit. Which parameters become ambiguous?
4. **Challenge:** load a case, switch to Challenge, and ask a partner to interpret it. The earth controls,
   true profile, and clean curve are hidden until Reveal. Downloaded challenge data omit the truth.
5. **Defend:** start fits from different trial earths. Report data misfit and what remains unconstrained.

### What is calculated?
The empymod layered-earth solver evaluates Maxwell's equations using Hankel and Fourier digital
filters. A horizontal **square electric transmitter loop** at 0.1 m above ground carries a steady
current, switched off instantaneously at t = 0. A central, horizontal **1 m² effective-area receiver**
at the same height measures induced voltage. The positive plotted polarity is
V = −μ₀ Aᵣ dH_step-off/dt. The impulse response of H equals −dH_step-off/dt.
One side of the square is integrated with five Gauss points and multiplied by four by symmetry.
Displacement currents are neglected (quasistatic EM). Air resistivity is 2 × 10¹⁴ Ω m. The model has one finite layer above an infinite basement.

At late time in a homogeneous earth, voltage scales as
V ∝ (I Aₜ) Aᵣ σ^(3/2) t^(−5/2). Diffusion length scales as √(t / (μσ));
it is a broad sensitivity scale, not a sharp depth boundary. The app computes the layered
response rather than substituting this asymptote.

### Limits and uncertainty
Isotropic, nonmagnetic horizontal layers; no topography, induced polarization, lateral targets,
finite shutoff ramp, or receiver electronics. Gates are **point samples**, not interval averages.
The log plot shows voltage magnitudes; CSV and fitting preserve signs. Error bars show ±1 standard
deviation where their lower magnitude bound stays positive. Noise combines a relative term with
an absolute floor of 0.1% of peak signal (the larger term is used). At 0% no random noise is added,
but the floor still defines fitting weights. A misfit near one is expected only when the assumed
noise model is appropriate. A two-layer fit is not evidence that the real earth has two layers.

### Essential Python
```python
from shared.em_model import Earth
from tdem_sounding.model import Acquisition, forward
voltage_nV = forward(Earth(.01, .1, 20), Acquisition(side=40))
```
Solver: [empymod](https://empymod.emsig.xyz/), pinned NumPy-only 1.10.6 core with documented
compatibility edits. See the repository's solver provenance and numerical validation.
'''
