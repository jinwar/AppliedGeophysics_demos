"""Entrypoint for local use and Render. Each session receives independent widgets."""
import os
import panel as pn
from sampling_aliasing.app import create_app
from shared.style import template


def home():
    return template('Interactive field laboratory',[
        pn.pane.Markdown('''# Applied Geophysics II
### Build intuition before interpreting field data
Change a physical model, inspect synthetic measurements, and test what the observations can resolve.

## 01 · Sampling & aliasing
Explore temporal and spatial sampling, Nyquist limits, frequency resolution, and apparent wave velocity.

[**Open the sampling & aliasing laboratory →**](./sampling-aliasing)

Colorado School of Mines · Spring 2027
''')])

if __name__ == '__main__':
    host=os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    pn.serve({'/':home,'sampling-aliasing':create_app},
             address='0.0.0.0',port=int(os.environ.get('PORT','5006')),
             websocket_origin=[host] if host else ['localhost:5006','127.0.0.1:5006'],
             show=False)
