from dataclasses import dataclass
from enum import Enum
from typing import Iterable

import moderngl
from OpenGL import GL
import numpy

from . import types, _light, _common

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


class Renderer:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._context = _common.create_context()
        self._shader = self._context.program(**_common.load_shader('render'))

    @staticmethod
    def _dump_triangles(triangles: Iterable[types.Triangle]) -> numpy.ndarray:
        dumped_triangles = []

        for triangle in triangles:
            color = [triangle.color.r / 255, triangle.color.g / 255, triangle.color.b / 255]

            for point, normal in zip(triangle.points, triangle.normals):
                point = list(point)
                normal = list(normal)
                dumped_triangles.append([*point, *normal, *color, 0.0, triangle.specular])

        return numpy.concatenate(dumped_triangles, axis=0).astype('f4')

    def render(
        self,
        canvas_size: CanvasSize,
        triangles: list[types.Triangle],
        lights: Iterable[_light.Light],
    ) -> numpy.ndarray:
        _cnv = (canvas_size.width, canvas_size.height)

        frame_buffer = self._context.framebuffer(
            color_attachments=self._context.texture(_cnv, 4),
            depth_attachment=self._context.depth_renderbuffer(_cnv),
        )

        vertex_buffer = self._context.buffer(self._dump_triangles(triangles))
        template_buffer = self._context.buffer(reserve=vertex_buffer.size)

        for light in lights:
            light.transform(vertex_buffer, template_buffer)
            vertex_buffer, template_buffer = template_buffer, vertex_buffer

        frame_buffer.use()
        frame_buffer.clear(1.0, 1.0, 1.0, 1.0)

        self._shader['viewSize'] = self._config.view_size
        vertex_array = self._context.simple_vertex_array(
            self._shader, vertex_buffer,
            'in_vert', 'in_normal', 'in_color', 'in_intensity', 'in_specular',
        )

        if self._config.mode == RenderMode.WIREFRAME:
            self._context.wireframe = True
        GL.glEnable(GL.GL_DEPTH_TEST)
        vertex_array.render(moderngl.TRIANGLES)
        if self._config.mode == RenderMode.WIREFRAME:
            self._context.wireframe = False

        return numpy.frombuffer(frame_buffer.read(), dtype=numpy.uint8)
