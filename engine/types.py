from dataclasses import dataclass
from . import _bindings


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def __mul__(self, coef: float) -> 'Vector3':
        return Vector3(
            self.x * coef,
            self.y * coef,
            self.z * coef,
        )

    @property
    def raw(self) -> _bindings.Vector3:
        return _bindings.Vector3(self.x, self.y, self.z)


@dataclass
class Color:
    r: int
    g: int
    b: int
    a: int = 255

    @property
    def raw(self) -> _bindings.Color:
        return _bindings.Color(self.r, self.g, self.b, self.a)


@dataclass
class Triangle:
    points: tuple[Vector3, Vector3, Vector3]
    normals: tuple[Vector3, Vector3, Vector3]
    color: Color
    specular: float = 0.0

    @property
    def raw(self) -> _bindings.Triangle:
        return _bindings.Triangle(
            points=tuple(p.raw for p in self.points),
            normals=tuple(n.raw for n in self.normals),
            color=self.color.raw,
            specular=self.specular,
        )
