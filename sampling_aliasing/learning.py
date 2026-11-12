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
        active=[])
