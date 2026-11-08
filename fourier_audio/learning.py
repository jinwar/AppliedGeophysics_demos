"""Student-facing processing diagram and reproducible Python examples."""
import panel as pn


def learning_section():
    diagram = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 570" role="img" aria-labelledby="flow-title flow-desc" style="width:100%;max-width:900px;height:auto">
<title id="flow-title">Audio processing: waveform, Fourier spectrum and spectrogram</title>
<desc id="flow-desc">Record, upload or synthesize sound; decode to mono samples and sample rate. Display the waveform. Remove the mean, then branch into a whole-record window and FFT for the spectrum, or overlapping windowed frames and FFTs for the spectrogram.</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#008c95"/></marker></defs>
<g fill="#eef7f8" stroke="#008c95" stroke-width="1.5">
<rect x="150" y="10" width="460" height="55" rx="10"/>
<rect x="150" y="90" width="460" height="65" rx="10"/>
<rect x="20" y="185" width="210" height="65" rx="10"/>
<rect x="280" y="185" width="330" height="65" rx="10"/>
<rect x="30" y="290" width="330" height="65" rx="10"/>
<rect x="400" y="290" width="330" height="65" rx="10"/>
<rect x="30" y="390" width="330" height="65" rx="10"/>
<rect x="400" y="390" width="330" height="65" rx="10"/>
<rect x="30" y="495" width="330" height="65" rx="10"/>
<rect x="400" y="495" width="330" height="65" rx="10"/>
</g>
<g fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)">
<path d="M380 65 V90"/><path d="M240 155 V170 H125 V185"/><path d="M445 155 V185"/>
<path d="M445 250 V270 H195 V290"/><path d="M445 250 V270 H565 V290"/>
<path d="M195 355 V390"/><path d="M565 355 V390"/>
<path d="M195 455 V495"/><path d="M565 455 V495"/>
</g>
<g font-family="sans-serif" font-size="17" text-anchor="middle" fill="#12344a">
<text x="380" y="44">Record · Upload WAV · Synthetic example</text>
<text x="380" y="116">Decode → mono samples y and sample rate fs</text><text x="380" y="140">Keep at most 10 seconds</text>
<text x="125" y="213">Waveform</text><text x="125" y="236">amplitude vs time</text>
<text x="445" y="213">Remove mean (DC)</text><text x="445" y="236">y − mean(y)</text>
<text x="195" y="318">Window the whole recording</text><text x="195" y="341">Hann or rectangular</text>
<text x="565" y="318">Split into overlapping frames</text><text x="565" y="341">Window each frame</text>
<text x="195" y="418">Real FFT → magnitude</text><text x="195" y="441">Correct one-sided amplitudes</text>
<text x="565" y="418">Real FFT of every frame</text><text x="565" y="441">Correct one-sided amplitudes</text>
<text x="195" y="523">Fourier spectrum</text><text x="195" y="546">amplitude vs frequency</text>
<text x="565" y="523">Spectrogram · dB relative to peak</text><text x="565" y="546">frequency vs time, color = level</text>
</g></svg>'''
    return pn.Accordion(
        ('How the data are processed', pn.Column(
            pn.pane.Markdown('The waveform shows timing, the FFT shows frequencies, and the spectrogram shows how frequencies change with time.'),
            pn.pane.HTML(diagram))),
        ('Python example · waveform, spectrum and spectrogram', pn.pane.Markdown("""Run in a notebook with **NumPy and Matplotlib**. This sound switches from 440 Hz to 880 Hz halfway through.

```python
import numpy as np
import matplotlib.pyplot as plt

fs = 16000                           # samples per second
t = np.arange(3 * fs) / fs
y = np.sin(2 * np.pi * np.where(t < 1.5, 440, 880) * t)

# Whole-record Fourier amplitude spectrum
f = np.fft.rfftfreq(len(y), d=1/fs)
a = np.abs(np.fft.rfft(y)) / len(y)
a[1:-1] *= 2                         # even-length signal: leave DC/Nyquist alone

fig, ax = plt.subplots(3, 1, figsize=(9, 8))
ax[0].plot(t, y)
ax[0].set(xlabel="Time (s)", ylabel="Amplitude")
ax[1].plot(f, a)
ax[1].set(xlim=(0, 2000), xlabel="Frequency (Hz)", ylabel="Amplitude")
ax[2].specgram(y, Fs=fs, NFFT=1024, noverlap=768, cmap="inferno")
ax[2].set(ylim=(0, 2000), xlabel="Time (s)", ylabel="Frequency (Hz)")
plt.tight_layout()
plt.show()
```

**Essentials:** `plot` draws a curve; `rfft` computes the Fourier coefficients; `rfftfreq` labels the frequencies; `specgram` makes a spectrogram from overlapping windows.

`NFFT=1024` means a 64 ms window at 16 kHz; `noverlap=768` means 75% overlap. Increase the window length to improve frequency detail at the expense of time detail. Zoom into the waveform to see individual cycles.

This simple example uses a rectangular window for the whole-record FFT. Matplotlib's `specgram` defaults to a Hann window and displays power spectral density in dB; the app displays amplitude in dB relative to its strongest STFT bin, so the color values differ. To analyze your own sound, replace `y` and `fs` with your samples and sample rate.
""")), active=[])
