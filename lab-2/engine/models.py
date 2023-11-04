from typing import NamedTuple, NewType


class Point(NamedTuple):
    x: float
    y: float
    z: float

    def __add__(self, other: 'Point') -> 'Point':
        return Point(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def __sub__(self, other: 'Point') -> 'Point':
        return Point(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def __mul__(self, coef: float) -> 'Point':
        return Point(
            self.x * coef,
            self.y * coef,
            self.z * coef,
        )


class Point2D(NamedTuple):
    x: int
    y: int


class Color(NamedTuple):
    r: int
    g: int
    b: int


class Triangle(NamedTuple):
    points: tuple[Point, Point, Point]
    color: Color


Mesh = NewType('Mesh', tuple[Triangle, ...])
