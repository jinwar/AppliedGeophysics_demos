import json
import numpy as np
import panel as pn
import pytest
from sampling_aliasing.app import create_app


def test_sampling_frequency_controls_samples_and_presets():
    app = create_app()
    widgets = [widget for item in list(app.sidebar) + list(app.main)
               for widget in pn.panel(item).select(pn.widgets.Widget)]
    by_name = {widget.name: widget for widget in widgets}
    assert 'Mode' not in by_name
    assert 'Sampling interval (ms)' not in by_name
    assert 'Receiver spacing (m)' not in by_name
    assert not any(pn.panel(item).select(pn.Tabs) for item in app.main)
    fs = by_name['Sampling frequency (Hz)']
    assert fs.value == 100
    csv = next(w for w in widgets if isinstance(w, pn.widgets.FileDownload) and w.filename == 'samples.csv')
    params = next(w for w in widgets if isinstance(w, pn.widgets.FileDownload) and w.filename == 'parameters.json')
    for hz in [20, 125, 1000]:
        fs.value = hz
        data = np.loadtxt(csv.callback(), delimiter=',', skiprows=1)
        assert len(data) == hz
        assert data[1, 0] - data[0, 0] == pytest.approx(1 / hz)
        exported = json.loads(params.callback().getvalue())
        assert exported['fs_hz'] == hz
        assert exported['dt_ms'] == pytest.approx(1000 / hz)
        assert 'spatial' not in exported
    for name, hz in [('Well sampled', 200), ('Temporal alias', 100),
                     ('Nyquist boundary', 100), ('Two close frequencies', 200)]:
        by_name['Experiment'].value = name
        assert fs.value == hz
