from itertools import starmap
from engine import types, scene
import numpy


def cylinder(r: float, h: float, n: int, color: types.Color, specular: float) -> scene.Mesh:
    angles = numpy.linspace(0, 2 * numpy.pi, n)
    xs = r * numpy.cos(angles)
    ys = r * numpy.sin(angles)

    middle_points = numpy.array([xs, ys, numpy.zeros((n,))]).transpose()
    top_points = middle_points + numpy.array([[0, 0, h / 2]])
    bottom_points = middle_points - numpy.array([[0, 0, h / 2]])

    top_points = tuple(starmap(types.Vector3, top_points))
    middle_points = tuple(starmap(types.Vector3, middle_points))
    bottom_points = tuple(starmap(types.Vector3, bottom_points))

    triangles = []

    for i in range(1, len(top_points) - 1):
        triangles.append(types.Triangle(
            points=(top_points[i], top_points[0], top_points[i + 1]),
            normals=(top_points[i], top_points[0], top_points[i + 1]),
            color=color,
            specular=specular,
        ))

    for i in range(1, len(bottom_points) - 1):
        triangles.append(types.Triangle(
            points=(bottom_points[0], bottom_points[i], bottom_points[i + 1]),
            normals=(bottom_points[0], bottom_points[i], bottom_points[i + 1]),
            color=color,
            specular=specular,
        ))

    for i in range(len(top_points) - 1):
        triangles.append(types.Triangle(
            points=(bottom_points[i], top_points[i], top_points[i + 1]),
            normals=(bottom_points[i], top_points[i], top_points[i + 1]),
            color=color,
            specular=specular,
        ))

        triangles.append(types.Triangle(
            points=(bottom_points[i + 1], bottom_points[i], top_points[i + 1]),
            normals=(bottom_points[i + 1], bottom_points[i], top_points[i + 1]),
            color=color,
            specular=specular,
        ))

    return scene.Mesh(triangles)
