"""Audio transforms with explicit normalization and no SciPy dependency."""
import io
import wave
import numpy as np

MAX_SECONDS = 10


def example(kind, fs=16000, duration=3):
    t = np.arange(round(fs*duration))/fs
    if kind == 'Pure tone':
        y = .6*np.sin(2*np.pi*440*t)
    elif kind == 'Two simultaneous tones':
        y = .3*np.sin(2*np.pi*440*t)+.3*np.sin(2*np.pi*880*t)
    elif kind == 'Two sequential tones':
        y = .6*np.sin(2*np.pi*np.where(t<duration/2,440,880)*t)
    else:
        y = .6*np.sin(2*np.pi*(200*t + .5*(2000-200)/duration*t*t))
    return y, fs


def read_wav(data):
    if len(data) > 20_000_000:
        raise ValueError('Please choose a WAV file smaller than 20 MB.')
    with wave.open(io.BytesIO(data),'rb') as w:
        fs, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        if not 1000 <= fs <= 192000 or not 1 <= channels <= 8:
            raise ValueError('Unsupported sample rate or channel count.')
        truncated = w.getnframes() > MAX_SECONDS*fs
        raw = w.readframes(min(w.getnframes(), MAX_SECONDS*fs))
    if width == 1:
        y=(np.frombuffer(raw,np.uint8).astype(float)-128)/128
    elif width in (2,4):
        y=np.frombuffer(raw, '<i2' if width==2 else '<i4').astype(float)/2**(width*8-1)
    elif width==3:
        b=np.frombuffer(raw,np.uint8).reshape(-1,3).astype(np.int32)
        v=b[:,0] | b[:,1]<<8 | b[:,2]<<16
        y=((v ^ 0x800000)-0x800000)/8388608
    else:
        raise ValueError('Use an uncompressed PCM WAV file (8, 16, 24, or 32 bit).')
    y=y.reshape(-1,channels).mean(axis=1)
    if len(y)<32:
        raise ValueError('Audio is too short to analyze.')
    return y,fs,truncated


def write_wav(y, fs):
    out=io.BytesIO()
    with wave.open(out,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(fs))
        w.writeframes((np.clip(y,-1,1)*32767).astype('<i2').tobytes())
    return out.getvalue()


def analyze(y,fs,window_ms=64,overlap=.75,window='Hann'):
    y=np.asarray(y,dtype=float)
    if len(y)<32 or not np.all(np.isfinite(y)):
        raise ValueError('Audio must contain at least 32 finite samples.')
    y=y-y.mean()
    win=np.hanning(len(y)) if window=='Hann' else np.ones(len(y))
    amp=np.abs(np.fft.rfft(y*win))/win.sum()
    amp[1:] *= 2
    if len(y)%2==0: amp[-1]/=2
    freq=np.fft.rfftfreq(len(y),1/fs)
    n=min(len(y),max(32,round(fs*window_ms/1000)))
    hop=max(1,round(n*(1-overlap)))
    starts=np.arange(0,len(y)-n+1,hop)
    # Build only the requested frames. A view of EVERY possible window
    # exceeds Pyodide's 32-bit array-size limit before hop slicing occurs.
    frames=np.stack([y[start:start+n] for start in starts])
    taper=np.hanning(n) if window=='Hann' else np.ones(n)
    spec=np.abs(np.fft.rfft(frames*taper,axis=1))/taper.sum()
    spec[:,1:] *= 2
    if n%2==0: spec[:,-1]/=2
    peak=max(float(spec.max()),1e-12)
    db=20*np.log10(np.maximum(spec/peak,1e-6))
    if spec.max()<1e-10: db[:]=-120
    return dict(frequency=freq,amplitude=amp,stft_frequency=np.fft.rfftfreq(n,1/fs),
                time=(starts+n/2)/fs,db=db.T,n=n,hop=hop,
                dominant=None if amp.max()<1e-10 else freq[np.argmax(amp)],
                rms=float(np.sqrt(np.mean(y*y))))
