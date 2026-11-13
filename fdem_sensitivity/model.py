"""Full layered-earth magnetic dipole FDEM, plus a separate LIN teaching kernel."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from shared.em_model import MU0
from shared import empymod_numpy as em

@dataclass(frozen=True)
class Acquisition:
    spacing: float = 10.0
    orientation: str = 'HCP · vertical magnetic dipoles'
    first_hz: float = 100.0
    last_hz: float = 100000.0
    gates: int = 24

    @property
    def axis(self):
        if not (0 < self.first_hz < self.last_hz and self.spacing > 0 and self.gates >= 3):
            raise ValueError('Choose positive spacing and minimum frequency < maximum frequency.')
        if self.orientation not in ORIENTATIONS:
            raise ValueError('Unknown coil orientation.')
        return np.geomspace(self.first_hz, self.last_hz, self.gates)

ORIENTATIONS = ['HCP · vertical magnetic dipoles', 'VCP · horizontal magnetic dipoles']

@lru_cache(maxsize=128)
def _response(earth, acquisition):
    earth.validate()
    f = acquisition.axis
    s = acquisition.spacing
    # HCP: z moments. VCP: y moments perpendicular to x separation. Both
    # primary fields are -m/(4*pi*s³). empymod's magnetic source is normalized
    # to magnetic current; i*omega*mu converts it to magnetic dipole moment.
    h = em.dipole(src=[0, 0, -.1], rec=[s, 0, -.1], depth=[0, earth.thickness],
        res=earth.resistivities, epermH=[0, 0, 0], freqtime=f, ab=66 if acquisition.orientation == ORIENTATIONS[0] else 55,
        xdirect=None, verb=0)
    ratio = h * (-4*np.pi*s**3 * 2j*np.pi*f*MU0)
    return np.column_stack([ratio.real, ratio.imag]) * 1e6  # secondary/primary ppm

def forward(earth, acquisition):
    return _response(earth, acquisition).copy()

def apparent_conductivity(quadrature_ppm, acquisition):
    """McNeill low-induction conversion, mS/m; not a full-response inversion."""
    return 4 * np.asarray(quadrature_ppm) * 1e-6 / (MU0*2*np.pi*acquisition.axis*acquisition.spacing**2) * 1000

def cumulative(z, spacing, orientation):
    u = np.asarray(z) / spacing
    root = np.sqrt(1 + 4*u*u)
    return 1/root if orientation == ORIENTATIONS[0] else 1/(root+2*u)

def depth_weight(z, spacing, orientation):
    """Normalized LIN sensitivity density at zero instrument height (1/m)."""
    u = np.asarray(z) / spacing
    if orientation == ORIENTATIONS[0]:
        return 4*u / (spacing*(1+4*u*u)**1.5)
    return (2 - 4*u/np.sqrt(1+4*u*u)) / spacing
