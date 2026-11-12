from sampling_aliasing.learning import learning_section
"""Panel UI. Run through server.py to get both the home page and this app."""
import io
import json
import numpy as np
import panel as pn
from bokeh.models import Span
from sampling_aliasing.model import temporal
from shared.style import plot, template, NAVY, TEAL, ORANGE

pn.extension(sizing_mode='stretch_width')

def create_app():
    f1 = pn.widgets.IntSlider(name='Signal frequency 1 (Hz)', start=1, end=150, value=30)
    f2 = pn.widgets.IntSlider(name='Signal frequency 2 (Hz)', start=1, end=150, value=80)
    a2 = pn.widgets.FloatSlider(name='Second component amplitude', start=0, end=1, step=.1, value=0)
    fs = pn.widgets.IntSlider(name='Sampling frequency (Hz)', start=20, end=1000, step=1, value=100)
    duration = pn.widgets.FloatSlider(name='Record length (s)', start=.2, end=4, step=.1, value=1)
    phase = pn.widgets.IntSlider(name='Phase (degrees)', start=0, end=180, value=0, step=5)
    noise = pn.widgets.FloatSlider(name='Noise standard deviation', start=0, end=.5, step=.05, value=0)
    seed = pn.widgets.IntInput(name='Noise seed', value=42, start=0, end=1000000)
    aa = pn.widgets.Checkbox(name='Ideal pre-sampling low-pass (cutoff 0.45 fs)')
    reveal = pn.widgets.Checkbox(name='Reveal model and alias', value=True)
    preset = pn.widgets.Select(name='Experiment', options=['Custom', 'Well sampled', 'Temporal alias', 'Nyquist boundary', 'Two close frequencies'], value='Custom')
    def apply_preset(event):
        values = {'Well sampled': (20,80,0,200,1,0), 'Temporal alias':(80,80,0,100,1,0),
                  'Nyquist boundary':(50,80,0,100,1,90), 'Two close frequencies':(30,33,1,200,.2,0)}
        if event.new in values:
            f1.value,f2.value,a2.value,fs.value,duration.value,phase.value=values[event.new]
            aa.value=False
            noise.value=0
    preset.param.watch(apply_preset, 'value')
    args = dict(f1=f1, f2=f2, a2=a2, fs_hz=fs, duration=duration,
                phase_deg=phase, noise=noise, seed=seed, antialias=aa)
    def sampled_data(fs_hz, **kw):
        return temporal(dt_ms=1000 / fs_hz, **kw)

    def temporal_view(show, **kw):
        d = sampled_data(**kw)
        p=plot('Continuous signal → discrete measurements', 'Time (s)')
        if show:
            p.line(d['dense'],d['true'],color=NAVY,alpha=.65,line_width=2,legend_label='Original signal')
            p.line(d['dense'],d['alias'],color=ORANGE,line_width=2,line_dash='dashed',legend_label='Baseband equivalent (noise-free)')
            if kw['antialias']:
                p.line(d['dense'],d['passed'],color=TEAL,line_width=2,legend_label='After ideal low-pass')
        p.scatter(d['t'],d['y'],color=TEAL,size=6,legend_label='Samples')
        p.legend.click_policy='hide'
        s=plot('Measured spectrum • rectangular window', 'Frequency (Hz)', 'One-sided amplitude', 250)
        s.line(d['frequency'],d['spectrum'],color=TEAL,line_width=2)
        s.scatter(d['frequency'],d['spectrum'],color=TEAL,size=4)
        s.add_layout(Span(location=d['fs']/2,dimension='height',line_color=ORANGE,line_dash='dashed'))
        summary=f"**Sampling frequency:** {d['fs']:.1f} Hz · **Nyquist:** {d['fs']/2:.1f} Hz · **FFT spacing:** {d['fs']/d['n']:.2f} Hz · **Samples:** {d['n']}"
        if show:
            active=[(kw['f1'],1,d['signed'][0],d['gains'][0]),(kw['f2'],kw['a2'],d['signed'][1],d['gains'][1])]
            summary+='\n\n'+ ' · '.join(f"{f:g} Hz → {abs(a):g} Hz" + (' (removed before sampling)' if not gain else '') for f,amp,a,gain in active if amp)
        return pn.Column(pn.pane.Markdown(summary),p,s,
            pn.pane.Markdown('**Read the plots:** The orange curve is an analytically equivalent signal at the sample times, not an estimate fitted to noisy data. FFT peaks can leak between bins. Longer records reduce bin spacing; faster sampling raises the Nyquist limit. At exactly Nyquist, phase information is lost—use a sampling rate strictly greater than twice the highest frequency.'))
    temporal_panel=pn.bind(temporal_view,show=reveal,**args)
    def data_download():
        d=sampled_data(**{k:w.value for k,w in args.items()})
        out=io.StringIO(); np.savetxt(out,np.column_stack([d['t'],d['y'],d['clean']]),delimiter=',',header='time_s,observed_amplitude,noise_free_amplitude',comments='');out.seek(0);return out
    def parameters_download():
        values={k:w.value for k,w in args.items()}
        values['dt_ms'] = 1000 / values['fs_hz']
        return io.StringIO(json.dumps(values,indent=2))
    return template('Sampling & aliasing',[
        pn.pane.Markdown('## When different waves produce the same measurements\nExplore how sampling frequency and record duration limit what seismic data can tell us.'),
        pn.Column(temporal_panel),
        pn.Row(pn.widgets.FileDownload(label='Download temporal samples (CSV)',filename='samples.csv',callback=data_download),pn.widgets.FileDownload(label='Download parameters (JSON)',filename='parameters.json',callback=parameters_download)),
        learning_section()
    ],[preset,reveal,pn.pane.Markdown('### Time sampling controls'),f1,f2,a2,fs,duration,phase,noise,seed,aa,
       pn.pane.Markdown('The ideal low-pass removes components at or above 0.45 fs before sampling. Noise is added afterward. All data are synthetic; amplitudes are normalized.')])
