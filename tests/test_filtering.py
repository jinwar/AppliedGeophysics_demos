from dataclasses import replace
import numpy as np
import pytest
from filtering.model import Parameters, PRESETS, synthesize, apply_filter, experiment


def test_fixed_noise_and_exact_removed_component():
    p = Parameters()
    a, b = experiment(p), experiment(replace(p, high=60))
    np.testing.assert_array_equal(a['observed'], b['observed'])
    np.testing.assert_allclose(a['recovered'] + a['removed'], a['observed'])
    assert not np.array_equal(a['observed'], experiment(replace(p, seed=13))['observed'])


@pytest.mark.parametrize('phase', ['Causal', 'Zero-phase'])
def test_measured_gain_matches_actual_response(phase):
    p = Parameters(filter_type='Low-pass', high=40, phase=phase, duration=8)
    t = np.arange(4000) / p.fs
    for hz in [15, 40, 100]:
        x = np.sin(2*np.pi*hz*t)
        y, f, gain, _ = apply_filter(x, p)
        actual = np.sqrt(np.mean(y[1000:-1000]**2) / np.mean(x[1000:-1000]**2))
        assert actual == pytest.approx(np.interp(hz, f, gain), abs=.002)


def test_phase_and_amplitude_on_noise_free_pulse():
    p = Parameters(noise=0, drift=0, low=1, high=120)
    r = experiment(p)
    assert r['metrics']['timing_ms'] == 0
    assert abs(r['metrics']['amplitude_pct']) < 1
    assert experiment(replace(p, phase='Causal'))['metrics']['timing_ms'] > 0


def test_drift_recovery_improves_error():
    r = experiment(Parameters())
    assert r['metrics']['output_snr'] > r['metrics']['input_snr'] + 5


@pytest.mark.parametrize('name', list(PRESETS))
@pytest.mark.parametrize('design', ['Butterworth', 'Ideal sharp cutoff'])
def test_presets_finite(name, design):
    r = experiment(Parameters(**PRESETS[name], design=design))
    assert len(r['recovered']) == 1000
    assert np.isfinite(r['recovered']).all()


def test_ideal_response_and_symmetry():
    p = Parameters(design='Ideal sharp cutoff', filter_type='Low-pass', high=40)
    impulse = np.zeros(1001)
    impulse[500] = 1
    y, f, gain, phase = apply_filter(impulse, p)
    np.testing.assert_allclose(y, y[::-1], atol=1e-15)
    assert set(gain) == {0., 1.}
    assert np.all(phase == 0)
    assert y[500] < 1  # Sharp filtering spreads a localized event.


def test_invalid_cutoffs():
    with pytest.raises(ValueError):
        experiment(Parameters(low=100, high=20))


def test_single_cutoff_filters_ignore_other_cutoff():
    for kind in ['Low-pass', 'High-pass']:
        r = experiment(Parameters(filter_type=kind, low=100, high=20))
        assert np.isfinite(r['recovered']).all()


def test_ui_challenge_presets_and_downloads():
    import panel as pn
    from filtering.app import create_app
    app = create_app()
    widgets = [w for item in list(app.sidebar) + list(app.main)
               for w in pn.panel(item).select(pn.widgets.Widget)]
    by_name = {w.name: w for w in widgets}
    mode = by_name['Mode']
    mode.value = 'Challenge'
    download = by_name['Download data (CSV)']
    assert 'clean' not in download.callback().getvalue().splitlines()[0]
    by_name['Reveal clean signal'].clicks += 1
    assert 'clean' in download.callback().getvalue().splitlines()[0]
    by_name['Upper cutoff (Hz)'].value = 70
    assert 'clean' not in download.callback().getvalue().splitlines()[0]
    for name in PRESETS:
        by_name['Experiment'].value = name
        by_name['Load experiment'].clicks += 1
        assert not download.disabled
    by_name['Lower cutoff (Hz)'].value = 150
    assert download.disabled
