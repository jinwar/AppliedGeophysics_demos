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

- Temporal view: one or two cosines, sampling interval, record duration, phase, reproducible Gaussian noise, ideal analog low-pass, sample points and one-sided FFT.
- Spatial view: a horizontal monochromatic plane wave, receiver spacing, aperture, snapshot time, and signed apparent velocity.
- Explore/Challenge modes, four presets, five guided questions, temporal CSV and complete parameter JSON downloads.
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
Challenge mode hides truth and metrics until reveal, resets on parameter edits,
and excludes clean data from CSV downloads until revealed. This is a teaching
exercise, not secure assessment: the synthetic model is available to the browser.

Four presets, expandable interpretation notes, a processing diagram, essential
Python snippets, and CSV/JSON downloads are included. SciPy is loaded only for
the filtering app in the browser. Static deployment follows the existing Pages
workflow; the `/filtering` server route is also available.
