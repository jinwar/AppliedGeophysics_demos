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
        page.get_by_text('128.0 ms ·',exact=False).wait_for(timeout=15000)
        # Verify WAV upload and a subsequent download through the actual UI.
        from fourier_audio.model import example,write_wav
        y,fs=example('Pure tone')
        page.locator('input[type=file]').set_input_files({'name':'tone.wav','mimeType':'audio/wav','buffer':write_wav(y,fs)})
        page.get_by_text('Source: Uploaded WAV',exact=False).wait_for(timeout=30000)
        # Keep the analysis scroll container fixed while changing sidebar controls.
        page.evaluate("""() => {
            window.analysisScroller = document.querySelector('#main');
            window.analysisScroller.scrollTop = 300;
        }""")
        before=page.evaluate('window.analysisScroller.scrollTop')
        assert before>100, 'Analysis must be scrolled for the regression check'
        for label in ['512','1024','2048']:
            page.get_by_role('combobox',name='STFT window length (ms)',exact=True).select_option(label=label)
            page.get_by_text(label+'.0 ms ·',exact=False).wait_for(timeout=15000)
            page.wait_for_timeout(300)
            assert abs(page.evaluate('window.analysisScroller.scrollTop')-before)<2
        for label in ['500 Hz','1 kHz']:
            page.get_by_role('combobox',name='Frequency axis upper limit',exact=True).select_option(label=label)
            page.wait_for_timeout(1000)
            assert abs(page.evaluate('window.analysisScroller.scrollTop')-before)<2
        print('Long windows, frequency limits and scroll preservation passed',flush=True)
        # Zoom the actual Bokeh range and verify that Python sends every sample.
        page.evaluate("""() => {
            const range=Bokeh.documents.filter(d => d.get_model_by_name('waveform_time_range')).at(-1).get_model_by_name('waveform_time_range');
            range.start=1; range.end=1.01;
        }""")
        page.wait_for_function("""() => {
            const data=Bokeh.documents.filter(d => d.get_model_by_name('waveform_samples')).at(-1).get_model_by_name('waveform_samples').data;
            const t=data.time;
            return t.length>150 && t.length<170 && t[0]>=0.999
                && Math.abs((t[1]-t[0])-1/16000)<1e-9;
        }""",timeout=20000)
        print('Zoom restores individual waveform samples',flush=True)
        with page.expect_download() as event:
            page.get_by_role('button',name='Download this sound (WAV)',exact=True).click()
        assert event.value.suggested_filename=='fourier_audio.wav'
        print('WAV upload and download passed',flush=True)
        page.get_by_role('combobox',name='Example sound',exact=True).select_option(label='Do–Re–Mi: piano and violin')
        page.get_by_role('button',name='Load example',exact=True).click()
        page.get_by_text('Source: Do–Re–Mi: piano and violin',exact=False).wait_for(timeout=30000)
        page.get_by_text('6.00 s ·',exact=False).wait_for(timeout=15000)
        print('Piano and violin sequence loaded and analyzed',flush=True)
        page.goto('http://127.0.0.1:8012/filtering_browser.html',wait_until='domcontentloaded')
        page.locator('#loader').wait_for(state='hidden',timeout=120000)
        page.get_by_role('combobox',name='Experiment',exact=True).select_option(label='Narrowband interference')
        page.get_by_role('button',name='Load experiment',exact=True).click()
        page.get_by_text('Notch / band-stop · Butterworth',exact=False).wait_for(timeout=30000)
        page.get_by_text('Challenge',exact=True).click()
        page.get_by_role('button',name='Reveal clean signal',exact=True).click()
        page.get_by_text('Recovery RMSE:',exact=False).wait_for(timeout=30000)
        page.get_by_role('button',name='New noise realization',exact=True).click()
        page.get_by_role('button',name='Reveal clean signal',exact=True).wait_for(timeout=30000)
        with page.expect_download() as event:
            page.get_by_role('button',name='Download data (CSV)',exact=True).click()
        assert event.value.suggested_filename=='filtering_data.csv'
        data=Path(event.value.path()).read_text()
        assert 'clean' not in data.splitlines()[0], 'Challenge CSV must not reveal target'
        page.get_by_role('combobox',name='Filter design',exact=True).select_option(label='Ideal sharp cutoff')
        page.get_by_text('Noncausal zero-phase',exact=False).wait_for(timeout=30000)
        print('Filtering presets, challenge reveal/reset, CSV and ideal response passed',flush=True)
        browser.close()
finally:
    server.shutdown()

