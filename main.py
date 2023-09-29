from typing import Callable
import numpy as np
import sys

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QWidget


def points_calculator(a: float) -> Callable[[np.arange], np.ndarray]:
    def calculate_values(arguments: np.arange) -> np.ndarray:
        sin_phi = np.sin(arguments)
        cos_phi = np.cos(arguments)
        r_values = 2 * a * sin_phi * cos_phi
        x_values = r_values * cos_phi
        y_values = r_values * sin_phi
        return np.array([x_values, y_values]).transpose()
    return calculate_values


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(QSize(400, 400))
        self.init_widgets()

    def init_widgets(self):
        pass


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
