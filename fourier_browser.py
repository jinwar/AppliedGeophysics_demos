from fourier_audio.app import create_app
app = create_app(browser=True)
app.site_url = './index.html'
app.servable()
