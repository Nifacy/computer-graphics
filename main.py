import numpy as np


def calculate_values(arguments: np.arange, a: float) -> np.ndarray:
    sin_phi = np.sin(arguments)
    cos_phi = np.cos(arguments)
    r_values = 2 * a * sin_phi * cos_phi
    x_values = r_values * cos_phi
    y_values = r_values * sin_phi
    return np.array([x_values, y_values])


