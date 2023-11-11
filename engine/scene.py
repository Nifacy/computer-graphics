import copy
from typing import Iterable, NewType
from dataclasses import dataclass
import numpy as np

from . import types
from ._light import Light, AmbientLight, PointLight, DirectionalLight


Mesh = NewType('Mesh', tuple[types.Triangle, ...])


@dataclass
class SceneObject:
    name: str
    rotation: types.Vector3
    position: types.Vector3
    scale: float
    mesh: Mesh


def _translate(scene_object: SceneObject, triangles: Iterable[types.Triangle]) -> Iterable[types.Triangle]:
    for triangle in triangles:
        triangle.points = tuple(point + scene_object.position for point in triangle.points)
        yield triangle


def _scale(scene_object: SceneObject, triangles: Iterable[types.Triangle]) -> Iterable[types.Triangle]:
    for triangle in triangles:
        triangle.points = tuple(point.dot(scene_object.scale) for point in triangle.points)
        yield triangle


# TODO: rewrite using scipy
def _get_matrix(index: int, angle: float) -> np.ndarray:
    samples = [
        [
            [1, 0, 0],
            [0, np.cos(angle), -np.sin(angle)],
            [0, np.sin(angle), np.cos(angle)],
        ],
        [
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ],
        [
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1],
        ],
    ]

    return np.array(samples[index], dtype=np.float16)


def _rotate(scene_object: SceneObject, triangles: Iterable[types.Triangle]) -> Iterable[types.Triangle]:
    for triangle in triangles:
        points = []
        normals = []

        for point, normal in zip(triangle.points, triangle.normals):
            pos = np.array([list(point)], dtype=np.float16)
            n = np.array([list(normal)], dtype=np.float16)

            for i, angle in enumerate(scene_object.rotation):
                rotation_matrix = _get_matrix(i, angle)
                pos = np.matmul(pos, rotation_matrix)
                n = np.matmul(n, rotation_matrix, n)

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
    
    def add_object(self, scene_object: SceneObject | Light) -> None:
        objects_container = self._objects if isinstance(scene_object, SceneObject) else self._lights

        if scene_object not in objects_container:
            objects_container.append(scene_object)


def dump_scene(scene: Scene) -> tuple[tuple[types.Triangle, ...], tuple[Light, ...]]:
    lights = tuple(scene._lights)
    triangles = []

    for scene_object in scene._objects:
        triangles.extend(_dump_scene_object(scene_object))
    
    return tuple(triangles), lights
