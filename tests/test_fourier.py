import numpy as np
import pytest
from fourier_audio.model import analyze, example, read_wav, write_wav


def test_tone_frequency_and_amplitude():
    y,fs=example('Pure tone')
    d=analyze(y,fs)
    assert d['dominant']==pytest.approx(440)
    assert d['amplitude'].max()==pytest.approx(.6,rel=1e-4)


def test_sequential_tones_are_separated_in_time():
    y,fs=example('Two sequential tones')
    d=analyze(y,fs)
    peaks=d['stft_frequency'][d['db'].argmax(axis=0)]
    assert np.median(peaks[d['time']<1])==pytest.approx(440,abs=fs/d['n'])
    assert np.median(peaks[d['time']>2])==pytest.approx(880,abs=fs/d['n'])


def test_chirp_frequency_increases():
    y,fs=example('Chirp: rising pitch')
    d=analyze(y,fs)
    peaks=d['stft_frequency'][d['db'].argmax(axis=0)]
    expected=200+600*d['time']
    assert np.max(abs(peaks-expected))<fs/d['n']


def test_window_and_overlap_tradeoff():
    y,fs=example('Pure tone')
    short=analyze(y,fs,16);long=analyze(y,fs,128)
    assert fs/long['n']<fs/short['n']
    dense=analyze(y,fs,16,.9)
    assert dense['n']==short['n'] and dense['hop']<short['hop']


def test_silence_has_no_peak():
    d=analyze(np.zeros(1600),16000)
    assert d['dominant'] is None
    assert np.all(d['db']==-120)


def test_wav_roundtrip():
    y,fs=example('Pure tone')
    restored,rate,truncated=read_wav(write_wav(y,fs))
    assert rate==fs and not truncated
    np.testing.assert_allclose(y,restored,atol=6e-5)


def test_wav_limits_duration():
    y,fs=example('Pure tone',duration=11)
    restored,rate,truncated=read_wav(write_wav(y,fs))
    assert truncated and len(restored)==10*fs


@pytest.mark.parametrize('window_ms',[256,512,1024,2048])
def test_full_rate_recording_long_window(window_ms):
    y,fs=example('Pure tone',fs=48000,duration=10)
    d=analyze(y,fs,window_ms,.75)
    assert d['db'].shape[1]==len(d['time'])
    assert d['n']==round(fs*window_ms/1000)
    assert d['dominant']==pytest.approx(440)


def test_waveform_zoom_restores_samples_and_preserves_overview_extrema():
    from fourier_audio.model import waveform_view
    y,fs=example('Pure tone',fs=48000,duration=10)
    y[123456]=1
    overview=waveform_view(y,fs,0,10)
    assert len(overview['time'])<=12002
    assert np.all(np.diff(overview['time'])>0)
    assert overview['amplitude'].max()==1
    detail=waveform_view(y,fs,1,1.01)
    indices=np.rint(detail['time']*fs).astype(int)
    np.testing.assert_array_equal(np.diff(indices),1)
    np.testing.assert_array_equal(detail['amplitude'],y[indices])
    assert indices[0]<=48000 and indices[-1]>=48480
