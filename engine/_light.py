from dataclasses import dataclass

import moderngl
from . import _common, types

_context = _common.create_context()


@dataclass
class Light:
    intensity: float


@dataclass
class AmbientLight(Light):
    _program: moderngl.Program = _context.program(
        **_common.load_shader('ambient_light'),
        varyings=['out_vert', 'out_normal', 'out_color', 'out_intensity', 'out_specular'],
    )

    def transform(self, in_buffer: moderngl.Buffer, out_buffer: moderngl.Buffer) -> None:
        self._program['intensity'] = self.intensity
        arr = _context.vertex_array(
            self._program, in_buffer,
            'in_vert', 'in_normal', 'in_color', 'in_intensity', 'in_specular',
        )
        arr.transform(out_buffer)


@dataclass
class PointLight(Light):
    position: types.Vector3
    _program: moderngl.Program = _context.program(
        **_common.load_shader('point_light'),
        varyings=['out_vert', 'out_normal', 'out_color', 'out_intensity', 'out_specular'],
    )

    def transform(self, in_buffer: moderngl.Buffer, out_buffer: moderngl.Buffer) -> None:
        self._program['intensity'] = self.intensity
        self._program['position'] = tuple(self.position)
        arr = _context.vertex_array(
            self._program, in_buffer,
            'in_vert', 'in_normal', 'in_color', 'in_intensity', 'in_specular',
        )
        arr.transform(out_buffer)


@dataclass
class DirectionalLight(Light):
    direction: types.Vector3
    _program: moderngl.Program = _context.program(
        **_common.load_shader('direction_light'),
        varyings=['out_vert', 'out_normal', 'out_color', 'out_intensity', 'out_specular'],
    )

    def transform(self, in_buffer: moderngl.Buffer, out_buffer: moderngl.Buffer) -> None:
        self._program['intensity'] = self.intensity
        self._program['direction'] = tuple(self.direction)
        arr = _context.vertex_array(
            self._program, in_buffer,
            'in_vert', 'in_normal', 'in_color', 'in_intensity', 'in_specular',
        )
        arr.transform(out_buffer)
