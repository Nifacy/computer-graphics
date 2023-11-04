import sys

import numpy as np

import engine.renderer as renderer

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPainter, QMouseEvent, QPaintEvent, QWheelEvent, QImage, QColor
from PyQt5.QtWidgets import QApplication, QFrame
from PyQt5.QtWidgets import QWidget

from engine import model, renderer, models, scene


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


class Canvas(QFrame):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(400, 400))

        self._pyramid = scene.GameObject(
            scale=2,
            rotation=models.Point(0, 0, 0),
            position=models.Point(0, 0, 5),
            mesh=model.load('./models/pyramid.obj'),
        )
        
        self._renderer = renderer.Renderer(renderer.Config(
            d=1,
            view_size=(1.0, 1.0),
            mode=renderer.RenderMode.FILL,
            projection=renderer.ProjectionType.PERSPECTIVE,
        ))

        self._move_handler = UserMoveActionHandler(self._pyramid)
        self._rotate_handler = UserRotateActionHandler(self._pyramid)
        self._scale_handler = UserScaleAction(self._pyramid)

    def put_pixel(self, image: QImage, point: tuple[int, int], color: QColor) -> None:
        image.setPixelColor(point[0], point[1], color)

    def paintEvent(self, _: QPaintEvent) -> None:
        painter = QPainter()
        viewport = QImageViewport(self.size().width(), self.size().height())

        painter.begin(self)
        self._renderer.render(viewport, self._pyramid.mesh())
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



class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(QSize(400, 400))
        self.__init_widgets()

    def __init_widgets(self):
        self.__canvas = Canvas(self)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    app.exec()


if __name__ == '__main__':
    main()
