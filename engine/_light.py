from dataclasses import dataclass

import moderngl
from . import _bindings, _common, types

_context = _common.create_context()

@dataclass
class Light:
    intensity: float

    @property
    def raw(self) -> _bindings.Light:
        raise NotImplementedError


@dataclass
class AmbientLight(Light):
    _program: moderngl.Program = _context.program(
        **_common.load_shader('ambient_light'),
        varyings=['out_vert', 'out_normal', 'out_color', 'out_intensity', 'out_specular'],
    )

    @property
    def raw(self) -> _bindings.Light:
        return _bindings.Light(
            type=_bindings.LightType.AMBIENT,
            intensity=self.intensity,
            position=_bindings.Vector3(0.0, 0.0, 0.0),
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

    @property
    def raw(self) -> _bindings.Light:
        return _bindings.Light(
            type=_bindings.LightType.POINT,
            intensity=self.intensity,
            position=self.position.raw,
        )


@dataclass
class DirectionalLight(Light):
    direction: types.Vector3

    @property
    def raw(self) -> _bindings.Light:
        return _bindings.Light(
            type=_bindings.LightType.DIRECTION,
            intensity=self.intensity,
            position=self.direction.raw,
        )
