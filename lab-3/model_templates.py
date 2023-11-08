from engine import models
import numpy


def create_grid(w: float, h: float, step: float) -> list[models.Triangle]:
    dots = []
    triangles = []

    green = models.Color(0, 255, 0)
    specular = 80.0

    for y in numpy.arange(-h/2, h/2 + step, step):
        row = []

        for x in numpy.arange(-w / 2, w / 2 + step, step):
            row.append(models.Point(x, y, 0.0))
        
        dots.append(row)
    
    for j in range(len(dots) - 1):
        for i in range(len(dots[j]) - 1):
            triangles.append(models.Triangle(
                points=(
                    dots[j][i],
                    dots[j][i + 1],
                    dots[j + 1][i],
                ),
                color=green,
                specular=specular,
            ))

            triangles.append(models.Triangle(
                points=(
                    dots[j + 1][i],
                    dots[j][i + 1],
                    dots[j + 1][i + 1],
                ),
                color=green,
                specular=specular,
            ))
    
    return triangles
