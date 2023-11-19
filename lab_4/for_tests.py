import itertools
from typing import Iterable
import moderngl
from collections import namedtuple
import numpy as np
from PIL import Image
from OpenGL import GL

# Определение структуры ColoredPoint и ColoredTriangle
ColoredPoint = namedtuple('ColoredPoint', ['x', 'y', 'z', 'r', 'g', 'b'])
ColoredTriangle = tuple[ColoredPoint, ColoredPoint, ColoredPoint]

def dump_colored_triangles(triangles: Iterable[ColoredTriangle]) -> np.array:
    return np.concatenate(triangles, axis=0).astype('f4')

def draw_colored_triangle(triangles: Iterable[ColoredTriangle], canvas_size: tuple[int, int]) -> np.ndarray:
    ctx = moderngl.create_standalone_context()

    prog = ctx.program(
        vertex_shader='''
            #version 330

            in vec3 in_vert;
            in vec3 in_color;
            out vec3 frag_vert;
            out vec3 frag_color;

            void main() {
                frag_vert = in_vert;
                frag_color = in_color;
                gl_Position = vec4(in_vert.x / in_vert.z, in_vert.y / in_vert.z, in_vert.z, 1.0);
            }
        ''',
        fragment_shader='''
            #version 330
            in vec3 frag_vert;
            in vec3 frag_color;
            out vec4 color;
            void main() {
                color = vec4(frag_color, 1.0); 
            }
        ''',
    )

    vbo = ctx.buffer(dump_colored_triangles(triangles))
    frame_buffer = ctx.framebuffer(
        color_attachments=ctx.texture(canvas_size, 4),
        depth_attachment=ctx.depth_renderbuffer(canvas_size),    
    )

    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert', 'in_color')
    frame_buffer.use()
    frame_buffer.clear(1.0, 1.0, 1.0, 0.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    vao.render(moderngl.TRIANGLES)

    data = np.frombuffer(frame_buffer.read(), dtype=np.uint8)
    image = np.reshape(data, (canvas_size[1], canvas_size[0], 3))
    return image


triangles = [
    (ColoredPoint(-0.1, -0.2, 0.5, 1.0, 0.0, 0.0), ColoredPoint(0.1, 0.2, 0.5, 1.0, 0.0, 0.0), ColoredPoint(0.3, -0.2, 0.5, 1.0, 0.0, 0.0)),
    (ColoredPoint(0.0, -0.2, 0.3, 0.0, 1.0, 0.0), ColoredPoint(0.1, 0.2, 0.55, 0.0, 1.0, 0.0), ColoredPoint(0.3, -0.2, 0.55, 0.0, 1.0, 0.0)),
]

data = draw_colored_triangle(triangles, (400, 400))
image = Image.fromarray(data, 'RGB')
image.show()
