"""Browser microphone capture. Only an explicit button click requests access."""
import param
from panel.reactive import ReactiveHTML

class Microphone(ReactiveHTML):
    payload = param.String(default='')
    _template = '''
    <div id="wrapper" style="padding:12px;border:1px solid #cbd5df;border-radius:8px;">
      <button id="record" onclick="${script('record')}" style="background:#008c95;color:white;padding:10px;border:0;border-radius:6px;">Record audio</button>
      <button id="stop" onclick="${script('stop')}" disabled style="padding:10px;margin-left:8px;">Stop</button>
      <p id="status" role="status" aria-live="polite">Ready · microphone access starts only when you press Record.</p>
    </div>'''
    _scripts = {
        'record': '''
        if (state.busy) return;
        state.busy = true;
        record.disabled = true;
        status.textContent = 'Requesting microphone access…';
        (async () => {
          try {
            if (!navigator.mediaDevices || !window.MediaRecorder) throw new Error('Recording is unavailable. Open in Chrome or Safari over HTTPS, or upload a WAV file.');
            const Context = window.AudioContext || window.webkitAudioContext;
            state.context = new Context();
            await state.context.resume();
            state.stream = await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
            const recorder = new MediaRecorder(state.stream);
            state.recorder = recorder;
            const chunks = [];
            recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
            recorder.onstop = async () => {
              clearInterval(state.timer);
              clearTimeout(state.limit);
              stop.disabled = true;
              state.stream.getTracks().forEach(t => t.stop());
              status.textContent = 'Preparing audio for analysis…';
              try {
                const blob = new Blob(chunks,{type:recorder.mimeType});
                const decoded = await state.context.decodeAudioData(await blob.arrayBuffer());
                const n = Math.min(decoded.length,Math.floor(10*decoded.sampleRate));
                const mono = new Float32Array(n);
                for(let ch=0;ch<decoded.numberOfChannels;ch++) {
                  const a=decoded.getChannelData(ch);
                  for(let i=0;i<n;i++) mono[i] += a[i]/decoded.numberOfChannels;
                }
                const bytes = new Uint8Array(mono.buffer);
                let binary='';
                for(let i=0;i<bytes.length;i+=8192) binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
                data.payload = JSON.stringify({fs:decoded.sampleRate,pcm:btoa(binary),nonce:Date.now()});
                status.textContent = 'Recorded '+(n/decoded.sampleRate).toFixed(2)+' s. Analysis updates below.';
              } catch(e) {status.textContent='Could not decode recording: '+e.message+'. Try WAV upload.';}
              finally {await state.context.close(); state.busy=false;record.disabled=false;}
            };
            recorder.onerror = () => {status.textContent='Recording failed. Try again or upload WAV.'; if(recorder.state==='recording') recorder.stop();};
            recorder.start();
            stop.disabled=false;
            const started=Date.now();
            status.textContent='Recording… 0.0 / 10 s';
            state.timer=setInterval(()=>{status.textContent='Recording… '+((Date.now()-started)/1000).toFixed(1)+' / 10 s';},100);
            state.limit=setTimeout(()=>{if(recorder.state==='recording') recorder.stop();},10000);
          } catch(e) {
            if(state.stream) state.stream.getTracks().forEach(t=>t.stop());
            if(state.context && state.context.state!=='closed') await state.context.close();
            status.textContent='Microphone unavailable: '+e.message+'. You can use an example or upload WAV.';
            state.busy=false;record.disabled=false;stop.disabled=true;
          }
        })();
        ''',
        'stop': "if(state.recorder && state.recorder.state==='recording') state.recorder.stop();",
        'remove': "clearInterval(state.timer);clearTimeout(state.limit);if(state.stream) state.stream.getTracks().forEach(t=>t.stop());if(state.context && state.context.state!=='closed') state.context.close();",
    }
