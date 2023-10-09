import sys
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
from PyQt5.QtCore import QPoint, QTimer, QRect, pyqtSignal, QSize
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPaintEvent, QPen, QMouseEvent, QWheelEvent, QColor, QFont, QFontMetrics
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDoubleSpinBox, QCheckBox


def points_calculator(a: float) -> Callable[[np.arange], np.ndarray]:
    def calculate_values(arguments: np.arange) -> np.ndarray:
        sin_phi = np.sin(arguments)
        cos_phi = np.cos(arguments)
        r_values = 2 * a * sin_phi * cos_phi
        x_values = r_values * cos_phi
        y_values = r_values * sin_phi
        return np.array([x_values, y_values]).transpose()

    return calculate_values


class SettingsWidget(QWidget):
    @dataclass(frozen=True)
    class Settings:
        render_range: tuple[float, float]
        precision: float
        auto_scale: bool

    on_change = pyqtSignal(Settings)

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        self.__init_widgets(main_layout)
        self.setLayout(main_layout)

    def __create_double_spin_box(self, start: float, end: float, default: float):
        spinbox = QDoubleSpinBox()
        spinbox.setDecimals(2)
        spinbox.setMinimum(start)
        spinbox.setMaximum(end)
        spinbox.setSingleStep(0.01)
        spinbox.setValue(default)
        spinbox.setFixedWidth(100)
        return spinbox

    def __init_range_field(self, layout: QVBoxLayout):
        subfields_layout = QVBoxLayout()

        self.__left_side_spin_box = self.__create_double_spin_box(0, 2 * np.pi, 0)
        self.__left_side_spin_box.valueChanged.connect(
            lambda _: self.__notify_about_settings_changed()
        )

        self.__right_side_spin_box = self.__create_double_spin_box(0, 2 * np.pi, 2 * np.pi)
        self.__right_side_spin_box.valueChanged.connect(
            lambda _: self.__notify_about_settings_changed()
        )

        left_side_layout = QHBoxLayout()
        left_side_layout.addWidget(QLabel('Левая грань: '), 0)
        left_side_layout.addWidget(self.__left_side_spin_box, 1)

        right_side_layout = QHBoxLayout()
        right_side_layout.addWidget(QLabel('Правая грань: '), 0)
        right_side_layout.addWidget(self.__right_side_spin_box, 1)

        subfields_layout.addLayout(left_side_layout)
        subfields_layout.addLayout(right_side_layout)
        layout.addLayout(subfields_layout)

    def __init_precision_field(self, layout: QVBoxLayout):
        fields_layout = QVBoxLayout()

        self.__precision_input_field = self.__create_double_spin_box(0.01, 2 * np.pi, 0.03)
        self.__precision_input_field.valueChanged.connect(lambda _: self.__notify_about_settings_changed())

        self.__auto_precision_checkbox = QCheckBox()
        self.__auto_precision_checkbox.stateChanged.connect(
            lambda _: self.__notify_about_settings_changed()
        )
        self.__auto_precision_checkbox.stateChanged.connect(
            lambda state: self.__precision_input_field.setEnabled(state != Qt.Checked)
        )

        user_defined_precision_field_layout = QHBoxLayout()
        user_defined_precision_field_layout.addWidget(
            QLabel('Шаг отрисовки:'),
            0,
        )
        user_defined_precision_field_layout.addWidget(
            self.__precision_input_field,
            1,
        )

        auto_precision_field_layout = QHBoxLayout()


        auto_precision_field_layout.addWidget(
            QLabel('Автоматическое определение'),
            0,
        )
        auto_precision_field_layout.addWidget(
            self.__auto_precision_checkbox,
            1,
        )

        fields_layout.addLayout(user_defined_precision_field_layout)
        fields_layout.addLayout(auto_precision_field_layout)
        layout.addLayout(fields_layout)

    def __init_widgets(self, layout: QVBoxLayout):
        layout.addWidget(QLabel('Область значений'))
        self.__init_range_field(layout)

        layout.addWidget(QLabel('Точность графика'))
        self.__init_precision_field(layout)

        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

    def __notify_about_settings_changed(self):
        settings = SettingsWidget.Settings(
            render_range=(
                self.__left_side_spin_box.value(),
                self.__right_side_spin_box.value(),
            ),
            precision=self.__precision_input_field.value(),
            auto_scale=self.__auto_precision_checkbox.isChecked(),
        )

        self.on_change.emit(settings)


class GraphicWidget(QFrame):
    def __init__(
            self,
            parent: QWidget | None,
            calculate_points: Callable[[np.arange], np.ndarray],
            settings_widget: SettingsWidget
    ):
        super().__init__(parent)

        self.__points: np.ndarray = np.empty((0, 2))
        self.__render_range = (0, 2 * np.pi, 0.03)
        self.__enable_auto_scale = False
        self.__default_step = 0.2
        self.__scale = 1.0
        self.__calculate_points = calculate_points
        self.__center = None
        self.__delta_coef = 0.03

        self.__grid_cell_size = 50

        self.__drag_start_point = None
        self.__drag_center_snapshot = None

        self.__wheel_scroll_end_timer = QTimer()
        self.__wheel_scroll_end_timer.setSingleShot(True)
        self.__wheel_scroll_end_timer.timeout.connect(self.__on_wheel_scroll_end)

        settings_widget.on_change.connect(self.__on_settings_changed)
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

        for y in self.__get_grid_line_positions(self.__center.y(), 0, height, cell_size):
            painter.drawLine(0, int(y), width, int(y))

    def __draw_axis_lines(self, painter: QPainter, cell_size: float):
        width, height = self.geometry().width(), self.geometry().height()
        pen = QPen(QColor(100, 100, 100), 4, Qt.SolidLine)
        painter.setPen(pen)

        x_start = QPoint(0, self.__center.y())
        x_end = QPoint(self.width(), self.__center.y())

        y_start = QPoint(self.__center.x(), 0)
        y_end = QPoint(self.__center.x(), self.height())

        left_side_delta = QPoint(-10, -10)
        right_side_delta = QPoint(-10, 10)

        painter.drawLine(x_start, x_end)
        painter.drawLine(x_end + left_side_delta, x_end)
        painter.drawLine(x_end + right_side_delta, x_end)

        text = 'X'
        metrics = QFontMetrics(painter.font())
        text_rect_size = QSize(metrics.width(text), metrics.height())
        rect = QRect(
            x_end - QPoint(text_rect_size.width() + 10, text_rect_size.height() + 10),
            text_rect_size
        )
        painter.drawText(rect, Qt.AlignBottom, text)

        painter.drawLine(y_start, y_end)
        painter.drawLine(y_start - left_side_delta, y_start)
        painter.drawLine(y_start - right_side_delta.transposed(), y_start)

        text = 'Y'
        metrics = QFontMetrics(painter.font())
        text_rect_size = QSize(metrics.width(text), metrics.height())
        rect = QRect(
            y_start + QPoint(10, 10),
            text_rect_size
        )
        painter.drawText(rect, Qt.AlignBottom, text)

        for x in self.__get_grid_line_positions(self.__center.x(), 0, width, cell_size):
            normalized_x = (x - self.__center.x()) / self.__scale
            represented_position = f"{round(normalized_x)}"
            metrics = QFontMetrics(painter.font())
            rect = QRect(int(x), self.__center.y(), metrics.width(represented_position), metrics.height())
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, represented_position)

        for y in self.__get_grid_line_positions(self.__center.y(), 0, height, cell_size):
            normalized_y = (y - self.__center.y()) / self.__scale
            represented_position = f"{round(normalized_y)}"
            metrics = QFontMetrics(painter.font())
            rect = QRect(self.__center.x(), int(y), metrics.width(represented_position), metrics.height())
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignBottom, represented_position)

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

        self.__draw_axis_lines(painter, big_cell_size)

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
        render_range = np.arange(
            self.__render_range[0],
            self.__render_range[1],
            self.__default_step / self.__scale if self.__enable_auto_scale else self.__render_range[2]
        )

        self.__points = self.__calculate_points(render_range)
        self.repaint()

    def __on_settings_changed(self, settings: SettingsWidget.Settings):
        self.__render_range = (*settings.render_range, settings.precision)
        self.__enable_auto_scale = settings.auto_scale
        self.__update_points()
        self.repaint()

    def __init_center(self):
        self.__center = QPoint(self.width() // 2, self.height() // 2)

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.__center is None:
            self.__init_center()
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
        self.setMinimumSize(QSize(700, 400))

        self.__calculate_points = points_calculator(100)

        self.__layout = QVBoxLayout()
        self.__init_widgets(self.__layout)
        self.setLayout(self.__layout)

    def __init_widgets(self, layout: QVBoxLayout):
        graph_with_settings_layout = QHBoxLayout()

        settings = SettingsWidget()
        graph_with_settings_layout.addWidget(settings, 0)

        graphic = GraphicWidget(self, self.__calculate_points, settings)
        graph_with_settings_layout.addWidget(graphic, 1)

        layout.addLayout(graph_with_settings_layout)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
