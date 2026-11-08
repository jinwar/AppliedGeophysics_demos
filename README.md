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
with a `file://` URL will not work. The first visit downloads Python, Panel,
Bokeh, and NumPy from their CDNs; allow the loading indicator to finish before
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
