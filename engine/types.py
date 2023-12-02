from dataclasses import dataclass
from math import sqrt
from typing import Iterator


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

    def dot(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.x * other.x,
            self.y * other.y,
            self.z * other.z,
        )

    def cross(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    @property
    def length(self) -> float:
        return sqrt(sum(coord ** 2 for coord in self))

    def normalize(self) -> 'Vector3':
        return self * (1 / self.length)

    def __iter__(self) -> Iterator[float]:
        return iter([self.x, self.y, self.z])


@dataclass
class Color:
    r: int
    g: int
    b: int
    a: float = 1.0


@dataclass
class Triangle:
    points: tuple[Vector3, Vector3, Vector3]
    normals: tuple[Vector3, Vector3, Vector3]
    color: Color
    specular: float = 0.0
