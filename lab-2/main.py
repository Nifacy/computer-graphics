import sys

import numpy as np

import engine.renderer as renderer

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPainter, QPaintEvent, QImage, QColor
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

    def put_pixel(self, image: QImage, point: tuple[int, int], color: QColor) -> None:
        image.setPixelColor(point[0], point[1], color)
    
    def paintEvent(self, _: QPaintEvent) -> None:
        painter = QPainter()
        viewport = QImageViewport(self.size().width(), self.size().height())

        painter.begin(self)
        self._renderer.render(viewport, self._pyramid.mesh())
        painter.drawImage(0, 0, viewport.image)
        painter.end()

        self._pyramid.rotation += models.Point(0.01, 0, 0.01)
        self.update()


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
