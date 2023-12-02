import copy
import itertools
from typing import Iterable, NewType
from dataclasses import dataclass
import numpy

from . import types, _light


Mesh = NewType('Mesh', tuple[types.Triangle, ...])


@dataclass
class ObjectBase:
    name: str


@dataclass
class SceneObject(ObjectBase):
    rotation: types.Vector3
    position: types.Vector3
    scale: types.Vector3
    mesh: Mesh


@dataclass
class Light(ObjectBase):
    intensity: float


@dataclass
class AmbientLight(Light):
    pass


@dataclass
class PointLight(Light):
    position: types.Vector3


@dataclass
class DirectionalLight(Light):
    direction: types.Vector3


def _translate(scene_object: SceneObject, triangles: Iterable[types.Triangle]) -> Iterable[types.Triangle]:
    for triangle in triangles:
        triangle.points = tuple(point + scene_object.position for point in triangle.points)
        yield triangle


def _scale(scene_object: SceneObject, triangles: Iterable[types.Triangle]) -> Iterable[types.Triangle]:
    for triangle in triangles:
        triangle.points = tuple(point.dot(scene_object.scale) for point in triangle.points)
        yield triangle


# TODO: rewrite using scipy
def _get_matrix(index: int, angle: float) -> numpy.ndarray:
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


def _rotate(scene_object: SceneObject, triangles: Iterable[types.Triangle]) -> Iterable[types.Triangle]:
    for triangle in triangles:
        points = []
        normals = []

        for point, normal in zip(triangle.points, triangle.normals):
            pos = numpy.array([list(point)], dtype=numpy.float16)
            n = numpy.array([list(normal)], dtype=numpy.float16)

            for i, angle in enumerate(scene_object.rotation):
                rotation_matrix = _get_matrix(i, angle)
                pos = numpy.matmul(pos, rotation_matrix)
                n = numpy.matmul(n, rotation_matrix, n)

            points.append(types.Vector3(*pos[0]))
            normals.append(types.Vector3(*n[0]))

        yield types.Triangle(tuple(points), tuple(normals), triangle.color, triangle.specular)


def _dump_scene_object(scene_object: SceneObject) -> Iterable[types.Triangle]:
    triangles = iter(copy.deepcopy(scene_object.mesh))

    triangles = _scale(scene_object, triangles)
    triangles = _rotate(scene_object, triangles)
    triangles = _translate(scene_object, triangles)

    return triangles


class Scene:
    def __init__(self):
        self._objects = []
        self._lights = []

    def add_object(self, scene_object: ObjectBase) -> None:
        objects_container = self._objects if isinstance(scene_object, SceneObject) else self._lights

        if scene_object not in objects_container:
            objects_container.append(scene_object)

    def get_by_name(self, name: str) -> ObjectBase | None:
        for obj in itertools.chain(self._objects, self._lights):
            if obj.name == name:
                return obj
        return None


def _dump_triangles(triangles: Iterable[types.Triangle]) -> numpy.ndarray:
    dumped_triangles = []

    for triangle in triangles:
        color = [triangle.color.r / 255, triangle.color.g / 255, triangle.color.b / 255, triangle.color.a]

        for point, normal in zip(triangle.points, triangle.normals):
            point = list(point)
            normal = list(normal)
            dumped_triangles.append([*point, *normal, *color, 0.0, triangle.specular])

    return numpy.concatenate(dumped_triangles, axis=0).astype('f4')


def dump_scene(scene: Scene) -> tuple[numpy.ndarray, tuple[Light, ...]]:
    lights = []
    triangles = []

    for scene_object in scene._objects:
        triangles.extend(_dump_scene_object(scene_object))
    
    for light_object in scene._lights:
        if isinstance(light_object, AmbientLight):
            lights.append(_light.AmbientLight(light_object.intensity))
        elif isinstance(light_object, PointLight):
            lights.append(_light.PointLight(light_object.intensity, light_object.position))
        elif isinstance(light_object, DirectionalLight):
            lights.append(_light.DirectionalLight(light_object.intensity, light_object.direction))
    
    return _dump_triangles(triangles), tuple(lights)
