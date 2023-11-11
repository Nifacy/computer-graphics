from dataclasses import dataclass
from enum import Enum
from typing import Iterable

import ctypes
import numpy

from . import types, _light, _bindings

class RenderMode(Enum):
    WIREFRAME = 1
    FILL = 2


class ProjectionType(Enum):
    ISOMETRIC = 1
    PERSPECTIVE = 2


@dataclass
class CanvasSize:
    width: int
    height: int
        

@dataclass
class Config:
    d: float
    view_size: tuple[float, float]
    mode: RenderMode
    projection: ProjectionType

    @property
    def raw(self) -> _bindings.Config:
        return _bindings.Config(
            d=self.d,
            viewSize=self.view_size,
            mode=self.mode.value,
            projection=self.projection.value,
        )


class Renderer:
    def __init__(self, config: Config) -> None:
        self._config = config

    def render(
        self,
        canvas_size: CanvasSize,
        triangles: list[types.Triangle],
        lights: Iterable[_light.Light],
    ) -> numpy.ndarray:
        data = numpy.zeros((canvas_size.height, canvas_size.width, 4), dtype=numpy.uint8)
        raw_triangles = (_bindings.Triangle * len(triangles))(*map(lambda t: t.raw, triangles))
        raw_lights = (_bindings.Light * len(lights))(*map(lambda t: t.raw, lights))

        _bindings.render(
            self._config.raw,
            _bindings.Canvas(
                pixels=data.ctypes.data_as(ctypes.POINTER(_bindings.Color)),
                width=canvas_size.width,
                height=canvas_size.height,
            ),
            raw_triangles,
            len(triangles),
            raw_lights,
            len(lights),
        )

        return data
