"""End-to-end static-site checks using Chromium's synthetic microphone."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',8012),partial(SimpleHTTPRequestHandler,directory=str(ROOT/'docs')))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        page=browser.new_page()
        page.on('pageerror',lambda e:print('Browser error:',e,flush=True))
        page.goto('http://127.0.0.1:8012/fourier_browser.html',wait_until='domcontentloaded')
        # A changed analysis confirms Python initialized; the prerender is inert.
        page.locator('#loader').wait_for(state='hidden',timeout=120000)
        page.get_by_role('combobox',name='Example sound',exact=True).select_option(label='Two sequential tones')
        page.get_by_role('button',name='Load example',exact=True).click()
        page.get_by_text('Source: Two sequential tones',exact=False).wait_for(timeout=30000)
        print('Example callback passed',flush=True)
        page.get_by_role('button',name='Record audio',exact=True).click()
        page.get_by_text('Recording…',exact=False).wait_for(timeout=20000)
        page.wait_for_timeout(1500)  # Capture a nonempty synthetic sound.
        page.get_by_role('button',name='Stop',exact=True).click()
        page.get_by_text('Source: Microphone recording',exact=False).wait_for(timeout=30000)
        print('Synthetic microphone recording and analysis passed',flush=True)
        page.get_by_role('combobox',name='STFT window length (ms)',exact=True).select_option(label='128')
        page.get_by_text('STFT window:',exact=True).wait_for(timeout=15000)
        # Verify WAV upload and a subsequent download through the actual UI.
        from fourier_audio.model import example,write_wav
        y,fs=example('Pure tone')
        page.locator('input[type=file]').set_input_files({'name':'tone.wav','mimeType':'audio/wav','buffer':write_wav(y,fs)})
        page.get_by_text('Source: Uploaded WAV',exact=False).wait_for(timeout=30000)
        with page.expect_download() as event:
            page.get_by_role('button',name='Download this sound (WAV)',exact=True).click()
        assert event.value.suggested_filename=='fourier_audio.wav'
        print('WAV upload and download passed',flush=True)
        browser.close()
finally:
    server.shutdown()
