import numpy as np
import pytest
from sampling_aliasing.model import fold_frequency, temporal, spatial, wave

@pytest.mark.parametrize('f,expected',[(20,20),(80,-20),(130,30),(100,0),(50,-50)])
def test_fold(f,expected):
    assert fold_frequency(f,100)==expected

@pytest.mark.parametrize('phase',[0,30,90,150])
def test_alias_matches_every_sample(phase):
    d=temporal(f1=80,f2=130,a2=.4,phase_deg=phase)
    np.testing.assert_allclose(d['clean'],wave(d['t'],d['signed'],[1,.4],np.deg2rad(phase)),atol=1e-12)

def test_nyquist_quadrature_disappears():
    np.testing.assert_allclose(temporal(f1=50,phase_deg=90)['clean'],0,atol=1e-12)

def test_filter_before_sampling():
    d=temporal(f1=80,antialias=True)
    np.testing.assert_array_equal(d['clean'],0)

def test_fft_amplitude_and_resolution():
    d=temporal(f1=20)
    assert d['frequency'][np.argmax(d['spectrum'])]==20
    assert np.max(d['spectrum'])==pytest.approx(1)
    e=temporal(f1=20,duration=2)
    assert e['frequency'][1]==d['frequency'][1]/2

def test_repeatable_noise():
    np.testing.assert_array_equal(temporal(noise=.2)['y'],temporal(noise=.2)['y'])

def test_spatial_reversal_and_sample_identity():
    d=spatial(time=.017)
    assert d['apparent_velocity']==pytest.approx(-1800)
    np.testing.assert_allclose(d['y'],np.cos(2*np.pi*(30*.017-d['ka']*d['x'])),atol=1e-12)

def test_zero_wavenumber():
    assert spatial(frequency=40,velocity=600,spacing=15)['apparent_velocity'] is None
