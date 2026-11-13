from fdem_sensitivity.app import create_app
app = create_app()
app.site_url = './index.html'
app.servable()
