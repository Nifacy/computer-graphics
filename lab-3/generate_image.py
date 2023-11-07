import math
from PIL import Image
from engine import renderer, scene, models, model
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
    rotation=models.Point(math.pi / 4, math.pi / 4, 0),
    position=models.Point(0, 0, 10),
    mesh=model.load('./models/pyramid.obj'),
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
    scene.PointLight(0.6, models.Point(2, 2, 5)),
    scene.DirectionalLight(0.2, models.Point(-1, 0, 0)),
])
v.image.show()
