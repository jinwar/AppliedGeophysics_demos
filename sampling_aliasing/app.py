"""Panel UI. Run through server.py to get both the home page and this app."""
import io
import json
import numpy as np
import panel as pn
from bokeh.models import Span
from sampling_aliasing.model import temporal, spatial
from shared.style import plot, template, NAVY, TEAL, ORANGE

pn.extension(sizing_mode='stretch_width')

def create_app():
    mode = pn.widgets.RadioButtonGroup(name='Mode', options=['Explore', 'Challenge'], value='Explore')
    f1 = pn.widgets.IntSlider(name='Signal frequency 1 (Hz)', start=1, end=150, value=30)
    f2 = pn.widgets.IntSlider(name='Signal frequency 2 (Hz)', start=1, end=150, value=80)
    a2 = pn.widgets.FloatSlider(name='Second component amplitude', start=0, end=1, step=.1, value=0)
    dt = pn.widgets.FloatSlider(name='Sampling interval (ms)', start=1, end=50, step=1, value=10)
    duration = pn.widgets.FloatSlider(name='Record length (s)', start=.2, end=4, step=.1, value=1)
    phase = pn.widgets.IntSlider(name='Phase (degrees)', start=0, end=180, value=0, step=5)
    noise = pn.widgets.FloatSlider(name='Noise standard deviation', start=0, end=.5, step=.05, value=0)
    seed = pn.widgets.IntInput(name='Noise seed', value=42, start=0, end=1000000)
    aa = pn.widgets.Checkbox(name='Ideal pre-sampling low-pass (cutoff 0.45 fs)')
    reveal = pn.widgets.Checkbox(name='Reveal model and alias', value=True)
    preset = pn.widgets.Select(name='Experiment', options=['Custom', 'Well sampled', 'Temporal alias', 'Nyquist boundary', 'Two close frequencies'], value='Custom')
    def apply_preset(event):
        values = {'Well sampled': (20,80,0,5,1,0), 'Temporal alias':(80,80,0,10,1,0),
                  'Nyquist boundary':(50,80,0,10,1,90), 'Two close frequencies':(30,33,1,5,.2,0)}
        if event.new in values:
            f1.value,f2.value,a2.value,dt.value,duration.value,phase.value=values[event.new]
            aa.value=False
            noise.value=0
    preset.param.watch(apply_preset, 'value')
    def change_mode(event):
        reveal.value=event.new=='Explore'
    mode.param.watch(change_mode, 'value')
    args = dict(f1=f1, f2=f2, a2=a2, dt_ms=dt, duration=duration,
                phase_deg=phase, noise=noise, seed=seed, antialias=aa)
    def temporal_view(show, **kw):
        d = temporal(**kw)
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
        summary=f"**Sampling rate:** {d['fs']:.1f} Hz · **Nyquist:** {d['fs']/2:.1f} Hz · **FFT spacing:** {d['fs']/d['n']:.2f} Hz · **Samples:** {d['n']}"
        if show:
            active=[(kw['f1'],1,d['signed'][0],d['gains'][0]),(kw['f2'],kw['a2'],d['signed'][1],d['gains'][1])]
            summary+='\n\n'+ ' · '.join(f"{f:g} Hz → {abs(a):g} Hz" + (' (removed before sampling)' if not gain else '') for f,amp,a,gain in active if amp)
        return pn.Column(pn.pane.Markdown(summary),p,s,
            pn.pane.Markdown('**Read the plots:** The orange curve is an analytically equivalent signal at the sample times, not an estimate fitted to noisy data. FFT peaks can leak between bins. Longer records reduce bin spacing; faster sampling raises the Nyquist limit. At exactly Nyquist, phase information is lost—use a sampling rate strictly greater than twice the highest frequency.'))
    temporal_panel=pn.bind(temporal_view,show=reveal,**args)
    sf=pn.widgets.IntSlider(name='Wave frequency (Hz)',start=5,end=100,value=30)
    velocity=pn.widgets.IntSlider(name='True horizontal phase velocity (m/s)',start=200,end=3000,step=100,value=600)
    spacing=pn.widgets.IntSlider(name='Receiver spacing (m)',start=1,end=50,value=15)
    nr=pn.widgets.IntSlider(name='Number of receivers',start=8,end=64,value=24)
    time=pn.widgets.FloatSlider(name='Snapshot time (s)',start=0,end=.1,step=.001,value=0)
    def spatial_view(frequency,velocity,spacing,receivers,time,show):
        d=spatial(frequency,velocity,spacing,receivers,time)
        p=plot('Plane wave along a receiver line', 'Distance (m)',height=340)
        if show:
            p.line(d['dense'],d['true'],color=NAVY,line_width=2,legend_label='True wave')
            p.line(d['dense'],d['alias'],color=ORANGE,line_width=2,line_dash='dashed',legend_label='Spatial alias')
        p.scatter(d['x'],d['y'],color=TEAL,size=8,legend_label='Receivers')
        p.legend.click_policy='hide'
        text=f"**Wavelength:** {velocity/frequency:.1f} m · **Spacing must be less than:** {velocity/(2*frequency):.1f} m · **Aperture:** {d['x'][-1]:.0f} m"
        if show:
            va=d['apparent_velocity']
            text+=f"\n\n**Signed aliased wavenumber:** {d['ka']:.4f} cycles/m · **Apparent velocity:** "+('undefined (zero wavenumber)' if va is None else f'{va:.1f} m/s')
        return pn.Column(pn.pane.Markdown(text),p,pn.pane.Markdown('Move **Snapshot time** to follow the wave. A negative apparent velocity means the sampled wave appears to travel backward. This is a monochromatic horizontal plane wave, cos[2π(ft − kx)]; time is treated as continuous here so spatial aliasing can be isolated. More receivers extend aperture; smaller spacing raises the spatial Nyquist limit.'))
    spatial_panel=pn.Column(pn.Row(sf,velocity),pn.Row(spacing,nr),time,
        pn.bind(spatial_view,frequency=sf,velocity=velocity,spacing=spacing,receivers=nr,time=time,show=reveal))
    def data_download():
        d=temporal(**{k:w.value for k,w in args.items()})
        out=io.StringIO(); np.savetxt(out,np.column_stack([d['t'],d['y'],d['clean']]),delimiter=',',header='time_s,observed_amplitude,noise_free_amplitude',comments='');out.seek(0);return out
    def parameters_download():
        values={k:w.value for k,w in args.items()}
        values['spatial']={k:w.value for k,w in dict(frequency=sf,velocity=velocity,spacing=spacing,receivers=nr,time=time).items()}
        return io.StringIO(json.dumps(values,indent=2))
    challenges=pn.pane.Markdown('''### Predict → experiment → explain
1. Select **Temporal alias**. With 80 Hz sampled at 100 samples/s, predict the observed frequency. Reveal the curves to check.
2. Select **Nyquist boundary**. Change phase from 90° to 0°. Why can a nonzero signal produce zero samples?
3. Select **Two close frequencies**. Increase record length without changing sampling interval. Which spectral feature improves?
4. Turn on the second component and the ideal low-pass. Can filtering after sampling undo an alias? Explain why the filter here must act before sampling.
5. In **Receiver spacing**, use 30 Hz and 600 m/s. Predict the largest safe spacing. Try 15 m and advance snapshot time: why does the apparent propagation reverse?

Challenge mode hides model curves and alias values until you choose **Reveal**. This is an exploration exercise, not an automatically graded test.''')
    return template('Sampling & aliasing',[
        pn.pane.Markdown('## When different waves produce the same measurements\nExplore how recording interval, duration, and receiver spacing limit what seismic data can tell us.'),
        pn.Tabs(('Time sampling',pn.Column(temporal_panel)),('Receiver spacing',spatial_panel),('Challenges',challenges),dynamic=True),
        pn.Row(pn.widgets.FileDownload(label='Download temporal samples (CSV)',filename='samples.csv',callback=data_download),pn.widgets.FileDownload(label='Download parameters (JSON)',filename='parameters.json',callback=parameters_download))
    ],[mode,preset,reveal,pn.pane.Markdown('### Time sampling controls'),f1,f2,a2,dt,duration,phase,noise,seed,aa,
       pn.pane.Markdown('The ideal low-pass removes components at or above 0.45 fs before sampling. Noise is added afterward. All data are synthetic; amplitudes are normalized.')])
