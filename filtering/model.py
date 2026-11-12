"""Synthetic recovery experiment; amplitudes are never independently normalized."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy import signal


@dataclass
class Parameters:
    kind: str = 'Seismic pulse'
    frequency: float = 30.0
    frequency2: float = 75.0
    amplitude: float = 1.0
    amplitude2: float = 0.7
    arrival: float = 0.8
    separation: float = 0.08
    noise: float = 0.18
    drift: float = 0.5
    drift_frequency: float = 2.0
    interference: float = 0.0
    interference_frequency: float = 60.0
    seed: int = 12
    filter_type: str = 'Band-pass'
    low: float = 10.0
    high: float = 80.0
    order: int = 4
    phase: str = 'Zero-phase'
    design: str = 'Butterworth'
    fs: float = 500.0
    duration: float = 2.0


def ricker(t, center, frequency):
    a = (np.pi * frequency * (t - center)) ** 2
    return (1 - 2 * a) * np.exp(-a)


def synthesize(p):
    t = np.arange(round(p.duration * p.fs)) / p.fs
    if p.kind == 'Sinusoids':
        clean = p.amplitude * np.sin(2 * np.pi * p.frequency * t)
        clean += p.amplitude2 * np.sin(2 * np.pi * p.frequency2 * t)
    else:
        clean = p.amplitude * ricker(t, p.arrival, p.frequency)
        if p.kind == 'Two seismic pulses':
            clean += p.amplitude2 * ricker(t, p.arrival + p.separation, p.frequency)
    noise = p.noise * np.random.default_rng(p.seed).standard_normal(t.size)
    drift = p.drift * np.sin(2 * np.pi * p.drift_frequency * t)
    interference = p.interference * np.sin(2 * np.pi * p.interference_frequency * t)
    return t, clean, clean + noise + drift + interference


def spectrum(x, fs):
    amplitude = np.abs(np.fft.rfft(x)) / len(x)
    amplitude[1:-1 if len(x) % 2 == 0 else None] *= 2
    return np.fft.rfftfreq(len(x), 1 / fs), amplitude


def apply_filter(x, p):
    if not (0 < p.low < p.fs / 2 and 0 < p.high < p.fs / 2):
        raise ValueError('Cutoffs must be between 0 and Nyquist (250 Hz).')
    if p.filter_type in ('Band-pass', 'Notch / band-stop') and p.low >= p.high:
        raise ValueError('Choose lower cutoff < upper cutoff.')
    band = {'Low-pass': 'lowpass', 'High-pass': 'highpass',
            'Band-pass': 'bandpass', 'Notch / band-stop': 'bandstop'}[p.filter_type]
    if p.design == 'Ideal sharp cutoff':
        # Zero padding reduces wraparound; finite records still have edge effects.
        n = len(x)
        padded = np.pad(x, (n, n))
        f = np.fft.rfftfreq(len(padded), 1 / p.fs)
        keep = {'lowpass': f <= p.high, 'highpass': f >= p.low,
                'bandpass': (f >= p.low) & (f <= p.high),
                'bandstop': (f < p.low) | (f > p.high)}[band]
        y = np.fft.irfft(np.fft.rfft(padded) * keep, n=len(padded))[n:2*n]
        return y, f, keep.astype(float), np.zeros_like(f)
    cutoff = p.high if band == 'lowpass' else p.low if band == 'highpass' else [p.low, p.high]
    sos = signal.butter(p.order, cutoff, btype=band, fs=p.fs, output='sos')
    f, h = signal.sosfreqz(sos, worN=2048, fs=p.fs)
    if p.phase == 'Zero-phase':
        y = signal.sosfiltfilt(sos, x)
        gain, phase = np.abs(h)**2, np.zeros_like(f)
    else:
        y = signal.sosfilt(sos, x)
        gain, phase = np.abs(h), np.unwrap(np.angle(h)) * 180 / np.pi
    return y, f, gain, phase


def snr(clean, estimate):
    error = np.sum((estimate - clean)**2)
    return float(10 * np.log10(np.sum(clean**2) / error)) if error else float('inf')


def experiment(p, filtering=True):
    t, clean, observed = synthesize(p)
    if filtering:
        recovered, f, gain, phase = apply_filter(observed, p)
    else:
        recovered = observed.copy()
        f = gain = phase = np.array([], dtype=float)
    metrics = dict(input_snr=snr(clean, observed), output_snr=snr(clean, recovered),
                   rmse=float(np.sqrt(np.mean((recovered-clean)**2))))
    if p.kind != 'Sinusoids':
        # Match the first event within a fixed local window, not an arbitrary noise peak.
        half = min(0.12, p.separation * 0.45) if p.kind == 'Two seismic pulses' else 0.12
        indices = np.flatnonzero(abs(t-p.arrival) <= half)
        truth_idx = indices[np.argmax(clean[indices])]
        peak_idx = indices[np.argmax(recovered[indices])]
        metrics['timing_ms'] = float((t[peak_idx]-t[truth_idx])*1000)
        metrics['amplitude_pct'] = float(100*(recovered[peak_idx]/clean[truth_idx]-1))
    return dict(t=t, clean=clean, observed=observed, recovered=recovered,
                removed=observed-recovered, frequency=f, gain=gain, phase=phase,
                metrics=metrics, parameters=asdict(p))


PRESETS = {
    'Pulse + slow drift': dict(),
    'Narrowband interference': dict(drift=0., noise=0.08, interference=0.65,
        filter_type='Notch / band-stop', low=56., high=64.),
    'Two nearby arrivals': dict(kind='Two seismic pulses', drift=0., noise=0.2,
        separation=0.045, low=8., high=65.),
    'Overlapping signal and noise': dict(kind='Sinusoids', frequency=30.,
        frequency2=60., drift=0., noise=0.2, interference=0.7,
        interference_frequency=60., filter_type='Notch / band-stop', low=56., high=64.),
}
