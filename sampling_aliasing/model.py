"""Transparent forward models; all frequencies use cycles, not radians."""
import numpy as np


def fold_frequency(frequency, sampling_rate):
    """Signed principal frequency in [-fs/2, fs/2)."""
    if sampling_rate <= 0:
        raise ValueError('Sampling rate must be positive')
    return (frequency + sampling_rate / 2) % sampling_rate - sampling_rate / 2


def wave(t, frequencies, amplitudes, phase=0):
    return sum(a * np.cos(2*np.pi*f*np.asarray(t) + phase)
               for f, a in zip(frequencies, amplitudes))


def temporal(f1=30, f2=80, a2=0, dt_ms=10, duration=1, phase_deg=0,
             noise=0, seed=42, antialias=False):
    dt = dt_ms / 1000
    n = max(4, int(round(duration / dt)))
    t = np.arange(n)*dt
    fs = 1/dt
    frequencies = np.array([f1, f2], dtype=float)
    amplitudes = np.array([1, a2], dtype=float)
    # Ideal analog low-pass before sampling; a teaching limit, not a realizable filter.
    gains = (frequencies < .45*fs) if antialias else np.ones(2)
    passed = amplitudes*gains
    phase = np.deg2rad(phase_deg)
    clean = wave(t, frequencies, passed, phase)
    observed = clean + np.random.default_rng(seed).normal(0, noise, n)
    dense = np.linspace(0, n*dt, 4000)
    signed = np.array([fold_frequency(f, fs) for f in frequencies])
    fft = np.abs(np.fft.rfft(observed))/n
    fft[1:] *= 2
    if n % 2 == 0:
        fft[-1] /= 2
    return dict(t=t, y=observed, clean=clean, dense=dense,
                true=wave(dense, frequencies, amplitudes, phase),
                passed=wave(dense, frequencies, passed, phase),
                alias=wave(dense, signed, passed, phase),
                signed=signed, gains=gains, fs=fs, n=n, dt=dt,
                frequency=np.fft.rfftfreq(n, dt), spectrum=fft)


def spatial(frequency=30, velocity=600, spacing=15, receivers=24, time=0):
    x = np.arange(receivers)*spacing
    dense = np.linspace(0, x[-1], 4000)
    k = frequency/velocity
    ka = fold_frequency(k, 1/spacing)
    signal = lambda xx, kk: np.cos(2*np.pi*(frequency*time-kk*xx))
    return dict(x=x, dense=dense, y=signal(x, k), true=signal(dense,k),
                alias=signal(dense,ka), k=k, ka=ka,
                apparent_velocity=None if abs(ka)<1e-12 else frequency/ka)
