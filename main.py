import sys
from typing import Callable, Iterable

import numpy as np
from PyQt5.QtCore import QSize, Qt, QPoint, QTimer, QRect
from PyQt5.QtGui import QPainter, QPaintEvent, QPen, QMouseEvent, QWheelEvent, QColor, QFont, QFontMetrics
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
    def __init__(self, parent: QWidget | None, calculate_points: Callable[[np.arange], np.ndarray]):
        super().__init__(parent)
        self.__points: np.ndarray = np.empty((0, 2))
        self.__default_step = 0.2
        self.__scale = 1.0
        self.__calculate_points = calculate_points
        self.__center = QPoint(0, 0)
        self.__delta_coef = 0.03

        self.__grid_cell_size = 50

        self.__drag_start_point = None
        self.__drag_center_snapshot = None

        self.__wheel_scroll_end_timer = QTimer()
        self.__wheel_scroll_end_timer.setSingleShot(True)
        self.__wheel_scroll_end_timer.timeout.connect(self.__on_wheel_scroll_end)

        self.__update_points()

    def __get_grid_line_positions(self, center_coord: float, a: int, b: int, step: float) -> Iterable[float]:
        coordinates = [center_coord]
        offset = step

        while (a < center_coord - offset) or (center_coord + offset < b):
            if center_coord - offset < b:
                coordinates.insert(0, center_coord - offset)
            if a < center_coord + offset:
                coordinates.append(center_coord + offset)
            offset += step

        return coordinates

    def __draw_grid_cells(self, painter: QPainter, cell_size: float, with_text: bool = False) -> None:
        width, height = self.geometry().width(), self.geometry().height()

        for x in self.__get_grid_line_positions(self.__center.x(), 0, width, cell_size):
            painter.drawLine(int(x), 0, int(x), height)

            if with_text:
                normalized_x = (x - self.__center.x()) / self.__scale
                represented_position = f"{normalized_x:.2f}"
                metrics = QFontMetrics(painter.font())
                rect = QRect(int(x), 0, metrics.width(represented_position), metrics.height())
                painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, represented_position)

        for y in self.__get_grid_line_positions(self.__center.y(), 0, height, cell_size):
            if with_text:
                normalized_y = (y - self.__center.y()) / self.__scale
                represented_position = f"{normalized_y:.2f}"
                metrics = QFontMetrics(painter.font())
                rect = QRect(0, int(y), metrics.width(represented_position), metrics.height())
                painter.drawText(rect, Qt.AlignLeft | Qt.AlignBottom, represented_position)

            painter.drawLine(0, int(y), width, int(y))

    def __draw_grid(self, painter: QPainter) -> None:
        pen = QPen(Qt.gray, 2, Qt.SolidLine)
        painter.setPen(pen)

        font = QFont('Arial', 10)
        painter.setFont(font)

        big_cell_size = self.__grid_cell_size * self.__scale
        small_cell_size = big_cell_size / 5

        painter.setPen(QPen(QColor(220, 220, 220), 2, Qt.SolidLine))
        self.__draw_grid_cells(painter, small_cell_size)

        painter.setPen(QPen(QColor(192, 192, 192), 2, Qt.SolidLine))
        self.__draw_grid_cells(painter, big_cell_size, with_text=True)

    def __draw_points(self, painter: QPainter) -> None:
        pen = QPen(Qt.black, 4, Qt.SolidLine)
        painter.translate(self.__center)
        painter.setPen(pen)

        for index in range(len(self.__points) - 1):
            start_point = self.__points[index] * self.__scale
            end_point = self.__points[index + 1] * self.__scale
            painter.drawLine(
                int(start_point[0]), int(start_point[1]),
                int(end_point[0]), int(end_point[1]),
            )

        painter.translate(-self.__center)

    def __get_painter(self) -> QPainter:
        painter = QPainter()
        painter.setRenderHint(QPainter.Antialiasing)
        return painter

    def __update_points(self) -> None:
        step = self.__default_step / self.__scale
        self.__points = self.__calculate_points(np.arange(0, np.pi, step))
        self.repaint()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = self.__get_painter()
        painter.begin(self)
        self.__draw_grid(painter)
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
        self.__wheel_scroll_end_timer.start(500)
        self.repaint()

    def __on_wheel_scroll_end(self) -> None:
        self.__update_points()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.__calculate_points = points_calculator(100)
        self.setFixedSize(QSize(400, 400))
        self.__init_widgets()

    def __init_widgets(self):
        self.__graphic = GraphicWidget(self, self.__calculate_points)
        self.__graphic.setFixedSize(QSize(400, 400))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
