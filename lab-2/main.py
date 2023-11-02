import sys
import time

import renderer

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPainter, QPaintEvent, QImage, QColor
from PyQt5.QtWidgets import QApplication, QFrame
from PyQt5.QtWidgets import QWidget

from renderer import Color, Point


class QImageViewport(renderer.IViewport):
    def __init__(self, width: int, height: int) -> None:
        self._image = self.__create_image(width, height)
        self._cx, self._cy = width // 2, height // 2
        self._w, self._h = width, height

    @staticmethod
    def __create_image(width: str, height: str) -> QImage:
        image = QImage(QSize(width, height), QImage.Format_RGB32)
        image.fill(QColor(255, 255, 255))
        return image

    @staticmethod
    def __to_bin_format(color: renderer.Color) -> int:
        return color.b + (color.g << 8) + (color.r << 16)

    def put_pixel(self, point: Point, color: Color) -> None:
        x = self._cx + point.x
        y = self._cy - point.y

        if 0 <= x < self.width() and 0 <= y < self.height():
            self._image.setPixel(x, y, self.__to_bin_format(color))
    
    @property
    def image(self) -> QImage:
        return self._image

    def width(self) -> int:
        return self._image.width()
    
    def height(self) -> int:
        return self._image.height()


class Canvas(QFrame):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(400, 400))

        self._triangles = [
            renderer.Triangle(
                points=(
                    renderer.Point(0, 1, 2),
                    renderer.Point(-2, -1, 6),
                    renderer.Point(0, -1, 8),
                ),
                color=renderer.Color(255, 0, 0),
            ),
        ]

        self._renderer = renderer.Renderer(renderer.Config(
            d=1,
            view_size=(1.0, 1.0),
            mode=renderer.RenderMode.WIREFRAME,
        ))

    def put_pixel(self, image: QImage, point: tuple[int, int], color: QColor) -> None:
        image.setPixelColor(point[0], point[1], color)
    
    def paintEvent(self, _: QPaintEvent) -> None:
        painter = QPainter()
        viewport = QImageViewport(self.size().width(), self.size().height())

        painter.begin(self)
        self._renderer.render(viewport, self._triangles)
        painter.drawImage(0, 0, viewport.image)
        painter.end()

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
