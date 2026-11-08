"""Short, standalone plotting examples for students."""
import panel as pn


def learning_section():
    return pn.Accordion(
        ('Python example · time sampling and spectrum', pn.pane.Markdown("""Run in a notebook with **NumPy and Matplotlib**. Sample an 80 Hz cosine at 100 samples/s: its measured spectrum peaks at 20 Hz.

```python
import numpy as np
import matplotlib.pyplot as plt

fs = 100                             # samples per second
t = np.arange(100) / fs               # one second of measurements
dense = np.linspace(0, 1, 4000)       # smooth drawing grid only
y = np.cos(2 * np.pi * 80 * t)
f = np.fft.rfftfreq(len(y), d=1/fs)
a = np.abs(np.fft.rfft(y)) / len(y)
a[1:-1] *= 2                         # even-length signal: leave DC/Nyquist alone

fig, ax = plt.subplots(2, 1, figsize=(9, 6))
ax[0].plot(dense, np.cos(2 * np.pi * 80 * dense), label="True: 80 Hz")
ax[0].plot(dense, np.cos(2 * np.pi * 20 * dense), "--", label="Alias: 20 Hz")
ax[0].scatter(t, y, color="black", label="Samples")
ax[0].set(xlim=(0, 0.1), xlabel="Time (s)", ylabel="Amplitude")
ax[0].legend()
ax[1].plot(f, a)
ax[1].set(xlabel="Frequency (Hz)", ylabel="Amplitude")
plt.tight_layout()
plt.show()
```

**Essentials:** `arange` sets the sample locations; `cos` generates the signal; `plot` draws curves; `scatter` marks measurements. `rfft` and `rfftfreq` provide the spectrum and its frequency axis.

The two curves agree at the sample times. Increase `fs` above 160 samples/s to resolve this 80 Hz signal without aliasing. The dense drawing grid is not additional measured data.
""")),
        ('Python example · receiver spacing', pn.pane.Markdown("""The same idea applies to distance. A 30 Hz wave traveling at 600 m/s has a 20 m wavelength, so receiver spacing should be less than 10 m.

```python
import numpy as np
import matplotlib.pyplot as plt

frequency, velocity, spacing = 30, 600, 15
k = frequency / velocity             # cycles per metre
ks = 1 / spacing                     # spatial sampling rate
ka = (k + ks/2) % ks - ks/2           # signed aliased wavenumber
x = np.arange(24) * spacing
xx = np.linspace(0, x[-1], 4000)
plt.plot(xx, np.cos(2*np.pi*k*xx), label="True wave")
plt.plot(xx, np.cos(2*np.pi*ka*xx), "--", label="Spatial alias")
plt.scatter(x, np.cos(2*np.pi*k*x), color="black", label="Receivers")
plt.xlabel("Distance (m)")
plt.ylabel("Amplitude")
plt.legend()
plt.show()
```

Change `spacing` from 15 to 5 m and compare the curves. Closer receivers improve spatial sampling; adding more receivers at the same spacing only extends the aperture.
""")), active=[])
