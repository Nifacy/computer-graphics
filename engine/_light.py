from dataclasses import dataclass
from . import _bindings, types

@dataclass
class Light:
    intensity: float

    @property
    def raw(self) -> _bindings.Light:
        raise NotImplementedError


@dataclass
class AmbientLight(Light):
    @property
    def raw(self) -> _bindings.Light:
        return _bindings.Light(
            type=_bindings.LightType.AMBIENT,
            intensity=self.intensity,
            position=_bindings.Vector3(0.0, 0.0, 0.0),
        )


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
