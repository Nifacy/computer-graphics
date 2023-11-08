from itertools import starmap
from typing import Iterable, Iterator
from dataclasses import dataclass
import numpy

from . import models


class GameObject:
    def __init__(self, scale: float, rotation: models.Point, position: models.Point, mesh: models.Mesh) -> None:
        self._mesh = mesh
        self.position = position
        self.rotation = rotation
        self.scale = scale

    def _translate(self, triangles: Iterable[models.Triangle]) -> Iterator[models.Triangle]:
        for triangle in triangles:
            yield models.Triangle(
                (
                    triangle.points[0] + self.position,
                    triangle.points[1] + self.position,
                    triangle.points[2] + self.position,
                ),
                triangle.normals,
                triangle.color,
                triangle.specular,
            )

    def _scale(self, triangles: Iterable[models.Triangle]) -> Iterator[models.Triangle]:
        for triangle in triangles:
            yield models.Triangle(
                points=tuple(map(lambda p: p * self.scale, triangle.points)),
                normals=triangle.normals,
                color=triangle.color,
                specular=triangle.specular,
            )

    def _get_matrix(self, index: int, angle: float) -> numpy.ndarray:
        samples = [
            [
                [1, 0, 0],
                [0, numpy.cos(angle), -numpy.sin(angle)],
                [0, numpy.sin(angle), numpy.cos(angle)],
            ],
            [
                [numpy.cos(angle), 0, numpy.sin(angle)],
                [0, 1, 0],
                [-numpy.sin(angle), 0, numpy.cos(angle)],
            ],
            [
                [numpy.cos(angle), -numpy.sin(angle), 0],
                [numpy.sin(angle), numpy.cos(angle), 0],
                [0, 0, 1],
            ],
        ]

        return numpy.array(samples[index], dtype=numpy.float16)


    def _rotate(self, triangles: Iterable[models.Triangle]) -> Iterable[models.Triangle]:
        for triangle in triangles:
            points = []
            normals = []

            for normal, point in zip(triangle.normals, triangle.points):
                pos = numpy.array(point, dtype=numpy.float16)
                n = numpy.array(normal, dtype=numpy.float16)

                for i, angle in enumerate(self.rotation):
                    rotation_matrix = self._get_matrix(i, angle)
                    pos = numpy.matmul(rotation_matrix, pos)
                    n = numpy.matmul(rotation_matrix, n)

                points.append(models.Point(*pos))
                normals.append(models.Point(*n))

            yield models.Triangle(tuple(points), tuple(normals), triangle.color, triangle.specular)

    def mesh(self) -> models.Mesh:
        triangles = iter(self._mesh)
        triangles = self._scale(triangles)
        triangles = self._rotate(triangles)
        triangles = self._translate(triangles)
        return models.Mesh(triangles)


@dataclass
class Light:
    intensity: float


@dataclass
class AmbientLight(Light):
    pass


@dataclass
class PointLight(Light):
    position: models.Point


@dataclass
class DirectionalLight(Light):
    direction: models.Point
