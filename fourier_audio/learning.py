"""Student-facing processing diagram and reproducible Python examples."""
import panel as pn


def learning_section():
    diagram = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 740" role="img" aria-labelledby="flow-title flow-desc" style="width:100%;max-width:1000px;height:auto">
<title id="flow-title">Window shape affects both spectra; STFT window length affects only the spectrogram</title>
<desc id="flow-desc">Mono audio is displayed as a waveform. After mean removal, the whole-record path applies a window of N samples and one FFT. The STFT path splits the audio into overlapping n-sample frames, applies a window to each frame, then computes an FFT per frame. Both paths use the selected Hann or rectangular shape. Only STFT uses the window length and overlap controls.</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#008c95"/></marker></defs>
<rect x="210" y="10" width="400" height="60" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="410.0" y="34.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Record / upload / synthetic sound</text>
<text x="410.0" y="57.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Mono samples y, sample rate fs</text>
<rect x="15" y="100" width="215" height="60" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="122.5" y="124.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Waveform</text>
<text x="122.5" y="147.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Original samples vs time</text>
<rect x="290" y="100" width="320" height="60" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="450.0" y="124.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Remove mean</text>
<text x="450.0" y="147.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">z = y − mean(y); N = len(z)</text>
<path d="M260 70 V85 H122 V100" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<path d="M450 70 V100" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<rect x="70" y="185" width="680" height="60" rx="10" fill="#fff4e8" stroke="#d16b33" stroke-width="1.5"/>
<text x="410.0" y="209.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Window function control: Hann or Rectangular</text>
<text x="410.0" y="232.5" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">The same SHAPE is used in BOTH paths below.</text>
<rect x="20" y="280" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="205.0" y="307.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">WHOLE-RECORD FFT</text>
<text x="205.0" y="330.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Use all N samples</text>
<rect x="430" y="280" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="615.0" y="307.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">STFT: split into overlapping frames</text>
<text x="615.0" y="330.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">n from window length; hop from overlap</text>
<path d="M450 160 V173 H5 V260 H205 V280" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<path d="M450 160 V173 H815 V260 H615 V280" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<rect x="20" y="380" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="205.0" y="407.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Apply selected window to whole record</text>
<text x="205.0" y="430.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">w = hanning(N) or ones(N)</text>
<rect x="430" y="380" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="615.0" y="407.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Apply selected window to EACH frame</text>
<text x="615.0" y="430.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">w = hanning(n) or ones(n)</text>
<path d="M205 345 V380" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<path d="M615 345 V380" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<rect x="20" y="480" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="205.0" y="507.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">One FFT: rfft(z × w)</text>
<text x="205.0" y="530.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Magnitude / sum(w); one-sided scaling</text>
<rect x="430" y="480" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="615.0" y="507.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">FFT of each frame: rfft(frames × w)</text>
<text x="615.0" y="530.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Magnitude / sum(w); one-sided scaling</text>
<path d="M205 445 V480" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<path d="M615 445 V480" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<rect x="20" y="580" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="205.0" y="607.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Fourier amplitude spectrum</text>
<text x="205.0" y="630.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Frequency spacing = fs / N</text>
<rect x="430" y="580" width="370" height="65" rx="10" fill="#eef7f8" stroke="#008c95" stroke-width="1.5"/>
<text x="615.0" y="607.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Spectrogram: dB relative to peak</text>
<text x="615.0" y="630.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">Time × frequency; spacing = fs / n</text>
<path d="M205 545 V580" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<path d="M615 545 V580" fill="none" stroke="#008c95" stroke-width="2" marker-end="url(#arrow)"/>
<rect x="70" y="675" width="680" height="55" rx="10" fill="#fff4e8" stroke="#d16b33" stroke-width="1.5"/>
<text x="410.0" y="697.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">STFT window length and overlap affect ONLY the right-hand path.</text>
<text x="410.0" y="720.0" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#12344a">The whole-record FFT always uses the full recording duration.</text>
</svg>'''
    return pn.Accordion(
        ('How the data are processed', pn.Column(
            pn.pane.Markdown('Window **shape** (Hann/Rectangular) affects both spectral plots. STFT window **length** and overlap affect only the spectrogram. The waveform is not windowed.'),
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
z = y - y.mean()
w = np.hanning(len(z))               # whole-record Hann window
a = np.abs(np.fft.rfft(z * w)) / w.sum()
a[1:-1] *= 2                         # even-length signal: leave DC/Nyquist alone

fig, ax = plt.subplots(3, 1, figsize=(9, 8))
ax[0].plot(t, y)
ax[0].set(xlabel="Time (s)", ylabel="Amplitude")
ax[1].plot(f, a)
ax[1].set(xlim=(0, 2000), xlabel="Frequency (Hz)", ylabel="Amplitude")
ax[2].specgram(z, Fs=fs, NFFT=1024, noverlap=768,
               window=np.hanning(1024), cmap="inferno")
ax[2].set(ylim=(0, 2000), xlabel="Time (s)", ylabel="Frequency (Hz)")
plt.tight_layout()
plt.show()
```

**Essentials:** `plot` draws a curve; `rfft` computes the Fourier coefficients; `rfftfreq` labels the frequencies; `specgram` makes a spectrogram from overlapping windows.

`NFFT=1024` means a 64 ms window at 16 kHz; `noverlap=768` means 75% overlap. Increase the window length to improve frequency detail at the expense of time detail. Zoom into the waveform to see individual cycles.

Both plots use Hann windows: one spanning the entire record for the FFT, and one per 1024-sample frame for the spectrogram. Matplotlib's `specgram` displays power spectral density in dB; the app displays amplitude in dB relative to its strongest STFT bin, so the color values differ. To analyze your own sound, replace `y` and `fs` with your samples and sample rate.
""")), active=[])
