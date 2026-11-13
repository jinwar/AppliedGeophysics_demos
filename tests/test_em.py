"""Physics regressions, inversion, and student-facing state transitions."""
import json
from pathlib import Path
from dataclasses import replace
import numpy as np
import panel as pn
import pytest
from shared.em_model import Earth, PRESETS, observe, fit_earth
from tdem_sounding import model as td
from fdem_sensitivity import model as fd
from tdem_sounding.app import create_app as tdem_app
from fdem_sensitivity.app import create_app as fdem_app

REFERENCE=json.loads((Path(__file__).parent/'data/em_simpeg_reference.json').read_text())

@pytest.mark.parametrize('case',REFERENCE['cases'])
def test_independent_simpeg_reference(case):
    model=td if case['kind']=='tdem' else fd
    acq=model.Acquisition(**({'orientation':case['orientation']} if 'orientation' in case else {}))
    actual=model.forward(PRESETS[case['preset']],acq)
    expected=np.array(case['response'])
    np.testing.assert_allclose(actual,expected,rtol=.003,atol=1e-5)

@pytest.mark.parametrize('model',[td,fd])
def test_homogeneous_interface_is_invisible(model):
    np.testing.assert_allclose(model.forward(Earth(.02,.02,5),model.Acquisition()),
        model.forward(Earth(.02,.02,90),model.Acquisition()),rtol=1e-7)


def test_tdem_current_and_late_time_power_law():
    a=td.Acquisition(first_ms=1,last_ms=10)
    v=td.forward(Earth(.02,.02,20),a)
    np.testing.assert_allclose(td.forward(Earth(.02,.02,20),replace(a,current=3)),3*v)
    slope=np.polyfit(np.log(a.axis),np.log(v),1)[0]
    assert -2.55<slope<-2.4

@pytest.mark.parametrize('orientation',fd.ORIENTATIONS)
def test_fdem_low_induction_conductivity_and_kernel(orientation):
    a=fd.Acquisition(spacing=10,first_hz=10,last_hz=100,orientation=orientation)
    actual=fd.apparent_conductivity(fd.forward(Earth(.01,.01,20),a)[:,1],a)
    # 0.1 m height and small finite-induction effects lower the zero-height LIN limit.
    np.testing.assert_allclose(actual,10,rtol=.09)
    z=np.geomspace(1e-7,1e6,10000)
    assert np.trapezoid(fd.depth_weight(z,a.spacing,orientation),z)==pytest.approx(1,rel=1e-4)

@pytest.mark.parametrize('model',[td,fd])
def test_fit_recovers_noise_free_layered_data(model):
    a=model.Acquisition()
    truth=Earth(.01,.08,18)
    measured,uncertainty=observe(model.forward(truth,a),0,12)
    fitted,result=fit_earth(model.forward,a,measured,uncertainty,Earth(.02,.05,25))
    assert result.success
    np.testing.assert_allclose([fitted.sigma1,fitted.sigma2,fitted.thickness],
                              [truth.sigma1,truth.sigma2,truth.thickness],rtol=.02)


def widgets(app):
    found = {}
    def walk(item):
        if isinstance(item, pn.widgets.Widget):
            found[item.name] = item
        for child in getattr(item, 'objects', []):
            walk(child)
    for item in list(app.sidebar)+list(app.main):
        walk(item)
    return found

@pytest.mark.parametrize('factory,kind',[(tdem_app,'tdem'),(fdem_app,'fdem')])
def test_challenge_exports_fit_reset_and_invalid_acquisition(factory,kind):
    app=factory(); w=widgets(app)
    downloads=[x for x in w.values() if isinstance(x,pn.widgets.FileDownload)]
    csv=next(x for x in downloads if x.filename.endswith('.csv'))
    params=next(x for x in downloads if x.filename.endswith('.json'))
    original=csv.callback().getvalue()
    w['Mode'].value='Challenge'
    assert 'clean' not in csv.callback().getvalue().splitlines()[0]
    assert 'earth' not in json.loads(params.callback().getvalue())
    w['Reveal earth model'].value=True
    assert 'clean' in csv.callback().getvalue().splitlines()[0]
    assert 'earth' in json.loads(params.callback().getvalue())
    w['Trial: top conductivity (mS/m)'].value=50
    # Modifying interpretation must not change the synthetic measurements.
    assert np.loadtxt(csv.callback(),delimiter=',',skiprows=1)[:,1].tolist()==np.loadtxt(io_string(original),delimiter=',',skiprows=1)[:,1].tolist()
    w['Fit trial model to measurements'].clicks+=1
    assert w['Trial: top conductivity (mS/m)'].value!=50
    w['Calculate sensitivity'].value=True
    if kind=='tdem':
        w['First gate (ms)'].value=.3; w['Last gate (ms)'].value=.3
    else:
        w['Minimum frequency (Hz)'].value=1000.; w['Maximum frequency (Hz)'].value=1000.
    assert csv.disabled and params.disabled
    w['Reset laboratory'].clicks+=1
    assert not csv.disabled
    assert csv.callback().getvalue()==original
    assert w['Mode'].value=='Explore'


def io_string(text):
    import io
    return io.StringIO(text)


def test_sessions_have_independent_widgets_and_noise():
    a=widgets(fdem_app()); b=widgets(fdem_app())
    a['Earth: top conductivity (mS/m)'].value=99
    assert b['Earth: top conductivity (mS/m)'].value==10
    clean=fd.forward(Earth(),fd.Acquisition())
    assert np.array_equal(observe(clean,3,12)[0],observe(clean,3,12)[0])
    assert not np.array_equal(observe(clean,3,12)[0],observe(clean,3,13)[0])
