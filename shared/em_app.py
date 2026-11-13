"""Linked model/data/interpretation views for the two course EM laboratories."""
import io
import json
from dataclasses import asdict
import numpy as np
import panel as pn
from bokeh.models import ColumnDataSource, Range1d, LogScale, LogTicker, LogTickFormatter
from shared.style import plot, template, NAVY, TEAL, ORANGE
from shared.em_model import Earth, PRESETS, observe, profile, fit_earth, sensitivity, MU0


def logarithmic(fig, axis):
    setattr(fig, axis+'_scale', LogScale())
    ax = getattr(fig, axis+'axis')
    ax.ticker = LogTicker()
    ax.formatter = LogTickFormatter()
    getattr(fig, axis+'grid').ticker = ax[0].ticker


def create_em_app(kind):
    pn.extension()
    temporal = kind == 'tdem'
    if temporal:
        from tdem_sounding import model
        from tdem_sounding.learning import NOTES as notes
    else:
        from fdem_sensitivity import model
        from fdem_sensitivity.learning import NOTES as notes
    title = 'TDEM sounding' if temporal else 'FDEM depth sensitivity'
    state = {'busy': False, 'result': None, 'fit': ''}
    mode = pn.widgets.Select(name='Mode', options=['Explore', 'Challenge'])
    reveal = pn.widgets.Toggle(name='Reveal earth model', value=False, button_type='success')
    preset = pn.widgets.Select(name='Experiment', options=list(PRESETS))
    load = pn.widgets.Button(name='Load experiment', button_type='primary')
    reset = pn.widgets.Button(name='Reset laboratory')
    seed = pn.widgets.IntInput(name='Noise seed', value=12, start=0, end=1000000)
    noise = pn.widgets.FloatSlider(name='Noise (%)', start=0, end=10, step=.5, value=3)
    reroll = pn.widgets.Button(name='New noise realization')

    def earth_controls(prefix, earth):
        return [pn.widgets.FloatSlider(name=prefix+'top conductivity (mS/m)', start=1, end=300, step=1, value=earth.sigma1*1000),
            pn.widgets.FloatSlider(name=prefix+'basement conductivity (mS/m)', start=1, end=300, step=1, value=earth.sigma2*1000),
            pn.widgets.FloatSlider(name=prefix+'top thickness (m)', start=1, end=100, step=1, value=earth.thickness)]
    truth = earth_controls('Earth: ', Earth())
    trial = earth_controls('Trial: ', Earth(.03,.03,30))
    truth_box = pn.Column(*truth)
    trial_box = pn.Column(*trial)
    settings = {}
    def setting(key, widget):
        settings[key] = widget
        return widget
    if temporal:
        acquisition_widgets = [
            setting('side', pn.widgets.FloatSlider(name='Square loop side (m)', start=10,end=100,step=5,value=40)),
            setting('current', pn.widgets.FloatSlider(name='Transmitter current (A)',start=1,end=10,step=1,value=1)),
            setting('first_ms', pn.widgets.Select(name='First gate (ms)',options=[.01,.03,.1,.3],value=.03)),
            setting('last_ms', pn.widgets.Select(name='Last gate (ms)',options=[.3,1.,3.,10.],value=3.)),
            setting('gates', pn.widgets.IntSlider(name='Number of time gates',start=8,end=30,step=2,value=20))]
    else:
        acquisition_widgets = [
            setting('spacing', pn.widgets.FloatSlider(name='Coil spacing (m)',start=1,end=40,step=1,value=10)),
            setting('orientation', pn.widgets.Select(name='Coil orientation',options=model.ORIENTATIONS)),
            setting('first_hz', pn.widgets.Select(name='Minimum frequency (Hz)',options=[10.,100.,1000.],value=100.)),
            setting('last_hz', pn.widgets.Select(name='Maximum frequency (Hz)',options=[1000.,10000.,100000.],value=100000.))]
    defaults = {k:w.value for k,w in settings.items()}
    fit_button = pn.widgets.Button(name='Fit trial model to measurements', button_type='primary')
    fit_message = pn.pane.Markdown('Adjust the trial model, then fit. Try different starting models to test uniqueness.')
    status = pn.pane.Markdown()
    alert = pn.pane.Alert('',alert_type='warning',visible=False)
    data = ColumnDataSource(dict(x=[],observed=[],trial=[],truth=[],lower=[],upper=[]),name=kind+'_response')
    second = ColumnDataSource(dict(x=[],observed=[],trial=[],truth=[]),name=kind+'_second')
    earth_true = ColumnDataSource(dict(conductivity=[],depth=[]),name=kind+'_earth_truth')
    earth_trial = ColumnDataSource(dict(conductivity=[],depth=[]),name=kind+'_earth_trial')
    earth_plot = plot('01 · Earth and interpretation', 'Conductivity (mS/m)', 'Depth below surface (m)',260)
    logarithmic(earth_plot,'x')
    earth_plot.y_range = Range1d(120,0)
    earth_plot.line('conductivity','depth',source=earth_true,color=NAVY,line_width=3,legend_label='True earth')
    earth_plot.line('conductivity','depth',source=earth_trial,color=ORANGE,line_width=3,line_dash='dashed',legend_label='Trial earth')
    xlabel = 'Time after current shutoff (ms)' if temporal else 'Frequency (Hz)'
    response = plot('02 · Transient voltage' if temporal else '02 · Quadrature response',xlabel,
                    '|Voltage| (nV, 1 m² receiver)' if temporal else 'Secondary / primary (ppm)',330)
    logarithmic(response,'x')
    if temporal:
        logarithmic(response,'y')
    response.line('x','truth',source=data,color=NAVY,legend_label='Noise-free response',line_width=2)
    response.line('x','trial',source=data,color=ORANGE,legend_label='Trial prediction',line_width=2)
    response.scatter('x','observed',source=data,color=TEAL,size=7,legend_label='Measurement')
    response.segment('x','lower','x','upper',source=data,color=TEAL,alpha=.5)
    second_plot = plot('03 · Weighted residuals' if temporal else '03 · In-phase response',xlabel,
                       '(Trial − measured) / uncertainty' if temporal else 'Secondary / primary (ppm)',260)
    logarithmic(second_plot,'x')
    second_plot.line('x','trial',source=second,color=ORANGE,legend_label='Trial prediction' if not temporal else 'Weighted residual')
    if not temporal:
        second_plot.scatter('x','observed',source=second,color=TEAL,size=6,legend_label='Measurement')
        second_plot.line('x','truth',source=second,color=NAVY,legend_label='Noise-free response')
    sensitivity_source = ColumnDataSource(dict(x=[],top=[],basement=[],thickness=[]),name=kind+'_sensitivity')
    sensitivity_plot = plot('04 · Sensitivity around the trial model',xlabel,'Response derivative / data uncertainty',260)
    logarithmic(sensitivity_plot,'x')
    for key,label,color in [('top','Top conductivity',NAVY),('basement','Basement conductivity',TEAL),('thickness','Top thickness',ORANGE)]:
        sensitivity_plot.line('x',key,source=sensitivity_source,color=color,line_width=2,legend_label=label)
    sensitivity_toggle = pn.widgets.Toggle(name='Calculate sensitivity',value=False)
    extras = []
    if not temporal:
        apparent_source = ColumnDataSource(dict(x=[],observed=[],trial=[]),name='fdem_apparent')
        apparent_plot = plot('04 · Apparent conductivity (LIN conversion)',xlabel,'Apparent conductivity (mS/m)',260)
        logarithmic(apparent_plot,'x')
        apparent_plot.scatter('x','observed',source=apparent_source,color=TEAL,size=6,legend_label='Measurement')
        apparent_plot.line('x','trial',source=apparent_source,color=ORANGE,legend_label='Trial prediction')
        weights = ColumnDataSource(dict(z=[],hcp=[],vcp=[]))
        weighting_plot = plot('05 · Low-induction depth weighting', 'Sensitivity density (1/m)', 'Depth (m)',260)
        weighting_plot.y_range=Range1d(60,0)
        weighting_plot.line('hcp','z',source=weights,color=NAVY,legend_label='HCP: vertical dipoles',line_width=2)
        weighting_plot.line('vcp','z',source=weights,color=TEAL,legend_label='VCP: horizontal dipoles',line_width=2)
        extras=[apparent_plot,weighting_plot]
    for fig in [earth_plot,response,second_plot,sensitivity_plot]+extras:
        fig.legend.location='top_right'
        fig.legend.click_policy='hide'
        fig.legend.label_text_font_size='9pt'

    def earth_from(controls):
        return Earth(controls[0].value/1000,controls[1].value/1000,controls[2].value)

    def assign_earth(controls, earth):
        for control,value in zip(controls,[earth.sigma1*1000,earth.sigma2*1000,earth.thickness]):
            control.value=float(value)

    def update(event=None):
        if state['busy']:
            return
        visible = mode.value == 'Explore' or reveal.value
        truth_box.visible = visible
        preset.visible = load.visible = visible
        reveal.visible = mode.value == 'Challenge'
        try:
            earth=earth_from(truth); alternative=earth_from(trial)
            acq=model.Acquisition(**{k:w.value for k,w in settings.items()})
            x=acq.axis*(1000 if temporal else 1)
            clean=model.forward(earth,acq)
            measured,uncertainty=observe(clean,noise.value,seed.value)
            predicted=model.forward(alternative,acq)
            if not np.all(np.isfinite(clean)) or not np.all(np.isfinite(predicted)):
                raise ValueError('Non-finite response; choose another acquisition range.')
            residual=(predicted-measured)/uncertainty
            rms=float(np.sqrt(np.mean(residual**2)))
        except ValueError as exc:
            alert.object=str(exc)+' Plots retain the last valid calculation.'
            alert.visible=True
            csv.disabled=params.disabled=fit_button.disabled=True
            state['result']=None
            return
        alert.visible=False
        csv.disabled=params.disabled=fit_button.disabled=False
        state['result']=dict(earth=earth,trial=alternative,acquisition=acq,x=x,clean=clean,
            observed=measured,uncertainty=uncertainty,predicted=predicted,visible=visible)
        earth_true.data=profile(earth,120) if visible else dict(conductivity=[],depth=[])
        earth_trial.data=profile(alternative,120)
        hidden=np.full(len(x),np.nan)
        if temporal:
            # Signed values are retained in CSV. Log plot shows magnitudes only.
            data.data=dict(x=x,observed=np.abs(measured),trial=np.abs(predicted),truth=np.abs(clean) if visible else hidden,
                lower=np.where(np.abs(measured)>uncertainty,np.abs(measured)-uncertainty,np.nan),upper=np.abs(measured)+uncertainty)
            second.data=dict(x=x,trial=residual,observed=hidden,truth=hidden)
            extra=f'{np.count_nonzero(measured<=0)} nonpositive measurements; magnitudes plotted, signed values exported.'
        else:
            data.data=dict(x=x,observed=measured[:,1],trial=predicted[:,1],truth=clean[:,1] if visible else hidden,
                           lower=measured[:,1]-uncertainty[:,1],upper=measured[:,1]+uncertainty[:,1])
            second.data=dict(x=x,observed=measured[:,0],trial=predicted[:,0],truth=clean[:,0] if visible else hidden)
            apparent_source.data=dict(x=x,observed=model.apparent_conductivity(measured[:,1],acq),trial=model.apparent_conductivity(predicted[:,1],acq))
            z=np.linspace(0,acq.spacing*6,200)
            weights.data=dict(z=z,hcp=model.depth_weight(z,acq.spacing,model.ORIENTATIONS[0]),vcp=model.depth_weight(z,acq.spacing,model.ORIENTATIONS[1]))
            weighting_plot.y_range.start=z[-1]
            beta=acq.spacing*np.sqrt(np.pi*acq.axis[-1]*MU0*max(alternative.sigma1,alternative.sigma2))
            extra=f'Trial maximum induction number: {beta:.2f}. '
            extra+='LIN apparent conductivity and depth kernels are approximate; full responses above include induction effects.'
        sensitivity_plot.visible=sensitivity_toggle.value
        if sensitivity_toggle.value:
            deriv=sensitivity(model.forward,alternative,acq)
            if not temporal:
                deriv=deriv[:,1,:]; scale=uncertainty[:,1]
            else:
                scale=uncertainty
            sensitivity_source.data=dict(x=x,top=deriv[:,0]/scale,basement=deriv[:,1]/scale,thickness=deriv[:,2]/scale)
        else:
            sensitivity_source.data=dict(x=[],top=[],basement=[],thickness=[])
        status.object=f'**{mode.value} · Weighted RMS misfit: {rms:.2f} · Noise seed: {seed.value}**\n\n'+extra

    def fit(event):
        if state['result'] is None:
            return
        fit_button.loading=True
        fit_message.object='Fitting three log parameters…'
        try:
            r=state['result']
            fitted,result=fit_earth(model.forward,r['acquisition'],r['observed'],r['uncertainty'],r['trial'])
            state['busy']=True
            assign_earth(trial,fitted)
            state['busy']=False
            update()
            fit_message.object=('**Fit converged.**' if result.success else '**Iteration limit reached; trial updated to the best current fit.**')+f' {result.nfev} forward evaluations reported by optimizer. A good fit does not establish a unique earth. Change the starting trial and fit again.'
        except (ValueError,RuntimeError) as exc:
            fit_message.object=f'Fit failed: {exc}'
        finally:
            state['busy']=False
            fit_button.loading=False

    def load_case(event=None):
        state['busy']=True
        assign_earth(truth,PRESETS[preset.value])
        assign_earth(trial,Earth(.03,.03,30))
        state['busy']=False
        fit_message.object='New experiment loaded. Predict the response before fitting.'
        update()

    def reset_all(event):
        state['busy']=True
        mode.value='Explore'; reveal.value=False; preset.value=list(PRESETS)[0]
        seed.value=12; noise.value=3; sensitivity_toggle.value=False
        for k,w in settings.items():
            w.value=defaults[k]
        state['busy']=False
        load_case()

    def csv_download():
        r=state['result']; columns=[r['x']]; labels=['time_ms' if temporal else 'frequency_hz']
        for key in ['observed','uncertainty','predicted']+(['clean'] if r['visible'] else []):
            if temporal:
                columns.append(r[key]); labels.append(key+'_nV')
            else:
                columns.extend([r[key][:,0],r[key][:,1]]); labels.extend([key+'_inphase_ppm',key+'_quadrature_ppm'])
        stream=io.StringIO()
        np.savetxt(stream,np.column_stack(columns),delimiter=',',header=','.join(labels),comments='')
        stream.seek(0)
        return stream

    def parameters_download():
        r=state['result']
        exported=dict(laboratory=kind,solver='empymod 1.10.6 NumPy core with compatibility patches',
            acquisition=asdict(r['acquisition']),trial=asdict(r['trial']),noise_percent=noise.value,
            seed=seed.value,mode=mode.value,truth_revealed=r['visible'],
            units=dict(conductivity='S/m',thickness='m'),
            uncertainty='max(relative noise * abs(clean), 0.001 * global max(abs(clean))); no random noise at 0%')
        if r['visible']:
            exported['earth']=asdict(r['earth'])
        return io.StringIO(json.dumps(exported,indent=2))

    csv=pn.widgets.FileDownload(label='Download measurements (CSV)',filename=kind+'_measurements.csv',callback=csv_download)
    params=pn.widgets.FileDownload(label='Download parameters (JSON)',filename=kind+'_parameters.json',callback=parameters_download)
    for w in truth+trial+list(settings.values())+[mode,reveal,noise,seed,sensitivity_toggle]:
        w.param.watch(update,'value')
    load.on_click(load_case)
    reset.on_click(reset_all)
    reroll.on_click(lambda event:setattr(seed,'value',(seed.value+1)%1000001))
    fit_button.on_click(fit)
    update()
    prompt=('How do early and late gates constrain different parts of the earth? Can a different thickness and conductivity fit the same transient?'
            if temporal else 'How do coil orientation, spacing, and frequency change the measurement over the same earth? When does apparent conductivity stop representing conductivity?')
    sidebar=[pn.pane.Markdown('### Explore → Predict → Explain'),mode,reveal,preset,load,
        pn.Accordion(('Subsurface model',truth_box),('Acquisition',pn.Column(*acquisition_widgets)),
                     ('Measurement noise',pn.Column(noise,seed,reroll)),active=[0,1]),reset]
    main=[pn.pane.Markdown('## '+title+'\n'+prompt),status,alert,earth_plot,response,second_plot,*extras,
        pn.pane.Markdown('### Interpret the measurements\nChange a trial earth manually or fit its three parameters. Bounds: 1–300 mS/m and 1–100 m. Fitting can take longer in the browser.'),
        trial_box,fit_button,fit_message,sensitivity_toggle,sensitivity_plot,
        pn.pane.Markdown('Sensitivity is the derivative with respect to a **natural-log parameter**, divided by data uncertainty, at the trial earth. FDEM shows quadrature sensitivity. It is not a depth-of-investigation boundary.'),
        pn.Accordion(('Experiments, equations & assumptions',pn.pane.Markdown(notes)),active=[]),pn.Row(csv,params)]
    return template(title,main,sidebar)
