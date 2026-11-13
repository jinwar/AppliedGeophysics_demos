# Browser-compatible empymod core

Vendored from the PyPI `empymod==1.10.6` wheel (2020), the last release before
Numba became a required dependency. Upstream: https://github.com/emsig/empymod.
This is the layered-earth electromagnetic solver, not a response surrogate.
Apache-2.0 LICENSE and upstream NOTICE are included unchanged.

Local changes:
- Namespace imports changed to `shared.empymod_numpy`.
- Minimal `__init__.py` exports `dipole`, `bipole`, and `loop`; optional scripts
  and plotting utilities are not bundled.
- Removed NumPy aliases `np.infty` and `np.int` replaced by `np.inf` and `int`.
- Extracted the singleton digital-filter factor before scalar conversion for
  NumPy 2 compatibility in `transform.get_spline_values`.

The apps use the digital linear filter paths only, NumPy and SciPy. This is a
pinned legacy solver core, not the latest empymod release. Do not expose unused
transform paths as supported app options without compatibility/convergence tests.
The TDEM and FDEM wrappers document source, receiver, sign and unit conventions.
