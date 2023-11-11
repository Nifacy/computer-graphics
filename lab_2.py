import math
import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPainter, QMouseEvent, QPaintEvent, QWheelEvent, QResizeEvent, QImage, QColor, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox, QLabel, QSpacerItem, QSizePolicy

from engine import engine, scene, types, model


class UserMoveActionHandler:
    def __init__(self, obj: scene.SceneObject):
        self._obj = obj
        self._start_position = None
        self._start_point = None

    def start(self, point: tuple[int, int]) -> None:
        self._start_position = self._obj.position
        self._start_point = point
    
    def update(self, point: tuple[int, int]) -> None:
        if self._start_point is None:
            return
        delta = types.Vector3(point[0] - self._start_point[0], self._start_point[1] - point[1], 0)
        self._obj.position = self._start_position + delta * 0.05
    
    def stop(self) -> None:
        self._start_point = None


class UserRotateActionHandler:
    def __init__(self, obj: scene.SceneObject):
        self._obj = obj
        self._start_rotation = None
        self._start_point = None

    def start(self, point: tuple[int, int]) -> None:
        self._start_rotation = self._obj.rotation
        self._start_point = point

    def update(self, point: tuple[int, int]) -> None:
        if self._start_point is None:
            return
        delta = types.Vector3(self._start_point[1] - point[1], self._start_point[0] - point[0], 0)
        self._obj.rotation = self._start_rotation + delta * 0.01

    def stop(self) -> None:
        self._start_point = None


class UserScaleAction:
    def __init__(self, obj: scene.SceneObject):
        self._obj = obj

    def update(self, direction: int) -> None:
        new_scale = max(self._obj.scale.x + direction * 0.03, 0.0)
        self._obj.scale = types.Vector3(new_scale, new_scale, new_scale)


class SettingsWidget(QWidget):
    _RENDER_MODE = {
        'Каркасная': engine.RenderMode.WIREFRAME,
        'Заливка': engine.RenderMode.FILL,
    }

    _PROJECTION_TYPE = {
        'Изометрия': engine.ProjectionType.ISOMETRIC,
        'Перспектива': engine.ProjectionType.PERSPECTIVE,
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

    def __init__(self, _engine: engine.Engine, _scene: scene.Scene):
        super().__init__()
        self._engine = _engine
        self.__object = _scene.get_by_name('pyramid')

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
        self.__object.position = types.Vector3(
            self._widgets_map['position.x'].value(),
            self._widgets_map['position.y'].value(),
            self._widgets_map['position.z'].value(),
        )

        self.__object.rotation = types.Vector3(
            self._widgets_map['rotation.x'].value(),
            self._widgets_map['rotation.y'].value(),
            self._widgets_map['rotation.z'].value(),
        )

        self._engine.render_config.mode = self._RENDER_MODE[self._widgets_map['render_mode'].currentText()]
        self._engine.render_config.projection = self._PROJECTION_TYPE[self._widgets_map['projection'].currentText()]

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
    def __init__(self, parent: QWidget, _engine: engine.Engine, scene: scene.Scene) -> None:
        super().__init__(parent)
        self.setMinimumSize(QSize(400, 400))
        self.setStyleSheet('background-color: #000000')

        self._engine = _engine
        self._scene = scene

        pyramid = self._scene.get_by_name('pyramid')

        self._move_handler = UserMoveActionHandler(pyramid)
        self._rotate_handler = UserRotateActionHandler(pyramid)
        self._scale_handler = UserScaleAction(pyramid)

    def put_pixel(self, image: QImage, point: tuple[int, int], color: QColor) -> None:
        image.setPixelColor(point[0], point[1], color)

    def paintEvent(self, _: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)

        canvas_size = engine.CanvasSize(self.size().width(), self.size().height())
        rendered_data = self._engine.render(canvas_size, self._scene)
        image = QImage(rendered_data.data, canvas_size.width, canvas_size.height, 4 * canvas_size.width, QImage.Format_RGBA8888)
        painter.drawImage(0, 0, image)
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
        self._engine.render_config.view_size = (1.0, event.size().height() / event.size().width())


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(QSize(400, 400))

        self._render_config = engine.Config(
            d=1.0,
            view_size=(1.0, 1.0),
            mode=engine.RenderMode.FILL,
            projection=engine.ProjectionType.PERSPECTIVE,
        )

        self._engine = engine.Engine(self._render_config)

        self._pyramid = scene.SceneObject(
            name='pyramid',
            scale=types.Vector3(1.0, 1.0, 1.0),
            rotation=types.Vector3(0, 0, 0),
            position=types.Vector3(0, 0, 5),
            mesh=model.load('./models/pyramid.obj'),
        )

        self._scene = scene.Scene()
        self._scene.add_object(self._pyramid)
        self._scene.add_object(scene.AmbientLight(1.0))

        self.__layout = QVBoxLayout()
        self.__init_widgets(self.__layout)
        self.setLayout(self.__layout)

    def __init_widgets(self, layout: QVBoxLayout) -> None:
        canvas_with_settings_layout = QHBoxLayout()

        canvas_with_settings_layout.addWidget(SettingsWidget(self._engine, self._scene), 0)
        canvas_with_settings_layout.addWidget(Canvas(self, self._engine, self._scene), 1)

        layout.addLayout(canvas_with_settings_layout)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
