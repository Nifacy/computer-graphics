import sys
from typing import Callable

import numpy as np
from PyQt5.QtCore import QSize, Qt, QPoint
from PyQt5.QtGui import QPainter, QPaintEvent, QPen, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QApplication, QWidget, QFrame


def points_calculator(a: float) -> Callable[[np.arange], np.ndarray]:
    def calculate_values(arguments: np.arange) -> np.ndarray:
        sin_phi = np.sin(arguments)
        cos_phi = np.cos(arguments)
        r_values = 2 * a * sin_phi * cos_phi
        x_values = r_values * cos_phi
        y_values = r_values * sin_phi
        return np.array([x_values, y_values]).transpose()
    return calculate_values


class GraphicWidget(QFrame):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setStyleSheet('background-color: grey;')
        self.__points: np.ndarray = np.empty((0, 2))
        self.__center = QPoint(0, 0)
        self.__scale = 1.0
        self.__delta_coef = 0.03
        self.__drag_start_point = None
        self.__drag_center_snapshot = None

    def __draw_points(self, painter: QPainter) -> None:
        pen = QPen(Qt.black, 4, Qt.SolidLine)
        painter.setPen(pen)

        for index in range(len(self.__points) - 1):
            start_point = self.__points[index] * self.__scale
            end_point = self.__points[index + 1] * self.__scale
            painter.drawLine(
                int(start_point[0]), int(start_point[1]),
                int(end_point[0]), int(end_point[1]),
            )

    def __get_painter(self) -> QPainter:
        painter = QPainter()
        painter.setRenderHint(QPainter.Antialiasing)
        return painter

    def draw_points(self, points: np.ndarray) -> None:
        self.__points = points

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = self.__get_painter()
        painter.begin(self)
        painter.translate(self.__center)
        self.__draw_points(painter)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.__drag_start_point = QPoint(event.x(), event.y())
            self.__drag_center_snapshot = self.__center

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.__drag_start_point is not None:
            delta = event.pos() - self.__drag_start_point
            self.__center = self.__drag_center_snapshot + delta
            self.repaint()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.__drag_start_point = None
        self.__drag_center_snapshot = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        direction = [-1, 1][event.angleDelta().y() >= 0]
        self.__scale *= 1 + direction * self.__delta_coef
        self.repaint()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.__calculate_points = points_calculator(100)
        self.setFixedSize(QSize(400, 400))
        self.__init_widgets()

    def __init_widgets(self):
        self.__graphic = GraphicWidget(self)
        self.__graphic.setFixedSize(QSize(400, 400))
        self.__graphic.draw_points(self.__calculate_points(np.arange(0, np.pi, 0.001)))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
