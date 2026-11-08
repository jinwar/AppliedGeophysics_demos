"""Build a static Panel/Pyodide site from the same Python sources as the server."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from panel.io.convert import convert_app

OUT = ROOT / 'docs'
OUT.mkdir(exist_ok=True)
convert_app(
    'sampling_browser.py', dest_path=str(OUT), runtime='pyodide-worker',
    requirements=['numpy'],
    resources=[str(p.relative_to(ROOT)) for folder in ('sampling_aliasing', 'shared')
               for p in (ROOT / folder).glob('*.py')],
    prerender=True,
)
required = ['sampling_browser.html', 'sampling_browser.js', 'sampling_browser.resources.zip']
for name in required:
    if not (OUT / name).is_file():
        raise RuntimeError(f'Missing conversion output: {name}')
(OUT / '.nojekyll').touch()
(OUT / 'index.html').write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Applied Geophysics II · Interactive laboratories</title>
<style>body{margin:0;font:18px/1.65 system-ui,sans-serif;color:#12344a;background:#f5f8fa}header{background:#12344a;color:white;padding:22px 6vw}main{max-width:900px;margin:60px auto;padding:0 24px}h1{font-size:clamp(30px,5vw,48px);line-height:1.15}article{background:white;border:1px solid #dae4e9;border-radius:16px;padding:32px;margin-top:32px}a{display:inline-block;background:#008c95;color:white;padding:12px 20px;border-radius:8px;text-decoration:none}small{color:#526875}footer{margin-top:40px}</style></head>
<body><header>Colorado School of Mines · Spring 2027</header><main>
<small>APPLIED GEOPHYSICS II</small><h1>Interactive field laboratory</h1>
<p>Change a physical model, inspect synthetic measurements, and test what the observations can resolve.</p>
<article><small>LABORATORY 01</small><h2>Sampling &amp; aliasing</h2>
<p>Explore sampling interval, record length, receiver spacing, and the different waves that can produce identical measurements.</p>
<a href="sampling_browser.html">Open the laboratory →</a>
<p><small>The first visit downloads the Python runtime. Allow a little time for the controls to become ready. Calculations run on your device.</small></p></article>
<footer><small>Explore → Predict → Explain</small></footer></main></body></html>''')
print(f'Static site built in {OUT}')
