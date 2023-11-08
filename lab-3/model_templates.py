from engine import models
import numpy


def cylinder(r: float, h: float, n: int, color: models.Color, specular: float) -> list[models.Triangle]:
    angles = numpy.linspace(0, 2 * numpy.pi, n)
    xs = r * numpy.cos(angles)
    ys = r * numpy.sin(angles)

    middle_points = numpy.array([xs, ys, numpy.zeros((n,))]).transpose()
    top_points = middle_points + numpy.array([[0, 0, h / 2]])
    bottom_points = middle_points - numpy.array([[0, 0, h / 2]])

    triangles = []

    for i in range(1, len(top_points) - 1):
        triangles.append(models.Triangle(
            points=(top_points[i], top_points[0], top_points[i + 1]),
            normals=(top_points[i], top_points[0], top_points[i + 1]),
            color=color,
            specular=specular,
        ))

    for i in range(1, len(bottom_points) - 1):
        triangles.append(models.Triangle(
            points=(bottom_points[0], bottom_points[i], bottom_points[i + 1]),
            normals=(bottom_points[0], bottom_points[i], bottom_points[i + 1]),
            color=color,
            specular=specular,
        ))

    for i in range(len(top_points) - 1):
        triangles.append(models.Triangle(
            points=(bottom_points[i], top_points[i], top_points[i + 1]),
            normals=(bottom_points[i], top_points[i], top_points[i + 1]),
            color=color,
            specular=specular,
        ))

        triangles.append(models.Triangle(
            points=(bottom_points[i + 1], bottom_points[i], top_points[i + 1]),
            normals=(bottom_points[i + 1], bottom_points[i], top_points[i + 1]),
            color=color,
            specular=specular,
        ))

    return triangles
