from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple, Protocol


class Point(NamedTuple):
    x: float
    y: float
    z: float


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


class IViewport(Protocol):
    def put_pixel(self, point: Point2D, color: Color) -> None:
        ...

    def width(self) -> int:
        ...

    def height(self) -> int:
        ...


class _ViewportWithZBuffer:
    def __init__(self, viewport: IViewport) -> None:
        w, h = viewport.width(), viewport.height()

        self._center = Point2D(- w // 2,  - h // 2)
        self._size = (w, h)
        self._zbuffer = [[0.0] * w for _ in range(h)]
        self._viewport = viewport

    def _can_be_changed(self, point: Point2D, z: float) -> bool:
        x, y = point.x - self._center.x, point.y - self._center.y

        if x < 0 or y < 0 or self._size[0] <= x or self._size[0] <= y:
            return False
        
        return z > self._zbuffer[x][y]

    def put_pixel(self, point: Point2D, z: float, color: Color) -> None:
        if self._can_be_changed(point, z):
            self._viewport.put_pixel(point, color)

    def width(self) -> int:
        return self._viewport.width()

    def height(self) -> int:
        return self._viewport.height()


class RenderMode(Enum):
    WIREFRAME = 1
    FILL = 2


@dataclass
class Config:
    d: float
    view_size: tuple[float, float]
    mode: RenderMode


class Renderer:
    def __init__(self, config: Config) -> None:
        self._config = config

    def _to_canvas_coords(self, canvas_size: tuple[int, int], x: float, y: float) -> Point2D:
        p = Point2D(
            int(x / self._config.view_size[0] * canvas_size[0]),
            int(y / self._config.view_size[1] * canvas_size[1]),
        )

        return p

    def _project_point(self, canvas_size: tuple[int, int], point: Point) -> Point2D:
        return self._to_canvas_coords(
            canvas_size,
            point.x * self._config.d / point.z,
            point.y * self._config.d / point.z,
        )

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

    def _draw_3d_line(self, viewport: _ViewportWithZBuffer, p0: Point, p1: Point, color: Color) -> None:
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
                viewport.put_pixel(Point2D(x, int(y)), z, color)

        # if it is a vertical line
        else:
            if a[0].y > b[0].y:
                a, b = b, a

            xs = self._interpolate(a[0].y, a[0].x, b[0].y, b[0].x)
            zs = self._interpolate(a[0].y, a[1], b[0].y, b[1])

            for y, x, z in zip(range(a[0].y, b[0].y + 1), xs, zs):
                viewport.put_pixel(Point2D(int(x), y), z, color)

    def _draw_bordered_triangle(self, viewport: _ViewportWithZBuffer, triangle: Triangle) -> None:
        a, b, c = triangle.points
        self._draw_3d_line(viewport, a, b, triangle.color)
        self._draw_3d_line(viewport, b, c, triangle.color)
        self._draw_3d_line(viewport, c, a, triangle.color)

    def _draw_3d_triangle(self, viewport: _ViewportWithZBuffer, triangle: Triangle) -> None:
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
                viewport.put_pixel(Point2D(x, y), z, triangle.color)

    def render(self, viewport: IViewport, triangles: list[Triangle]) -> None:
        _viewport = _ViewportWithZBuffer(viewport)

        for triangle in triangles:
            if self._config.mode == RenderMode.WIREFRAME:
                self._draw_bordered_triangle(_viewport, triangle)
            else:
                self._draw_3d_triangle(_viewport, triangle)
