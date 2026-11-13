"""Common two-layer earth, reproducible observations, and bounded data fitting."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import least_squares

MU0 = 4e-7 * np.pi

@dataclass(frozen=True)
class Earth:
    sigma1: float = 0.01  # S/m
    sigma2: float = 0.1
    thickness: float = 20.0  # m

    def validate(self):
        values = np.array([self.sigma1, self.sigma2, self.thickness])
        if not np.all(np.isfinite(values)) or np.any(values <= 0):
            raise ValueError('Conductivities and thickness must be finite and positive.')

    @property
    def resistivities(self):
        self.validate()
        return [2e14, 1 / self.sigma1, 1 / self.sigma2]

PRESETS = {
    'Conductive basement': Earth(.01, .1, 20),
    'Resistive basement': Earth(.1, .005, 15),
    'Homogeneous earth': Earth(.02, .02, 20),
    'Thin conductive cover': Earth(.15, .01, 5),
}

def observe(clean, noise_percent, seed):
    """Relative Gaussian noise with an absolute floor; never clip its sign."""
    floor = .001 * np.max(np.abs(clean))
    uncertainty = np.maximum(noise_percent / 100 * np.abs(clean), floor)
    noisy = clean + np.random.default_rng(seed).normal(size=clean.shape) * uncertainty
    if noise_percent == 0:
        noisy = clean.copy()
    return noisy, uncertainty


def fit_earth(forward, acquisition, observed, uncertainty, initial):
    """Fit log parameters; weights use the exported data uncertainty."""
    def residual(x):
        return ((forward(Earth(*np.exp(x)), acquisition) - observed) / uncertainty).ravel()
    result = least_squares(residual, np.log([initial.sigma1, initial.sigma2, initial.thickness]),
        bounds=(np.log([.001, .001, 1]), np.log([.3, .3, 100])), max_nfev=35,
        diff_step=1e-3, ftol=1e-5, xtol=1e-5, gtol=1e-5)
    return Earth(*np.exp(result.x)), result


def sensitivity(forward, earth, acquisition):
    """Central derivative d(response)/d(log parameter), in response units."""
    x = np.log([earth.sigma1, earth.sigma2, earth.thickness])
    columns = []
    for i in range(3):
        delta = np.zeros(3); delta[i] = .01
        columns.append((forward(Earth(*np.exp(x + delta)), acquisition) -
                        forward(Earth(*np.exp(x - delta)), acquisition)) / .02)
    return np.stack(columns, axis=-1)


def profile(earth, max_depth):
    return dict(conductivity=[1000*earth.sigma1, 1000*earth.sigma1,
                              1000*earth.sigma2, 1000*earth.sigma2],
                depth=[0, earth.thickness, earth.thickness, max_depth])
