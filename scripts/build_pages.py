"""Build a static Panel/Pyodide site from the same Python sources as the server."""
from pathlib import Path
import os
import sys
import subprocess
import tempfile
import urllib.request
import zipfile
import hashlib

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
import panel.io.convert as converter
from panel.io.convert import convert_app

OUT = ROOT / 'docs'
OUT.mkdir(exist_ok=True)
# Package the exact Python wheels with the site. The converter's default
# Bokeh CDN wheel may not exist for the installed Bokeh release.
wheel_dir = Path(tempfile.mkdtemp(prefix='panel-browser-wheels-'))
subprocess.run([sys.executable, '-m', 'pip', 'download', '--no-deps',
                '--only-binary=:all:', '--dest', str(wheel_dir),
                f'bokeh=={converter.BOKEH_VERSION}'], check=True)
bokeh_wheel = wheel_dir / f'bokeh-{converter.BOKEH_VERSION}-py3-none-any.whl'
panel_wheel = wheel_dir / f'panel-{converter.PY_VERSION}-py3-none-any.whl'
with urllib.request.urlopen(converter.PANEL_CDN_WHL, timeout=60) as response:
    panel_wheel.write_bytes(response.read())
for wheel in (bokeh_wheel, panel_wheel):
    with zipfile.ZipFile(wheel) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f'Corrupt wheel: {wheel.name}')
# Panel's converter automatically packs file: requirements into its ZIP.
converter.BOKEH_CDN_WHL = bokeh_wheel.as_uri()
converter.PANEL_CDN_WHL = panel_wheel.as_uri()
def build_app(stem, folder):
    convert_app(
        f'{stem}.py', dest_path=str(OUT), runtime='pyodide-worker',
        requirements=['numpy', 'scipy'] if folder in ('filtering', 'tdem_sounding', 'fdem_sensitivity') else ['numpy'],
        resources=[str(p.relative_to(ROOT)) for folder in (folder, 'shared')
                   for p in (ROOT / folder).rglob('*')
                   if p.is_file() and (p.suffix in ('.py', '.md') or p.name in ('LICENSE', 'NOTICE'))],
        prerender=True,
    )
    required = [f'{stem}.html', f'{stem}.js', f'{stem}.resources.zip']
    for name in required:
        if not (OUT / name).is_file():
            raise RuntimeError(f'Missing conversion output: {name}')
    # Stop on the original installation error instead of masking it as a later
    # ModuleNotFoundError. Assert the template matches our pinned Panel version.
    worker = OUT / f'{stem}.js'
    js = worker.read_text()
    old = "      type: 'status',\n      msg: `Error while installing packages`\n    });\n  }"
    new = "      type: 'error',\n      msg: `Python package installation failed: ${e}`\n    });\n    return;\n  }"
    if old not in js:
        raise RuntimeError('Panel worker template changed; review error handling')
    js = js.replace(old, new)
    if 'emfs:packed_wheels/bokeh-' not in js or 'emfs:packed_wheels/panel-' not in js:
        raise RuntimeError('Browser wheels were not bundled')
    # Content-address runtime assets so browsers cannot mix a new page with a
    # cached old worker or package archive after a deployment.
    archive = OUT / f'{stem}.resources.zip'
    archive_name = f'{stem}.{hashlib.sha256(archive.read_bytes()).hexdigest()[:12]}.resources.zip'
    archive.rename(OUT / archive_name)
    js = js.replace(f'{stem}.resources.zip', archive_name)
    worker_name = f'{stem}.{hashlib.sha256(js.encode()).hexdigest()[:12]}.js'
    (OUT / worker_name).write_text(js)
    worker.unlink()
    html = OUT / f'{stem}.html'
    html.write_text(html.read_text().replace(f'{stem}.js', worker_name))


for stem, folder in [('sampling_browser', 'sampling_aliasing'), ('fourier_browser', 'fourier_audio'), ('filtering_browser', 'filtering'), ('tdem_browser', 'tdem_sounding'), ('fdem_browser', 'fdem_sensitivity')]:
    build_app(stem, folder)
(OUT / '.nojekyll').touch()
(OUT / 'index.html').write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Applied Geophysics II · Interactive laboratories</title>
<style>body{margin:0;font:18px/1.65 system-ui,sans-serif;color:#12344a;background:#f5f8fa}header{background:#12344a;color:white;padding:22px 6vw}main{max-width:900px;margin:60px auto;padding:0 24px}h1{font-size:clamp(30px,5vw,48px);line-height:1.15}article{background:white;border:1px solid #dae4e9;border-radius:16px;padding:32px;margin-top:32px}a{display:inline-block;background:#008c95;color:white;padding:12px 20px;border-radius:8px;text-decoration:none}small{color:#526875}footer{margin-top:40px}</style></head>
<body><header>Colorado School of Mines · Spring 2027</header><main>
<small>APPLIED GEOPHYSICS II</small><h1>Interactive field laboratory</h1>
<p>Change a physical model, inspect synthetic measurements, and test what the observations can resolve.</p>
<article><small>LABORATORY 01</small><h2>Sampling &amp; aliasing</h2>
<p>Explore sampling frequency, record length, and the different waves that can produce identical measurements.</p>
<a href="sampling_browser.html">Open the laboratory →</a>
<p><small>The first visit downloads the Python runtime. Allow a little time for the controls to become ready. Calculations run on your device.</small></p></article>
<article><small>LABORATORY 02</small><h2>Fourier transform · sound laboratory</h2><p>Record a short sound, hear it back, and explore its waveform, frequency spectrum, and spectrogram.</p><a href="fourier_browser.html">Open the sound laboratory →</a><p><small>Microphone recording stays on your device. Example sounds and WAV uploads are also available.</small></p></article>
<article><small>LABORATORY 03</small><h2>Filtering &amp; signal recovery</h2><p>Build a noisy measurement, design a filter, and discover what recovery preserves and what it damages.</p><a href="filtering_browser.html">Open the filtering laboratory →</a></article>
<article><small>LABORATORY 04 · WEEKS 3–4</small><h2>TDEM sounding</h2><p>Explore EM diffusion, loop size, time gates, and non-unique layered-earth fits.</p><a href="tdem_browser.html">Open the TDEM laboratory →</a></article>
<article><small>LABORATORY 05 · WEEK 5</small><h2>FDEM depth sensitivity</h2><p>Compare coil geometries, in-phase and quadrature responses, and apparent conductivity.</p><a href="fdem_browser.html">Open the FDEM laboratory →</a></article>
<footer><small>Explore → Predict → Explain</small></footer></main></body></html>''')
print(f'Static site built in {OUT}')

