import moderngl
from collections import namedtuple
import numpy as np
from PIL import Image

# Определение структуры Point
Point = namedtuple('Point', ['x', 'y'])

def draw_triangle(triangle: tuple[Point, Point, Point], canvas_size: tuple[int, int]) -> np.ndarray:
    ctx = moderngl.create_standalone_context()

    vertices = np.array([
        triangle[0].x, triangle[0].y, 
        triangle[1].x, triangle[1].y, 
        triangle[2].x, triangle[2].y
    ], dtype='f4')

    vbo = ctx.buffer(vertices)
    prog = ctx.program(
        vertex_shader='''
            #version 330
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
        ''',
        fragment_shader='''
            #version 330
            out vec4 color;
            void main() {
                color = vec4(1.0, 0.0, 0.0, 1.0);  // Красный цвет
            }
        ''',
    )

    frame_buffer = ctx.simple_framebuffer(canvas_size)

    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert')
    frame_buffer.use()
    frame_buffer.clear(0.0, 0.0, 0.0, 1.0)
    vao.render(moderngl.TRIANGLES)

    data = np.frombuffer(frame_buffer.read(), dtype=np.uint8)
    image = np.reshape(data, (canvas_size[1], canvas_size[0], 3))
    return image


triangle = (
    Point(-0.5, -0.5),
    Point(0.0, 0.5),
    Point(0.5, -0.5),
)

data = draw_triangle(triangle, (400, 400))
image = Image.fromarray(data, 'RGB')
image.show()
