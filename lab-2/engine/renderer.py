from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from . import models


class IViewport(Protocol):
    def put_pixel(self, point: models.Point2D, color: models.Color) -> None:
        ...

    def width(self) -> int:
        ...

    def height(self) -> int:
        ...


class _ViewportWithZBuffer:
    def __init__(self, viewport: IViewport) -> None:
        w, h = viewport.width(), viewport.height()

        self._center = models.Point2D(- w // 2,  - h // 2)
        self._size = (w, h)
        self._zbuffer = [[0.0] * w for _ in range(h)]
        self._viewport = viewport

    def _can_be_changed(self, point: models.Point2D, z: float) -> bool:
        x, y = point.x - self._center.x, point.y - self._center.y

        if x < 0 or y < 0 or self._size[0] <= x or self._size[0] <= y:
            return False
        
        result = z > self._zbuffer[x][y]
        self._zbuffer[x][y] = max(self._zbuffer[x][y], z)
        return result

    def put_pixel(self, point: models.Point2D, z: float, color: models.Color) -> None:
        if self._can_be_changed(point, z):
            self._viewport.put_pixel(point, color)

    def width(self) -> int:
        return self._viewport.width()

    def height(self) -> int:
        return self._viewport.height()


class RenderMode(Enum):
    WIREFRAME = 1
    FILL = 2


class ProjectionType(Enum):
    ISOMETRIC = 1
    PERSPECTIVE = 2


@dataclass
class Config:
    d: float
    view_size: tuple[float, float]
    mode: RenderMode
    projection: ProjectionType


class Renderer:
    def __init__(self, config: Config) -> None:
        self._config = config

    def _mult(self, a: models.Point, b: models.Point) -> models.Point:
        return models.Point(
            a.y * b.z - b.y * a.z,
            a.z * b.x - a.x * b.z,
            a.x * b.y - b.x * a.y,
        )

    def _scalar(self, v: models.Point, w: models.Point) -> float:
        return v.x * w.x + v.y * w.y + v.z * w.z

    def _is_back_facing(self, triangle: models.Triangle) -> bool:
        v = triangle.points[1] - triangle.points[0]
        w = triangle.points[2] - triangle.points[0]
        n = self._mult(v, w)
        h = (triangle.points[0] + triangle.points[1] + triangle.points[2]) * (1 / 3)

        return self._scalar(n, h) < 0

    def _to_canvas_coords(self, canvas_size: tuple[int, int], x: float, y: float) -> models.Point2D:
        p = models.Point2D(
            int(x / self._config.view_size[0] * canvas_size[0]),
            int(y / self._config.view_size[1] * canvas_size[1]),
        )

        return p

    def _project_point_1(self, canvas_size: tuple[int, int], point: models.Point) -> models.Point2D:
        return self._to_canvas_coords(
            canvas_size,
            point.x * self._config.d / point.z,
            point.y * self._config.d / point.z,
        )

    def _project_point_2(self, canvas_size: tuple[int, int], point: models.Point) -> models.Point2D:
        return self._to_canvas_coords(canvas_size, point.x, point.y)

    def _project_point(self, canvas_size: tuple[int, int], point: models.Point) -> models.Point2D:
        if self._config.projection == ProjectionType.ISOMETRIC:
            return self._project_point_2(canvas_size, point)
        return self._project_point_1(canvas_size, point)

    @staticmethod
    def _interpolate(i0: int, d0: int, i1: int, d1: int) -> list[float]:
        if i0 == i1:
            return [d0]

        values = []
        a = (d1 - d0) / (i1 - i0)
        d = d0

        for _ in range(i0, i1 + 1):
            values.append(d)
            d += a

        return values

    def _draw_3d_line(self, viewport: _ViewportWithZBuffer, p0: models.Point, p1: models.Point, color: models.Color) -> None:
        canvas_size = viewport.width(), viewport.height()

        a = self._project_point(canvas_size, p0), p0.z
        b = self._project_point(canvas_size, p1), p1.z

        # if it as a point
        if a[0] == b[0]:
            viewport.put_pixel(a[0], a[1], color)
            return

        # if it is a horizontal line
        if abs(a[0].x - b[0].x) > abs(a[0].y - b[0].y):
            if a[0].x > b[0].x:
                a, b = b, a

            ys = self._interpolate(a[0].x, a[0].y, b[0].x, b[0].y)
            zs = self._interpolate(a[0].x, a[1], b[0].x, b[1])

            for x, y, z in zip(range(a[0].x, b[0].x + 1), ys, zs):
                viewport.put_pixel(models.Point2D(x, int(y)), z, color)

        # if it is a vertical line
        else:
            if a[0].y > b[0].y:
                a, b = b, a

            xs = self._interpolate(a[0].y, a[0].x, b[0].y, b[0].x)
            zs = self._interpolate(a[0].y, a[1], b[0].y, b[1])

            for y, x, z in zip(range(a[0].y, b[0].y + 1), xs, zs):
                viewport.put_pixel(models.Point2D(int(x), y), z, color)

    def _draw_bordered_triangle(self, viewport: _ViewportWithZBuffer, triangle: models.Triangle) -> None:
        a, b, c = triangle.points
        self._draw_3d_line(viewport, a, b, triangle.color)
        self._draw_3d_line(viewport, b, c, triangle.color)
        self._draw_3d_line(viewport, c, a, triangle.color)

    def _draw_3d_triangle(self, viewport: _ViewportWithZBuffer, triangle: models.Triangle) -> None:
        if self._is_back_facing(triangle):
            return

        canvas_size = viewport.width(), viewport.height()
        projected_points = map(lambda p: (self._project_point(canvas_size, p), p.z), triangle.points)
        [p0, z0], [p1, z1], [p2, z2] = sorted(projected_points, key=lambda p: p[0].y)

        x02 = self._interpolate(p0.y, p0.x, p2.y, p2.x)
        x01 = self._interpolate(p0.y, p0.x, p1.y, p1.x)
        x12 = self._interpolate(p1.y, p1.x, p2.y, p2.x)
        x01.pop()
        x012 = x01 + x12

        z02 = self._interpolate(p0.y, 1 / z0, p2.y, 1 / z2)
        z01 = self._interpolate(p0.y, 1 / z0, p1.y, 1 / z1)
        z12 = self._interpolate(p1.y, 1 / z1, p2.y,  1 / z2)
        z01.pop()

        z012 = z01 + z12

        for y, x1, x2, z1, z2 in zip(range(p0.y, p2.y + 1), x02, x012, z02, z012):
            x_left, x_right = map(int, sorted((x1, x2)))
            zs = self._interpolate(x_left, z1, x_right, z2)

            for x, z in zip(range(x_left, x_right + 1), zs):
                viewport.put_pixel(models.Point2D(x, y), z, triangle.color)

    def render(self, viewport: IViewport, triangles: list[models.Triangle]) -> None:
        _viewport = _ViewportWithZBuffer(viewport)

        for triangle in triangles:
            if self._config.mode == RenderMode.WIREFRAME:
                self._draw_bordered_triangle(_viewport, triangle)
            else:
                self._draw_3d_triangle(_viewport, triangle)
