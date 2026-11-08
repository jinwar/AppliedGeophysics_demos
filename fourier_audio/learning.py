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
    return pn.Column(
        pn.pane.Markdown('## From sound to frequency and time\nThe waveform preserves timing; the whole-record FFT summarizes frequencies; the STFT shows when those frequencies occur.'),
        pn.pane.HTML(diagram),
        pn.pane.Markdown("""## Key Python functions and usage

| Function | Role in this app |
| --- | --- |
| `np.asarray(y, dtype=float)` and `y.mean()` | Convert samples to a numeric array and remove the mean before spectral analysis. |
| `np.hanning(n)` / `np.ones(n)` | Make a Hann / rectangular window. Multiply samples by it before the FFT. |
| `np.fft.rfft(y)` | Return complex Fourier coefficients for nonnegative frequencies of a real signal. |
| `np.fft.rfftfreq(n, d=1/fs)` | Label FFT bins in Hz; spacing is `fs/n`. |
| `np.abs(X)` | Convert complex coefficients to magnitudes. Divide by the window sum and double interior bins for a one-sided amplitude spectrum. |
| `np.arange(...)` and `np.stack(...)` | Choose frame starts and assemble overlapping segments for the STFT. |
| `np.fft.rfft(frames * taper, axis=1)` | Transform each windowed frame along its sample axis. |
| `20 * np.log10(...)` | Express amplitude ratios in decibels. The spectrogram reference is its strongest time-frequency bin. |
| `read_wav(data)` / `write_wav(y, fs)` | App helpers to decode PCM WAV bytes to mono samples / encode samples as a downloadable WAV. |
| `analyze(y, fs, ...)` | App helper returning the whole-record spectrum, STFT, frequency/time axes, and summary values. |

### Example 1 · Build a one-sided amplitude spectrum

Run this standalone NumPy example in Python or a notebook. A 440 Hz tone with amplitude 0.6 produces a peak near 440 Hz with amplitude 0.6.

```python
import numpy as np

fs = 16000                         # samples per second
t = np.arange(3 * fs) / fs          # three seconds
y = 0.6 * np.sin(2 * np.pi * 440 * t)
y = y - y.mean()
w = np.hanning(len(y))
X = np.fft.rfft(y * w)
amplitude = np.abs(X) / w.sum()
amplitude[1:] *= 2                 # positive-frequency contribution
if len(y) % 2 == 0:
    amplitude[-1] /= 2             # do not double Nyquist
frequency = np.fft.rfftfreq(len(y), d=1/fs)
print(frequency[np.argmax(amplitude)])  # 440.0 Hz
```


### Example 2 · Reproduce the app's time-frequency analysis

Run from the cloned repository root (NumPy installed). The two tones occur sequentially; the spectrum contains both, while the spectrogram separates them in time.

```python
from fourier_audio.model import example, analyze, read_wav, write_wav
from pathlib import Path

y, fs = example("Two sequential tones")
d = analyze(y, fs, window_ms=512, overlap=0.75, window="Hann")
print(d["n"], d["hop"])              # 8192 samples, 2048 samples
print(d["db"].shape)                 # (frequency bins, time frames)
# Plot d["amplitude"] against d["frequency"].
# Plot d["db"] with d["time"] and d["stft_frequency"] as axes.
Path("example.wav").write_bytes(write_wav(y, fs))
y_loaded, fs_loaded, truncated = read_wav(Path("example.wav").read_bytes())
```

**Connect code to the controls:** `window_ms` sets frame duration, `overlap` sets the shared fraction between frames, and `window` selects the taper. The frequency upper limit only crops the displayed frequency range; it does not filter the audio. Longer windows reduce FFT bin spacing but blur timing. Browser microphone capture uses JavaScript; NumPy performs the analysis in Python.
"""))
