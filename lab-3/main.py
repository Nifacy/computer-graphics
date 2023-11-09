import math
import sys
from typing import Iterable
import numpy as np

import engine.renderer as renderer

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPainter, QMouseEvent, QPaintEvent, QWheelEvent, QResizeEvent, QImage, QColor, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox, QLabel, QSpacerItem, QSizePolicy

from engine import model, renderer, models, scene
from model_templates import cylinder


class QImageViewport(renderer.IViewport):
    def __init__(self, width: int, height: int) -> None:
        self._image = self.__create_image(width, height)
        self._width = width
        self._height = height

    @staticmethod
    def __create_image(width: str, height: str) -> QImage:
        image = QImage(QSize(width, height), QImage.Format_RGBA8888)
        image.fill(QColor(255, 255, 255, 255))
        return image

    def update(self, data: np.ndarray) -> None:
        bytesPerLine = 4 * self.width()
        qimage = QImage(data.data, self.width(), self.height(), bytesPerLine, QImage.Format_RGBA8888)
        self._image = qimage

    @property
    def image(self) -> QImage:
        return self._image

    def width(self) -> int:
        return self._width
    
    def height(self) -> int:
        return self._height


class UserMoveActionHandler:
    def __init__(self, obj: scene.GameObject):
        self._obj = obj
        self._start_position = None
        self._start_point = None

    def start(self, point: tuple[int, int]) -> None:
        self._start_position = self._obj.position
        self._start_point = point
    
    def update(self, point: tuple[int, int]) -> None:
        if self._start_point is None:
            return
        delta = models.Point(point[0] - self._start_point[0], self._start_point[1] - point[1], 0)
        self._obj.position = self._start_position + delta * 0.05
    
    def stop(self) -> None:
        self._start_point = None


class UserRotateActionHandler:
    def __init__(self, obj: scene.GameObject):
        self._obj = obj
        self._start_rotation = None
        self._start_point = None

    def start(self, point: tuple[int, int]) -> None:
        self._start_rotation = self._obj.rotation
        self._start_point = point
    
    def update(self, point: tuple[int, int]) -> None:
        if self._start_point is None:
            return
        delta = models.Point(self._start_point[1] - point[1], self._start_point[0] - point[0], 0)
        self._obj.rotation = self._start_rotation + delta * 0.01
    
    def stop(self) -> None:
        self._start_point = None


class UserScaleAction:
    def __init__(self, obj: scene.GameObject):
        self._obj = obj

    def update(self, direction: int) -> None:
        new_scale = self._obj.scale + direction * 0.03
        self._obj.scale = max(new_scale, 0.0)


class SettingsWidget(QWidget):
    _RENDER_MODE = {
        'Каркасная': renderer.RenderMode.WIREFRAME,
        'Заливка': renderer.RenderMode.FILL,
    }

    _PROJECTION_TYPE = {
        'Изометрия': renderer.ProjectionType.ISOMETRIC,
        'Перспектива': renderer.ProjectionType.PERSPECTIVE,
    }

    class _Spinbox(QDoubleSpinBox):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.__edit_lock = False
            self.valueChanged.connect(self.__notify_about_changes)
            self._on_change_subscribers = []

        def setValue(self, val: float) -> None:
            if not self.__edit_lock:
                super().setValue(val)

        def focusInEvent(self, event):
            super().focusInEvent(event)
            self.__edit_lock = True

        def focusOutEvent(self, event):
            super().focusOutEvent(event)
            self.__edit_lock = False

        def __notify_about_changes(self):
            if not self.__edit_lock:
                return

            for subscriber in self._on_change_subscribers:
                subscriber(self.value())

        def on_change(self, subscriber):
            if subscriber not in self._on_change_subscribers:
                self._on_change_subscribers.append(subscriber)

    def __init__(self, config: renderer.Config, object: scene.GameObject, lights: dict[str, scene.Light]):
        super().__init__()
        self.__config = config
        self.__object = object
        self.__lights = lights

        main_layout = QVBoxLayout()
        self.__init_widgets(main_layout)
        self.setLayout(main_layout)

    def __create_double_spin_box(self, start: float, end: float | None, default: float):
        spinbox = self._Spinbox()
        spinbox.setDecimals(2)
        spinbox.setMinimum(start)

        spinbox.setMaximum(end or float('inf'))

        spinbox.setSingleStep(0.01)
        spinbox.setValue(default)
        spinbox.setFixedWidth(100)

        spinbox.on_change(lambda _: self._on_change())

        return spinbox

    def __create_combo_box(self, options: list[str], default: str):
        combo_box = QComboBox()
        combo_box.addItems(options)
        combo_box.setCurrentText(default)
        combo_box.setFixedWidth(100)

        combo_box.currentTextChanged.connect(lambda: self._on_change())

        return combo_box

    def __create_param_field(self, path: str, name: str, widget: QWidget):
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel(name), 0)
        param_layout.addWidget(widget, 1)
        return param_layout, [{'path': path, 'widget': widget}]

    def __create_param_block(self, path, name, fields):
        param_block_layout = QVBoxLayout()
        label = QLabel(name)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        label.setFont(font)
        param_block_layout.addWidget(label, 0)
        children_info = []

        for layout, child_widgets_info in fields:
            param_block_layout.addLayout(layout, 1)

            for widget_info in child_widgets_info:
                children_info.append({
                    'path': f'{path}.{widget_info["path"]}',
                    'widget': widget_info['widget'],
                })

        return param_block_layout, children_info

    def _on_change(self):
        self.__object.position = models.Point(
            self._widgets_map['position.x'].value(),
            self._widgets_map['position.y'].value(),
            self._widgets_map['position.z'].value(),
        )

        self.__object.rotation = models.Point(
            self._widgets_map['rotation.x'].value(),
            self._widgets_map['rotation.y'].value(),
            self._widgets_map['rotation.z'].value(),
        )

        self.__lights['ambient'].intensity = self._widgets_map['ambient_light.intensity'].value()
        self.__lights['point'].intensity = self._widgets_map['point_light.intensity'].value()
        self.__lights['point'].position = models.Point(
            self._widgets_map['point_light.x'].value(),
            self._widgets_map['point_light.y'].value(),
            self._widgets_map['point_light.z'].value(),
        )
        self.__lights['direction'].intensity = self._widgets_map['direction_light.intensity'].value()
        self.__lights['direction'].direction = models.Point(
            self._widgets_map['direction_light.x'].value(),
            self._widgets_map['direction_light.y'].value(),
            self._widgets_map['direction_light.z'].value(),
        )

        self.__config.mode = self._RENDER_MODE[self._widgets_map['render_mode'].currentText()]
        self.__config.projection = self._PROJECTION_TYPE[self._widgets_map['projection'].currentText()]

    def _normalize(self, angle: float) -> float:
        while not (0 <= angle <= 2 * math.pi):
            if angle < 0: angle += 2 * math.pi
            else: angle -= 2 * math.pi
        return angle

    def paintEvent(self, event: QPaintEvent) -> None:
        self._widgets_map['position.x'].setValue(self.__object.position.x)
        self._widgets_map['position.y'].setValue(self.__object.position.y)
        self._widgets_map['position.z'].setValue(self.__object.position.z)

        self._widgets_map['rotation.x'].setValue(self._normalize(self.__object.rotation.x))
        self._widgets_map['rotation.y'].setValue(self._normalize(self.__object.rotation.y))
        self._widgets_map['rotation.z'].setValue(self._normalize(self.__object.rotation.z))

        self.update()

    def __init_widgets(self, layout: QVBoxLayout):
        self._widgets_map = dict()

        d = [
            self.__create_param_block(
                'point_light', 'Свет (точечный)',
                [
                    self.__create_param_field(
                        'x', 'x',
                        self.__create_double_spin_box(-10, 10, 0),
                    ),
                    self.__create_param_field(
                        'y', 'y',
                        self.__create_double_spin_box(-10, 10, 0),
                    ),
                    self.__create_param_field(
                        'z', 'z',
                        self.__create_double_spin_box(-10, 10, 0),
                    ),
                    self.__create_param_field(
                        'intensity', 'Интенсивность',
                        self.__create_double_spin_box(0, 2, 1),
                    ),
                ]
            ),

            self.__create_param_block(
                'direction_light', 'Свет (направленный)',
                [
                    self.__create_param_field(
                        'x', 'x',
                        self.__create_double_spin_box(-10, 10, 0),
                    ),
                    self.__create_param_field(
                        'y', 'y',
                        self.__create_double_spin_box(-10, 10, 0),
                    ),
                    self.__create_param_field(
                        'z', 'z',
                        self.__create_double_spin_box(-10, 10, 0),
                    ),
                    self.__create_param_field(
                        'intensity', 'Интенсивность',
                        self.__create_double_spin_box(0, 2, 1),
                    ),
                ]
            ),

            self.__create_param_block(
                'ambient_light', 'Свет (рассеянный)',
                [
                    self.__create_param_field(
                        'intensity', 'Интенсивность',
                        self.__create_double_spin_box(0, 2, 1),
                    ),
                ]
            ),

            self.__create_param_block(
                'position', 'Координаты',
                [
                    self.__create_param_field(
                        'x', 'x',
                        self.__create_double_spin_box(-10, 10, 0)
                    ),
                    self.__create_param_field(
                        'y', 'y',
                        self.__create_double_spin_box(-10, 10, 0)
                    ),
                    self.__create_param_field(
                        'z', 'z',
                        self.__create_double_spin_box(-10, 10, 5)
                    ),
                ]
            ),

            self.__create_param_block(
                'rotation', 'Поворот',
                [
                    self.__create_param_field(
                        'x', 'x',
                        self.__create_double_spin_box(0, 2 * math.pi, 0)
                    ),
                    self.__create_param_field(
                        'y', 'y',
                        self.__create_double_spin_box(0, 2 * math.pi, 0)
                    ),
                    self.__create_param_field(
                        'z', 'z',
                        self.__create_double_spin_box(0, 2 * math.pi, 0)
                    ),
                ]
            ),

            self.__create_param_field(
                'render_mode', 'Режим рендеринга:',
                self.__create_combo_box(['Каркасная', 'Заливка'], 'Заливка')
            ),

            self.__create_param_field(
                'projection', 'Проекция:',
                self.__create_combo_box(['Перспектива', 'Изометрия'], 'Перспектива')
            ),
        ]

        for param_layout, widgets_info in d:
            layout.addLayout(param_layout)
            for widget_info in widgets_info:
                self._widgets_map[widget_info['path']] = widget_info['widget']

        print(self._widgets_map)
        layout.addItem(QSpacerItem(200, 1000, QSizePolicy.Minimum, QSizePolicy.Expanding))



class Canvas(QFrame):
    def __init__(
            self,
            parent: QWidget,
            render_config: renderer.Config,
            object: scene.GameObject,
            lights: Iterable[scene.Light],
    ) -> None:
        super().__init__(parent)
        self.setMinimumSize(QSize(400, 400))
        self.setStyleSheet('background-color: #000000')

        self._pyramid = object
        self._lights = tuple(lights)

        self._render_config = render_config

        self._renderer = renderer.Renderer(self._render_config)

        self._move_handler = UserMoveActionHandler(self._pyramid)
        self._rotate_handler = UserRotateActionHandler(self._pyramid)
        self._scale_handler = UserScaleAction(self._pyramid)

    def put_pixel(self, image: QImage, point: tuple[int, int], color: QColor) -> None:
        image.setPixelColor(point[0], point[1], color)

    def paintEvent(self, _: QPaintEvent) -> None:
        painter = QPainter()
        viewport = QImageViewport(self.size().width(), self.size().height())

        painter.begin(self)
        self._renderer.render(viewport, self._pyramid.mesh(), self._lights)

        painter.drawImage(0, 0, viewport.image)
        painter.end()

        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        point = (event.pos().x(), event.pos().y())

        if event.button() == Qt.LeftButton:
            self._move_handler.start(point)
        elif event.button() == Qt.RightButton:
            self._rotate_handler.start(point)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        point = (event.pos().x(), event.pos().y())
        self._move_handler.update(point)
        self._rotate_handler.update(point)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._move_handler.stop()
        self._rotate_handler.stop()

    def wheelEvent(self, event: QWheelEvent) -> None:
        direction = [-1, 1][event.angleDelta().y() >= 0]
        self._scale_handler.update(direction)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._render_config.view_size = (1.0, event.size().height() / event.size().width())


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(QSize(400, 400))

        self.__render_config = renderer.Config(
            d=1,
            view_size=(1.0, 1.0),
            mode=renderer.RenderMode.FILL,
            projection=renderer.ProjectionType.PERSPECTIVE,
        )

        vertices_amount = int(input('Количество вершин: '))
        self.__object = scene.GameObject(
            scale=1,
            rotation=models.Point(0, 0, 0),
            position=models.Point(0, 0, 5),
            mesh=cylinder(1.0, 2.0, vertices_amount, models.Color(0, 255, 0), 500.0),
        )

        self.__lights = {
            'ambient' : scene.AmbientLight(1.0),
            'point': scene.PointLight(1.0, models.Point(0.0, 0.0, 0.0)),
            'direction': scene.PointLight(0.0, models.Point(0.0, 0.0, 0.0)),
        }

        self.__layout = QVBoxLayout()
        self.__init_widgets(self.__layout)
        self.setLayout(self.__layout)

    def __init_widgets(self, layout: QVBoxLayout) -> None:
        canvas_with_settings_layout = QHBoxLayout()

        canvas_with_settings_layout.addWidget(SettingsWidget(
            self.__render_config,
            self.__object,
            self.__lights,
        ), 0)

        canvas_with_settings_layout.addWidget(
            Canvas(self, self.__render_config, self.__object, self.__lights.values()),
            1,
        )

        layout.addLayout(canvas_with_settings_layout)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
