"""Regenerate independent golden curves with optional simpeg==0.26.0.

Not a production dependency: .venv/bin/python scripts/generate_em_references.py
Do not regenerate fixtures to make a failing forward-model test pass.
"""
import json
from pathlib import Path
import sys
import numpy as np
import simpeg
from simpeg.electromagnetics import time_domain as td, frequency_domain as fd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from shared.em_model import PRESETS
from tdem_sounding.model import Acquisition as TA
from fdem_sensitivity.model import Acquisition as FA, ORIENTATIONS

cases=[]
for name,earth in PRESETS.items():
    a=TA()
    rx=td.receivers.PointMagneticFluxTimeDerivative([[0,0,.1]],a.axis,orientation='z')
    h=a.side/2
    source=td.sources.LineCurrent([rx],location=np.array([[-h,-h,.1],[h,-h,.1],[h,h,.1],[-h,h,.1],[-h,-h,.1]]),current=a.current,waveform=td.sources.StepOffWaveform())
    sim=td.Simulation1DLayered(survey=td.Survey([source]),thicknesses=[earth.thickness],sigma=[earth.sigma1,earth.sigma2],n_points_per_path=9)
    cases.append(dict(kind='tdem',preset=name,response=(-sim.dpred(None)*1e9).tolist()))
    for orientation in ORIENTATIONS:
        a=FA(orientation=orientation)
        direction='z' if orientation==ORIENTATIONS[0] else 'y'
        sources=[]
        for f in a.axis:
            rx=[fd.receivers.PointMagneticFieldSecondary([[a.spacing,0,.1]],orientation=direction,component=c) for c in ['real','imag']]
            sources.append(fd.sources.MagDipole(rx,frequency=f,location=[0,0,.1],orientation=direction))
        sim=fd.Simulation1DLayered(survey=fd.Survey(sources),thicknesses=[earth.thickness],sigma=[earth.sigma1,earth.sigma2])
        response=sim.dpred(None).reshape(-1,2)*(-4*np.pi*a.spacing**3)*1e6
        cases.append(dict(kind='fdem',preset=name,orientation=orientation,response=response.tolist()))
(ROOT/'tests/data/em_simpeg_reference.json').write_text(json.dumps(dict(simpeg_version=simpeg.__version__,cases=cases),indent=2)+'\n')
