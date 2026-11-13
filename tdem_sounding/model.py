"""Central-loop step-off TEM over two isotropic layers, using empymod."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from shared.em_model import Earth, MU0
from shared import empymod_numpy as em

@dataclass(frozen=True)
class Acquisition:
    side: float = 40.0  # square transmitter side, m
    current: float = 1.0  # A
    first_ms: float = .03
    last_ms: float = 3.0
    gates: int = 20

    @property
    def axis(self):
        if not (0 < self.first_ms < self.last_ms and self.side > 0 and self.current > 0 and self.gates >= 3):
            raise ValueError('Choose positive loop/current and first gate < last gate.')
        return np.geomspace(self.first_ms, self.last_ms, self.gates) / 1000

@lru_cache(maxsize=128)
def _response(earth, acquisition):
    earth.validate()
    t = acquisition.axis
    a = acquisition.side / 2
    # In a horizontally layered earth each square side contributes equally at
    # its center. Five Gauss points integrate one side; multiply by four.
    # A current impulse gives -dH_step_off/dt. Multiply by mu0 and unit receiver
    # effective area for step-off induced voltage (positive chosen polarity).
    field = em.bipole(src=[-a, a, -a, -a, -.1, -.1], rec=[0, 0, -.1, 0, 90],
        depth=[0, earth.thickness], res=earth.resistivities, epermH=[0, 0, 0], freqtime=t,
        signal=0, mrec=True, strength=acquisition.current, srcpts=5,
        xdirect=None, ftarg={'pts_per_dec': 30}, verb=0)
    return np.asarray(field, dtype=float) * (4 * MU0 * 1e9)  # nV per 1 m² receiver

def forward(earth, acquisition):
    return _response(earth, acquisition).copy()
