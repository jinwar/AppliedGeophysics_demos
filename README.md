# Applied Geophysics II · Interactive laboratories

Panel applications for Colorado School of Mines, Spring 2027. Each laboratory lives in its own folder; `shared/` holds reusable presentation utilities. The index at `/` links to the first laboratory at `/sampling-aliasing`.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Open http://localhost:5006. For model checks: `pip install pytest` then `python -m pytest -q`.

## Render

Create a Render Blueprint from this repository using `render.yaml`. It installs pinned dependencies and runs `python server.py`, reading Render's `PORT` and `RENDER_EXTERNAL_HOSTNAME`. No credentials are required. The supplied plan is free; cold starts are possible. Custom domains must also be added to the websocket origin list in `server.py`.

## Sampling and aliasing

- One temporal view with one or two cosines, sampling frequency in Hz, record duration, phase, reproducible Gaussian noise, ideal analog low-pass, sample points and one-sided FFT.
- Four presets, optional model/alias reveal, temporal CSV and parameter JSON downloads.
- Sampling frequency ranges from 20 to 1000 Hz (100 Hz by default); exported parameters include both frequency and the corresponding sampling interval.
- Transparent NumPy forward models are separate from the Panel UI in `sampling_aliasing/model.py`.

The orange curve is the analytically folded, noise-free baseband equivalent, not a numerical reconstruction or inversion. Signed folding preserves phase at every sample. Exactly Nyquist is deliberately demonstrated as ambiguous. The spectrum uses a rectangular window, no zero padding, and amplitude normalization (DC/Nyquist bins are not doubled). Requested record length is rounded to an integer sample count; FFT bin spacing is fs/N. The last sample is at (N−1)dt. Ideal filtering removes components at or above 0.45 fs before samples are taken; measurement noise is added after filtering. Spatial apparent velocity assumes continuous time and known positive temporal frequency.

Deployment references: [Panel server](https://panel.holoviz.org/en/docs/latest/how_to/server/programmatic.html), [Render Blueprint](https://render.com/docs/blueprint-spec).

## GitHub Pages · Python in the browser

The same Panel app can run without Render using Pyodide in a Web Worker. The
Python model and UI remain shared with the server version. `sampling_browser.py`
is the browser entry point, and `scripts/build_pages.py` bundles the local
`sampling_aliasing/` and `shared/` modules into an accompanying resource archive.
The home link is relative so navigation works under a GitHub project subpath.

Build and try locally:

```bash
python scripts/build_pages.py
python -m http.server 8000 --directory docs
```

Open http://localhost:8000/index.html. Serve the whole output folder: the app
needs its HTML, JavaScript worker, and `.resources.zip` file. Opening the HTML
with a `file://` URL will not work. The first visit downloads Python and NumPy from their CDNs, plus the bundled Panel and Bokeh wheels; allow the loading indicator to finish before
using controls. Browser caching reduces later download costs. Runtime packages
must be available for Pyodide; its NumPy version is chosen by the Pyodide
runtime rather than the native Python pin in `requirements.txt`.

In repository **Settings → Pages → Build and deployment → Source**, select
**GitHub Actions** once. `.github/workflows/pages.yml` then tests, builds, and
publishes on every push to `main`. If Pages was not enabled when the workflow
first ran, rerun it from the Actions tab after selecting the source. The expected
site is https://jinwar.github.io/AppliedGeophysics_demos/.

Generated `docs/` files are workflow artifacts, not hand-maintained source.
The optional Render configuration remains available for server deployments.

The build bundles matching Panel and Bokeh wheels in the app resource archive. It validates both wheels and fails early if downloads are unavailable, so a successful deployment cannot rely on a missing Bokeh CDN wheel. Browser startup preserves installation errors instead of continuing with an incomplete environment.

## Fourier transform · audio laboratory

The second app (`fourier_audio/`, browser entry point `fourier_browser.py`) lets
students record up to 10 seconds, upload uncompressed PCM WAV files, or load
synthetic sounds. It provides playback, WAV download, a waveform, a whole-record
FFT, and a short-time Fourier spectrogram. Hann/rectangular windows, window
length, overlap, frequency limits, and color range are adjustable. Examples
include a pure tone, simultaneous tones, sequential tones, and a chirp.

The browser asks for microphone permission only after **Record audio** is
clicked. MediaRecorder captures audio and Web Audio decodes it to mono PCM;
Panel/NumPy performs the transforms inside Pyodide. The microphone stops after
10 seconds or on **Stop**. HTTPS or localhost and a browser with microphone
support are required. No audio is uploaded by the GitHub Pages version. The
optional Python server version receives audio in memory for analysis and
therefore displays a different privacy notice. PCM WAV uploads support 8/16/24/32
bit integer samples, average channels to mono, and use the first 10 seconds.

Spectrogram colors are relative amplitude dB, not calibrated sound pressure.
FFT amplitude is one-sided and corrected for the selected window's coherent
gain. STFT uses only complete windows; overlap changes the hop, not frequency
resolution. Tests check known frequencies, amplitudes, sequential timing,
chirp tracking, silence, WAV conversion, and duration limits.


## Filtering and signal recovery

The third lab (`filtering/`, entry point `filtering_browser.py`) synthesizes
seismic pulses or sinusoidal mixtures with reproducible Gaussian noise, drift,
and narrowband interference. It compares Butterworth low/high/band-pass and
band-stop filters with an ideal sharp FFT mask. Controls expose cutoffs, order,
and causal versus forward–backward processing. The plotted response includes
the squared gain of forward–backward filtering. Ideal filtering uses a three-times
zero-padded record and crops the result; boundary effects remain.

Linked time views show measured, recovered, clean, and removed components.
Spectra retain physical relative amplitudes. Full-record recovery RMSE/SNR
include distortion and edges; first-event peak errors use a local matching window.
Apply filter and Reveal true signal are independent controls, both off on startup.
With filtering off, only the measurement is shown; recovery traces and diagnostics
appear when filtering is enabled. Figure 1 always shows estimated input SNR and adds output SNR when filtering is
enabled, using the synthetic truth as reference. True-signal traces and the other
error metrics are shown only when revealed. CSV downloads follow these controls. Frequency spectra use a
logarithmic amplitude axis; zero-amplitude bins are omitted. Parameter downloads
include both toggle states.

Four presets, expandable interpretation notes, a processing diagram, essential
Python snippets, and CSV/JSON downloads are included. SciPy is loaded only for
the filtering app in the browser. Static deployment follows the existing Pages
workflow; the `/filtering` server route is also available.

## TDEM sounding and FDEM depth sensitivity

These two course labs implement the model → measurement → interpretation workflow
from **Course Outline and App list**: TDEM supports weeks 3–4; FDEM supports week 5.
They run entirely in the browser through the existing Panel/Pyodide GitHub Pages
build. No simulation server, account, API key, or SimPEG installation is required.

- `tdem_sounding/`, browser entry point `tdem_browser.py`, server route
  `/tdem-sounding`: central square-loop step-off sounding, adjustable loop side,
  current, time range and gate count; induced voltage and weighted residuals.
- `fdem_sensitivity/`, browser entry point `fdem_browser.py`, server route
  `/fdem-sensitivity`: HCP/VCP dipole configurations, spacing and frequency range;
  in-phase and quadrature, LIN apparent conductivity and depth-weighting overlays.
- Both offer two-layer conductivity/thickness controls, four resettable cases,
  reproducible noise, Explore/Challenge modes, an independently adjustable trial
  earth, bounded nonlinear least-squares fitting, finite-difference sensitivity,
  interpretation prompts, and CSV/JSON exports. Challenge exports omit the earth
  and clean responses until revealed. This is a teaching aid, not exam security.

**Simulation engine:** the NumPy/SciPy core of `empymod==1.10.6`, vendored in
`shared/empymod_numpy/` with Apache-2.0 license, notices, and documented namespace
and NumPy 2 compatibility edits. This pre-Numba release avoids a compiled JIT
requirement in Pyodide. It is deliberately pinned and is not current empymod.
SimPEG 0.26.0 is used only to generate independent numerical test fixtures;
`python scripts/generate_em_references.py` requires that optional development
package. Normal tests use committed fixtures without importing SimPEG.

Both solvers use quasistatic, isotropic, nonmagnetic horizontal layers, one finite
layer above a half-space, 0.1 m instrument height, and negligible air conductivity.
Displacement currents, IP, lateral structure, and instrument electronics are
excluded. TDEM assumes instantaneous switch-off and a 1 m² effective receiver
area; gates are point samples, not time averages. Five Gauss points integrate one
side of the square loop and symmetry supplies the other three. TDEM's log plot
shows absolute voltage; fitting and exported data preserve signs. FDEM uses full
layered-earth responses, not LIN kernels, for both simulation and fitting. LIN
apparent conductivity and zero-height kernels are explicitly labeled teaching
approximations; their failure at higher induction numbers is part of the lesson.

Noise standard deviation is the larger of relative noise and 0.1% of the global
peak response. At zero noise the observations are exactly clean, while the floor
remains for fitting weights. Fitting uses log conductivity and thickness, bounds
1–300 mS/m and 1–100 m, and at most 35 optimizer evaluations (finite-difference
calls are additional). A local optimum is not proof of uniqueness. Sensitivities
are derivatives with respect to log parameters at the trial model divided by
measurement uncertainty; they are not depth-of-investigation boundaries.

Validation covers all four earth presets against independent SimPEG TDEM and
both FDEM orientations (0.3% relative tolerance plus a small absolute tolerance),
homogeneous-layer invariance, current scaling, late-time TEM decay, FDEM LIN
limits, normalized depth kernels, noise-free recovery, session isolation, hidden
truth exports, and invalid acquisitions. The Pages browser test also exercises
both Pyodide workers, fitting, sensitivity, downloads, and challenge/reset flows.
