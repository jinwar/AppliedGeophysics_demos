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
