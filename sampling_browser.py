"""Static deployment entry point; bundled modules execute inside Pyodide."""
from sampling_aliasing.app import create_app

app = create_app()
app.site_url = './index.html'
app.servable()
