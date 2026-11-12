NOTES = '''
### Predict → filter → inspect
1. Which frequencies belong to the target? Which belong to contamination?
2. Choose a filter and enable **Apply filter**. Use **Reveal true signal** to show or hide the target.
3. Inspect the removed trace. Did the filter discard an arrival or a sinusoid?
4. Compare recovery error as well as visual smoothness.

**Pulse + slow drift:** increase the lower cutoff. When does pulse amplitude suffer?

**Narrowband interference:** widen the rejected band. What happens to pulse shape?

**Two nearby arrivals:** lower the upper cutoff. When do two arrivals merge?

**Overlapping spectra:** the 60 Hz target and interference occupy the same frequency.
A notch removes both; frequency selection alone cannot separate them.

### What the calculations mean
The measurement is the clean signal plus Gaussian noise, sinusoidal drift, and
sinusoidal interference. Gaussian noise strength is its standard deviation;
other strengths are peak amplitudes. Noise is repeatable for a fixed seed.

Butterworth order is the prototype order. Band-pass and band-stop designs have
twice that order. Zero-phase filtering applies the filter forward and backward:
its amplitude response is the square of the single-pass response. The plotted
response includes this change. Causal filtering starts from zero initial state.

The ideal filter multiplies a zero-padded record's FFT by a binary mask and then
crops the inverse FFT to the original record. It is noncausal and zero phase;
sharp frequency edges produce ringing. Padding reduces periodic wraparound but
does not remove finite-record boundary effects. Inspect record edges for every filter.

Spectra use a rectangular window and one-sided amplitude scaling on a logarithmic
amplitude axis, without independent normalization. Zero-amplitude bins are omitted. Sampling is 500 Hz for 2 seconds (Nyquist 250 Hz).
The filter response describes interior behavior; finite-record edges can differ.

Figure 1 shows estimated SNR before filtering and, when enabled, after filtering,
using the synthetic true signal as the reference even when its curve is hidden.
RMSE and output SNR use **recovered − clean**, so both residual noise and signal
distortion count as error. Metrics include the entire record, including its edges.
Timing and amplitude errors track the first event's positive peak in a local window;
for overlapping pulses the reference is the composite clean trace, not an isolated pulse.
These are diagnostics, not an automatic arrival picker.
'''

CODE = '''
### Essential Python
Design a band-pass filter, apply it, then plot the result:
```python
from scipy.signal import butter, sosfiltfilt
import matplotlib.pyplot as plt

sos = butter(4, [10, 80], btype="bandpass", fs=500, output="sos")
recovered = sosfiltfilt(sos, measured)
plt.plot(t, measured, label="Measured")
plt.plot(t, recovered, label="Recovered")
plt.legend()
```
`butter` designs the filter; `sosfiltfilt` applies it in both directions.
Use `sosfilt` for a causal, single-pass comparison.

Plot a one-sided amplitude spectrum (even sample count):
```python
import numpy as np
f = np.fft.rfftfreq(len(measured), d=1/500)
amplitude = np.abs(np.fft.rfft(measured)) / len(measured)
amplitude[1:-1] *= 2
plt.plot(f, amplitude)
plt.xlabel("Frequency (Hz)")
```
'''

FLOW = '''<div style="padding:16px;background:#eef7f8;border-radius:8px;line-height:1.9">
<b>Measurement:</b> clean signal + fixed noise + drift + interference<br>
<b>Recovery:</b> measurement → selected filter → recovered trace<br>
<b>Removed:</b> measurement − recovered trace<br>
<b>Assessment:</b> recovered − clean → RMSE, SNR, peak errors<br>
<b>Spectra:</b> clean / measurement / recovered → separate FFTs for comparison
</div>'''
