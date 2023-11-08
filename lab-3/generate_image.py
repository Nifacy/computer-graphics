import math
from PIL import Image
from engine import renderer, scene, models
from model_templates import create_grid
import numpy


class PillowViewport(renderer.IViewport):
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self.image = None

    def update(self, data: numpy.ndarray) -> None:
        self.image = Image.fromarray(data)

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height


pyramid = scene.GameObject(
    scale=1,
    rotation=models.Point(0, math.pi / 4, 0),
    position=models.Point(0, 0, 5),
    mesh=create_grid(3, 3, 0.2),
)


r = renderer.Renderer(renderer.Config(
    d=1,
    view_size=(1.0, 1.0),
    mode=renderer.RenderMode.FILL,
    projection=renderer.ProjectionType.PERSPECTIVE,
))

v = PillowViewport(400, 400)
r.render(v, pyramid.mesh(), [
    scene.AmbientLight(0.2),
    scene.PointLight(0.6, models.Point(0, 0, 4)),
    scene.DirectionalLight(0.2, models.Point(1, 0, 0)),
])
v.image.show()
