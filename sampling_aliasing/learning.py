"""Student-facing Python reference for the sampling models."""
import panel as pn


def learning_section():
    return pn.pane.Markdown("""## Key Python functions and usage

| Function | Role in this app |
| --- | --- |
| `np.arange(n) * dt` | Build uniformly spaced sample times. Sampling rate is `fs = 1/dt`; Nyquist frequency is `fs/2`. |
| `np.cos(2*np.pi*f*t + phase)` | Generate a sinusoid; `f` is in Hz, `t` in seconds, and phase in radians. |
| `np.linspace(start, stop, 4000)` | Make a dense grid for drawing the underlying wave between measurements. This does not increase the measurement sampling rate. |
| `np.deg2rad(phase_deg)` | Convert the phase control from degrees to radians. |
| `np.random.default_rng(seed).normal(0, noise, n)` | Generate reproducible Gaussian noise with standard deviation `noise`. |
| `np.fft.rfft(y)` / `np.fft.rfftfreq(n, dt)` | Compute a real-input FFT and its frequency labels. Divide magnitudes by `n` and double interior bins for this rectangular-window spectrum. |
| `fold_frequency(f, fs)` | App helper mapping a frequency into the signed interval `[-fs/2, fs/2)`. It also works for spatial wavenumbers when the units are cycles/m. |
| `temporal(...)` | App helper generating continuous curves, samples, equivalent alias, and measured spectrum. |
| `spatial(...)` | App helper generating a plane-wave snapshot along receivers and its spatial alias. |

### Example 1 · Why 80 Hz looks like 20 Hz

Run this standalone NumPy example in Python or a notebook. With 100 samples/s, these two zero-phase cosines agree at every measurement time.

```python
import numpy as np

fs = 100                           # samples/s
t = np.arange(100) / fs             # one second, endpoint excluded
f = 80
f_alias = (f + fs/2) % fs - fs/2    # -20 Hz (signed)
y = np.cos(2 * np.pi * f * t)
y_alias = np.cos(2 * np.pi * f_alias * t)
print(np.allclose(y, y_alias))      # True
frequency = np.fft.rfftfreq(len(y), d=1/fs)
amplitude = np.abs(np.fft.rfft(y)) / len(y)
amplitude[1:] *= 2
if len(y) % 2 == 0:
    amplitude[-1] /= 2              # DC and Nyquist are not doubled
print(frequency[np.argmax(amplitude)])  # 20.0 Hz
```


The FFT displays positive frequency, so the peak appears at 20 Hz. The signed alias retains phase and propagation information. Sampling strictly faster than twice the highest signal frequency avoids aliasing; filtering must remove unwanted high frequencies **before** sampling.

### Example 2 · Reproduce the temporal and spatial models

Run from the cloned repository root (NumPy installed). Time intervals use milliseconds in `temporal`; receiver spacing and velocity use m and m/s in `spatial`.

```python
from sampling_aliasing.model import temporal, spatial, fold_frequency

print(fold_frequency(80, 100))      # -20.0 Hz
result = temporal(f1=80, dt_ms=10, duration=1, noise=0)
# Sample times and amplitudes:
t, y = result["t"], result["y"]
print(result["fs"], result["signed"][0])  # 100.0, -20.0
# result["frequency"] and result["spectrum"] give the measured FFT.

filtered = temporal(f1=80, dt_ms=10, antialias=True)
# Ideal pre-sampling filter removes this 80 Hz component:
print(filtered["gains"][0])         # False

line = spatial(frequency=30, velocity=600, spacing=15, receivers=24)
print(line["k"])                   # 0.05 cycles/m (wavelength 20 m)
print(round(line["ka"], 5))         # -0.01667 cycles/m
print(round(line["apparent_velocity"]))  # -1800 m/s
```

**Connect code to the controls:** decreasing `dt_ms` raises temporal Nyquist; increasing `duration` reduces FFT bin spacing. Decreasing receiver `spacing` raises spatial Nyquist; adding `receivers` extends aperture. Here, 15 m spacing exceeds half the 20 m wavelength, so the apparent wave travels backward. The ideal low-pass uses a cutoff of `0.45 * fs`; it is a teaching model, not a realizable filter design.
""")
