from dataclasses import dataclass
from enum import Enum
from typing import Iterable

import moderngl
from OpenGL import GL
import numpy

from . import types, _light, _bindings, _common

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
        self._context = _common.create_context()
        self._shader = self._context.program(
            vertex_shader='''
                #version 330

                uniform vec2 viewSize;

                in vec3 in_vert;
                in vec3 in_color;

                out vec3 frag_color;

                void main() {
                    vec3 v = in_vert;
                    v = vec3(v.x / v.z, -v.y / v.z, v.z / 100.0); // project point on view

                    // fit point coordinates to viewSize
                    if (viewSize.y < 1.0) {
                        v = vec3(v.x * viewSize.y, v.y, v.z);
                    } else {
                        v = vec3(v.x, v.y / viewSize.y, v.z);
                    }

                    gl_Position = vec4(v, 1.0);
                    frag_color = in_color;
                }
            ''',
            fragment_shader='''
                #version 330

                in vec3 frag_color;

                out vec4 color;
                
                void main() {
                    color = vec4(frag_color, 1.0); // convert to RGBA format
                }
            ''',
        )

    @staticmethod
    def _dump_triangles(triangles: Iterable[types.Triangle]) -> numpy.ndarray:
        dumped_triangles = []

        for triangle in triangles:
            color = [triangle.color.r / 255, triangle.color.g / 255, triangle.color.b / 255]

            for point in triangle.points:
                dumped_triangles.append(list(point))
                dumped_triangles.append(color)

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
        vertex_array = self._context.simple_vertex_array(self._shader, vertex_buffer, 'in_vert', 'in_color')

        frame_buffer.use()
        frame_buffer.clear(1.0, 1.0, 1.0, 1.0)

        self._shader['viewSize'] = self._config.view_size

        if self._config.mode == RenderMode.WIREFRAME:
            self._context.wireframe = True
        GL.glEnable(GL.GL_DEPTH_TEST)
        vertex_array.render(moderngl.TRIANGLES)
        if self._config.mode == RenderMode.WIREFRAME:
            self._context.wireframe = False

        return numpy.frombuffer(frame_buffer.read(), dtype=numpy.uint8)
