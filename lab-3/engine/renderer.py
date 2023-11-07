from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Protocol
import subprocess as sp

import numpy

from . import models, scene


CURRENT_DIRECTORY_PATH = Path('.').absolute()
CURRENT_FILE_PATH = Path(__file__).parent.absolute().relative_to(CURRENT_DIRECTORY_PATH)
SOURCE_FILE_PATH = CURRENT_FILE_PATH / Path('.cpp/renderer.cpp')
BINARIES_PATH = CURRENT_FILE_PATH / Path('.bin/renderer')


class IViewport(Protocol):
    def update(self, data: numpy.ndarray) -> None:
        ...

    def width(self) -> int:
        ...

    def height(self) -> int:
        ...


class RenderMode(Enum):
    WIREFRAME = 'wireframe'
    FILL = 'fill'


class ProjectionType(Enum):
    ISOMETRIC = 'isometric'
    PERSPECTIVE = 'perspective'


@dataclass
class Config:
    d: float
    view_size: tuple[float, float]
    mode: RenderMode
    projection: ProjectionType


def _build_renderer():
    BINARIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = sp.run(['g++', str(SOURCE_FILE_PATH), '-o', str(BINARIES_PATH)], stdin=sp.PIPE, stdout=sp.PIPE)
    result.check_returncode()


def _run_renderer():
    return sp.Popen([str(BINARIES_PATH)], stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)


class Renderer:
    def __init__(self, config: Config) -> None:
        self._config = config

        _build_renderer()
        self._process = _run_renderer()

    def _serialize_config(self) -> str:
        return '{d} {view_width} {view_height} {render_mode} {projection_type}'.format(
            d=self._config.d,
            view_width=self._config.view_size[0],
            view_height=self._config.view_size[1],
            render_mode=self._config.mode.value,
            projection_type=self._config.projection.value,
        )

    @classmethod
    def _serialize_triangle(cls, triangle: models.Triangle) -> str:
        data = ''

        for point in triangle.points:
            data += f'{point.x} {point.y} {point.z}\n'

        data += f'{triangle.color.r} {triangle.color.g} {triangle.color.b}'
        return data

    @classmethod
    def _serialize_canvas_size(cls, canvas_size: tuple[int, int]) -> str:
        return ' '.join(map(str, canvas_size))

    @classmethod
    def _serialize_triangles(cls, triangles: Iterable[models.Triangle]) -> str:
        data = ''
        amount = 0

        for triangle in triangles:
            amount += 1
            data += cls._serialize_triangle(triangle) + '\n\n'

        return f'{amount}\n{data}'

    @classmethod
    def _serialize_light(cls, light: scene.Light) -> str:
        if isinstance(light, scene.AmbientLight):
            return f'ambient\n{light.intensity}'

        if isinstance(light, scene.PointLight):
            return f'point\n{light.intensity}\n{light.position.x} {light.position.y} {light.position.z}'

        if isinstance(light, scene.DirectionalLight):
            return f'directional\n{light.intensity}\n{light.direction.x} {light.direction.y} {light.direction.z}'

    @classmethod
    def _serialize_lights(cls, lights: Iterable[scene.Light]) -> str:
        data = ''
        amount = 0

        for light in lights:
            amount += 1
            data += cls._serialize_light(light) + '\n\n'

        return f'{amount}\n{data}'

    def render(
            self,
            viewport: IViewport,
            triangles: list[models.Triangle],
            lights: Iterable[scene.Light]) -> None:
        canvas_size = (viewport.width(), viewport.height())
        
        data = '{config}\n{canvas_size}\n{lights}\n{triangles}'.format(
            config=self._serialize_config(),
            canvas_size=self._serialize_canvas_size(canvas_size),
            lights=self._serialize_lights(lights),
            triangles=self._serialize_triangles(triangles),
        )

        self._process.stdin.write(data.encode())
        self._process.stdin.flush()

        output = self._process.stdout.readline().strip()
        pixels = numpy.frombuffer(output, dtype=numpy.uint8).reshape((*canvas_size[::-1], 4))
        viewport.update(pixels)

    def __del__(self) -> None:
        if hasattr(self, '_process'):
            self._process.terminate()
            self._process.wait()
