"""Interactive filtering lab, shared by the Panel server and Pyodide worker."""
import io
import json
from dataclasses import asdict
import numpy as np
import panel as pn
from bokeh.models import ColumnDataSource, Range1d
from shared.style import plot, template, NAVY, TEAL, ORANGE
from .model import Parameters, PRESETS, experiment, spectrum
from .learning import NOTES, CODE, FLOW


def create_app():
    pn.extension()
    w = {}
    def slider(key, name, start, end, step):
        w[key] = pn.widgets.FloatSlider(name=name, start=start, end=end, step=step,
                                       value=getattr(Parameters(), key))
        return w[key]
    def select(key, name, options):
        w[key] = pn.widgets.Select(name=name, options=options, value=getattr(Parameters(), key))
        return w[key]
    mode = pn.widgets.RadioButtonGroup(name='Mode', options=['Explore', 'Challenge'], value='Explore')
    preset = pn.widgets.Select(name='Experiment', options=list(PRESETS))
    load = pn.widgets.Button(name='Load experiment', button_type='primary')
    reveal = pn.widgets.Button(name='Reveal clean signal', button_type='success', visible=False)
    new_noise = pn.widgets.Button(name='New noise realization')
    w['seed'] = pn.widgets.IntInput(name='Noise seed', value=12, start=0, end=1000000)
    source_controls = pn.Column(
        select('kind', 'Clean signal', ['Seismic pulse', 'Two seismic pulses', 'Sinusoids']),
        slider('frequency', 'Pulse / first frequency (Hz)', 5, 120, 1),
        slider('amplitude', 'First amplitude', .1, 2, .1),
        slider('arrival', 'First arrival (s)', .3, 1.3, .01),
        slider('separation', 'Pulse separation (s)', .02, .4, .005),
        slider('frequency2', 'Second sinusoid (Hz)', 5, 150, 1),
        slider('amplitude2', 'Second amplitude', .1, 2, .1))
    noise_controls = pn.Column(
        slider('noise', 'Random noise σ', 0, 1, .02),
        slider('drift', 'Drift amplitude', 0, 1.5, .05),
        slider('drift_frequency', 'Drift frequency (Hz)', .5, 10, .5),
        slider('interference', 'Interference amplitude', 0, 1.5, .05),
        slider('interference_frequency', 'Interference frequency (Hz)', 5, 200, 1),
        w['seed'], new_noise)
    filter_controls = pn.Column(
        select('filter_type', 'Filter type', ['Low-pass', 'High-pass', 'Band-pass', 'Notch / band-stop']),
        select('design', 'Filter design', ['Butterworth', 'Ideal sharp cutoff']),
        slider('low', 'Lower cutoff (Hz)', 1, 220, 1),
        slider('high', 'Upper cutoff (Hz)', 2, 240, 1))
    w['order'] = pn.widgets.IntSlider(name='Prototype order', start=1, end=8, value=4)
    filter_controls.extend([w['order'], select('phase', 'Phase behavior', ['Zero-phase', 'Causal'])])
    state = {'revealed': False, 'updating': False, 'result': None}
    trace = ColumnDataSource(data=dict(t=[], clean=[], observed=[], recovered=[], removed=[]), name='filtering_traces')
    spectra = ColumnDataSource(data=dict(f=[], clean=[], observed=[], recovered=[]))
    response = ColumnDataSource(data=dict(f=[], gain=[], phase=[]))
    time_range = Range1d(0, 2, name='filtering_time_range')
    ptime = plot('01 · Recover the signal', 'Time (s)', height=330)
    ptime.x_range = time_range
    ptime.line('t', 'observed', source=trace, color='#94a3b8', alpha=.8, legend_label='Measured')
    clean_line = ptime.line('t', 'clean', source=trace, color=NAVY, line_width=2, legend_label='Clean target')
    ptime.line('t', 'recovered', source=trace, color=TEAL, line_width=2, legend_label='Recovered')
    pspec = plot('02 · Compare frequency content', 'Frequency (Hz)', height=280)
    pspec.x_range = Range1d(0, 250)
    pspec.line('f', 'observed', source=spectra, color='#94a3b8', legend_label='Measured')
    clean_spec = pspec.line('f', 'clean', source=spectra, color=NAVY, line_width=2, legend_label='Clean target')
    pspec.line('f', 'recovered', source=spectra, color=TEAL, line_width=2, legend_label='Recovered')
    premoved = plot('03 · What did the filter remove?', 'Time (s)', height=220)
    premoved.x_range = time_range
    premoved.line('t', 'removed', source=trace, color=ORANGE)
    pgain = plot('04 · Applied filter response', 'Frequency (Hz)', 'Amplitude gain', height=240)
    pgain.x_range = pspec.x_range
    pgain.line('f', 'gain', source=response, color=TEAL, line_width=2)
    pphase = plot('Phase response', 'Frequency (Hz)', 'Phase (degrees)', height=220)
    pphase.x_range = pspec.x_range
    pphase.line('f', 'phase', source=response, color=NAVY)
    for fig in [ptime, pspec]:
        fig.legend.location = 'top_right'
    metrics = pn.pane.Markdown()
    status = pn.pane.Markdown()
    error = pn.pane.Alert('', alert_type='warning', visible=False)

    def current():
        return Parameters(**{k: control.value for k, control in w.items()})

    def update(event=None):
        if state['updating']:
            return
        if event is not None and event.obj is not mode:
            state['revealed'] = False
        p = current()
        w['frequency2'].visible = p.kind == 'Sinusoids'
        w['amplitude2'].visible = p.kind != 'Seismic pulse'
        w['arrival'].visible = p.kind != 'Sinusoids'
        w['separation'].visible = p.kind == 'Two seismic pulses'
        w['order'].disabled = w['phase'].disabled = p.design == 'Ideal sharp cutoff'
        w['low'].visible = p.filter_type != 'Low-pass'
        w['high'].visible = p.filter_type != 'High-pass'
        try:
            result = experiment(p)
        except ValueError as exc:
            error.object = str(exc) + ' Plots retain the last valid result.'
            error.visible = True
            csv.disabled = params.disabled = True
            return
        error.visible = False
        csv.disabled = params.disabled = False
        state['result'] = result
        show = mode.value == 'Explore' or state['revealed']
        reveal.visible = mode.value == 'Challenge' and not show
        clean_line.visible = clean_spec.visible = show
        trace.data = {key: result[key] if key != 'clean' or show else np.full_like(result[key], np.nan)
                      for key in ['t', 'clean', 'observed', 'recovered', 'removed']}
        f, measured_spectrum = spectrum(result['observed'], p.fs)
        spectra.data = dict(f=f, observed=measured_spectrum,
            clean=spectrum(result['clean'], p.fs)[1] if show else np.full_like(f, np.nan),
            recovered=spectrum(result['recovered'], p.fs)[1])
        response.data = dict(f=result['frequency'], gain=result['gain'], phase=result['phase'])
        m = result['metrics']
        if show:
            metrics.object = (f"**Input SNR:** {m['input_snr']:.1f} dB　 **Output SNR:** {m['output_snr']:.1f} dB　 "
                              f"**Recovery RMSE:** {m['rmse']:.3f}")
            if 'timing_ms' in m:
                metrics.object += f"\n\n**First peak timing error:** {m['timing_ms']:+.1f} ms　 **Peak amplitude error:** {m['amplitude_pct']:+.1f}%"
        else:
            metrics.object = '**Challenge:** predict the result, choose your filter, then reveal the target and recovery errors.'
        phase_label = 'Noncausal zero-phase' if p.design == 'Ideal sharp cutoff' else p.phase
        status.object = f'**{p.filter_type} · {p.design} · {phase_label}** | Seed {p.seed} | 500 Hz sampling · 2 s record'

    def load_preset(event):
        state['updating'] = True
        for key, value in asdict(Parameters(**PRESETS[preset.value])).items():
            if key in w:
                w[key].value = value
        state['updating'] = False
        state['revealed'] = False
        update()

    def reveal_target(event):
        state['revealed'] = True
        update()

    def change_mode(event):
        state['revealed'] = False
        update()

    def csv_download():
        r = state['result']
        keys = ['t', 'observed', 'recovered', 'removed']
        if mode.value == 'Explore' or state['revealed']:
            keys.insert(1, 'clean')
        buffer = io.StringIO()
        np.savetxt(buffer, np.column_stack([r[k] for k in keys]), delimiter=',', header=','.join(keys), comments='')
        buffer.seek(0)
        return buffer

    def parameter_download():
        return io.StringIO(json.dumps(state['result']['parameters'], indent=2))

    csv = pn.widgets.FileDownload(label='Download data (CSV)', filename='filtering_data.csv', callback=csv_download)
    params = pn.widgets.FileDownload(label='Download parameters', filename='filtering_parameters.json', callback=parameter_download)
    for control in w.values():
        control.param.watch(update, 'value')
    mode.param.watch(change_mode, 'value')
    load.on_click(load_preset)
    reveal.on_click(reveal_target)
    new_noise.on_click(lambda event: setattr(w['seed'], 'value', (w['seed'].value + 1) % 1000001))
    update()
    sidebar = [pn.pane.Markdown('### Build a measurement'), mode, preset, load,
        pn.Accordion(('Signal', source_controls), ('Noise & interference', noise_controls), active=[0]),
        pn.pane.Markdown('### Recover the target'), filter_controls, reveal]
    main = [pn.pane.Markdown('## Filtering & signal recovery\nDoes a cleaner-looking trace preserve the signal you want?'),
        status, error, metrics, ptime, pspec, premoved, pgain,
        pn.Accordion(('Phase response', pn.pane.Bokeh(pphase)),
                     ('Experiments & interpretation', pn.pane.Markdown(NOTES)),
                     ('Processing diagram', pn.pane.HTML(FLOW)),
                     ('Essential Python', pn.pane.Markdown(CODE)), active=[]),
        pn.Row(csv, params)]
    return template('Filtering & signal recovery', main, sidebar)
