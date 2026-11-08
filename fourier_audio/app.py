import base64
import io
import json
import wave
import numpy as np
import panel as pn
from bokeh.models import ColorBar, LinearColorMapper, ColumnDataSource, Range1d
from bokeh.palettes import Inferno256
from fourier_audio.model import example, analyze, read_wav, write_wav, waveform_view
from fourier_audio.recorder import Microphone
from fourier_audio.learning import learning_section
from shared.style import template, plot, TEAL

pn.extension(sizing_mode='stretch_width')

def create_app(browser=False):
    source=pn.widgets.Select(name='Example sound',options=['Pure tone','Two simultaneous tones','Two sequential tones','Chirp: rising pitch'],value='Pure tone')
    load=pn.widgets.Button(name='Load example',button_type='primary')
    upload=pn.widgets.FileInput(name='Upload PCM WAV (max 20 MB)',accept='.wav')
    mic=Microphone(height=125,sizing_mode='stretch_width')
    window=pn.widgets.Select(name='Window function',options=['Hann','Rectangular'])
    length=pn.widgets.Select(name='STFT window length (ms)',options=[16,32,64,128,256,512,1024,2048],value=64)
    overlap=pn.widgets.Select(name='STFT overlap',options={'50%':.5,'75%':.75,'90%':.9},value=.75)
    limit=pn.widgets.Select(name='Frequency axis upper limit',options={'500 Hz':500,'1 kHz':1000,'2 kHz':2000,'5 kHz':5000,'10 kHz':10000,'Nyquist':0},value=5000)
    contrast=pn.widgets.IntSlider(name='Spectrogram dynamic range (dB)',start=30,end=100,step=10,value=70)
    note=pn.pane.Markdown('**Source:** Pure tone example · 440 Hz')
    playback=pn.pane.HTML(height=65)
    # Keep the same models and layout mounted when analysis controls change.
    summary=pn.pane.Markdown()
    trace=ColumnDataSource(dict(time=[],amplitude=[]),name='waveform_samples')
    spectrum=ColumnDataSource(dict(frequency=[],amplitude=[]))
    spectrogram=ColumnDataSource(dict(image=[],x=[],y=[],dw=[],dh=[]))
    p=plot('1 · Waveform: amplitude through time','Time (s)',height=220)
    p.x_range=Range1d(0,3,name='waveform_time_range')
    p.lod_factor=1  # Never skip samples while interacting with the waveform.
    p.line('time','amplitude',source=trace,color=TEAL)
    s=plot('2 · Fourier spectrum: whole recording','Frequency (Hz)','Amplitude (relative to full scale)',250)
    s.x_range=Range1d(0,5000)
    s.line('frequency','amplitude',source=spectrum,color=TEAL,line_width=2)
    h=plot('3 · Spectrogram: how frequency changes through time','Time (s)','Frequency (Hz)',320)
    h.y_range=Range1d(0,5000)
    mapper=LinearColorMapper(palette=Inferno256,low=-contrast.value,high=0)
    h.image(image='image',x='x',y='y',dw='dw',dh='dh',source=spectrogram,color_mapper=mapper)
    h.add_layout(ColorBar(color_mapper=mapper,title='dB relative to peak'),'right')
    plots=pn.Column(summary,p,s,h)
    audio={'y':example('Pure tone')[0],'fs':16000}
    def update_waveform():
        trace.data=waveform_view(audio['y'],audio['fs'],p.x_range.start,p.x_range.end)
    def waveform_range_changed(attr,old,new):
        update_waveform()
    p.x_range.on_change('start',waveform_range_changed)
    p.x_range.on_change('end',waveform_range_changed)
    def update_plots(*events):
        y,fs=audio['y'],audio['fs']
        d=analyze(y,fs,length.value,overlap.value,window.value)
        top=min(limit.value or fs/2,fs/2)
        update_waveform()
        keep=d['frequency']<=top
        spectrum.data=dict(frequency=d['frequency'][keep],amplitude=d['amplitude'][keep])
        s.x_range.start=0;s.x_range.end=top
        keep=d['stft_frequency']<=top
        df=fs/d['n']; step=d['hop']/fs
        mapper.low=-contrast.value
        spectrogram.data=dict(image=[d['db'][keep]],x=[d['time'][0]-step/2],y=[-df/2],
                              dw=[len(d['time'])*step],dh=[keep.sum()*df])
        h.y_range.start=0;h.y_range.end=top
        dominant='None (silence)' if d['dominant'] is None else f"{d['dominant']:.1f} Hz"
        warnings=' **Near full-scale samples: possible clipping.**' if np.max(np.abs(y))>=.999 else ''
        if np.max(np.abs(y))<1e-5: warnings+=' **Very quiet or silent recording.**'
        summary.object=(f"**Duration:** {len(y)/fs:.2f} s · **Sample rate:** {fs:g} Hz · **Nyquist:** {fs/2:g} Hz\n\n**Largest spectral peak:** {dominant} · **Whole-record FFT spacing:** {fs/len(y):.2f} Hz\n\n**STFT window:** {d['n']/fs*1000:.1f} ms · **STFT bin spacing:** {df:.1f} Hz · **Hop:** {step*1000:.1f} ms"+warnings)
    def set_audio(y,fs,label):
        audio.update(y=np.asarray(y,dtype=float)[:int(fs*10)],fs=int(fs))
        p.x_range.start=0
        p.x_range.end=len(audio['y'])/audio['fs']
        p.x_range.reset_start=0
        p.x_range.reset_end=p.x_range.end
        note.object='**Source:** '+label
        uri=base64.b64encode(write_wav(audio['y'],audio['fs'])).decode()
        playback.object=f'<audio controls preload="metadata" style="width:100%" src="data:audio/wav;base64,{uri}"></audio>'
        update_plots()
    def load_example(event):
        y,fs=example(source.value);set_audio(y,fs,source.value)
    load.on_click(load_example)
    def uploaded(event):
        if not event.new:return
        try:
            y,fs,truncated=read_wav(event.new)
            set_audio(y,fs,'Uploaded WAV (channels averaged to mono)'+(' · first 10 seconds only' if truncated else ''))
        except (ValueError,wave.Error,EOFError) as e: note.object='**Could not load WAV:** '+str(e)
    upload.param.watch(uploaded,'value')
    def recorded(event):
        try:
            data=json.loads(event.new); fs=int(data['fs'])
            if not 1000<=fs<=192000: raise ValueError('Unsupported sample rate')
            y=np.frombuffer(base64.b64decode(data['pcm'],validate=True),dtype='<f4').copy()
            if not 32<=len(y)<=fs*10 or not np.isfinite(y).all():raise ValueError('Recording is empty or invalid')
            set_audio(y,fs,'Microphone recording')
        except (ValueError,KeyError,TypeError) as e:note.object='**Recording error:** '+str(e)
    mic.param.watch(recorded,'payload')
    for w in [window,length,overlap,limit,contrast]:w.param.watch(update_plots,'value')
    download=pn.widgets.FileDownload(label='Download this sound (WAV)',filename='fourier_audio.wav',callback=lambda:io.BytesIO(write_wav(audio['y'],audio['fs'])))
    set_audio(audio['y'],audio['fs'],'Pure tone example · 440 Hz')
    privacy=('Audio stays on your device; it is not uploaded or saved by this GitHub Pages app.' if browser else 'This server version sends audio to the Python server for analysis; it is not saved to disk by the app.')
    return template('Fourier transform · sound laboratory',[
        pn.pane.Markdown('## Hear a sound. See its frequencies.\nRecord a vowel, whistle, clap, or changing pitch. Compare the full-record Fourier transform with a short-time Fourier transform (STFT).'),
        mic,pn.pane.Markdown(privacy+' Recording stops automatically after 10 seconds. For microphone access, use a full browser over HTTPS.'),
        note,playback,plots,download,
        pn.Accordion(('Try these experiments',pn.pane.Markdown('''1. Load **Pure tone**, then **Two simultaneous tones**. Match the peaks to what you hear.
2. Compare **Two simultaneous tones** with **Two sequential tones**. Both contain 440 and 880 Hz; which plot tells you when each tone occurs?
3. Load **Chirp**, then change the STFT window from 16 to 2048 ms. Compare frequency sharpness with time smearing.
4. Record a sustained vowel or hum. Identify a fundamental and its harmonics. The largest peak need not be the fundamental.
5. Record a clap. Why does a short event occupy many frequencies?''')),
        ('How to read the analysis',pn.pane.Markdown('''The waveform shows normalized digital amplitude, not calibrated sound pressure. Zoom into a few milliseconds to see individual oscillations. The overview retains local extrema at their actual sample times; zooming reveals all samples in the visible interval. This display reduction does not affect the FFT or STFT. The FFT and STFT remove the recording's mean (DC). One-sided amplitudes are corrected for the window's coherent gain; DC and Nyquist are not doubled. The spectrogram uses **20 log₁₀(amplitude / peak STFT amplitude)**, so 0 dB is the strongest time-frequency bin in this sound, not 0 dB SPL.

STFT windows are centered on the displayed time coordinates; only complete windows are used. Windows longer than the recording are shortened to its duration. Longer windows give finer frequency spacing but smear changes in time. Greater overlap gives more closely spaced snapshots; it does not improve the underlying frequency resolution. A Hann window reduces leakage at the expense of a wider spectral peak. The displayed bin spacing is not the same as the minimum resolvable frequency separation.

Stereo uploads are averaged to mono. Browser/device microphone processing may affect amplitudes. Examples are synthetic; recordings are limited to 10 seconds.'''))),
        learning_section()],
        [pn.pane.Markdown('### Sound source'),source,load,pn.pane.Markdown('**Or upload uncompressed PCM WAV** (first 10 s; max 20 MB)'),upload,
         pn.pane.Markdown('### Analysis controls'),window,length,overlap,limit,contrast])
