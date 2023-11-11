import ctypes
import os

# Paths
# TODO: Make constants configurable or runtime calculatable
CURRENT_PATH = os.path.dirname(__file__)
CPPSTDLIB_PATH = 'C:\\msys64\\ucrt64\\bin\\libstdc++-6.dll'
RENDERER_LIB_PATH = os.path.join(CURRENT_PATH, '.bin/renderer.dll')

# Load libraries
def _load_library():
    try:
        ctypes.cdll.LoadLibrary(CPPSTDLIB_PATH)
    except OSError:
        pass  # stdc++ library could not be loaded, but it might not be necessary
    renderer_lib = ctypes.cdll.LoadLibrary(RENDERER_LIB_PATH)
    return renderer_lib

# Basic types
Color = ctypes.c_uint8 * 4
Vector3 = ctypes.c_float * 3

# Triangle class
class Triangle(ctypes.Structure):
    _fields_ = [
        ('points', Vector3 * 3),
        ('normals', Vector3 * 3),
        ('color', Color),
        ('specular', ctypes.c_float)
    ]

# Light classes and constants
class LightType:
    AMBIENT = 0
    POINT = 1
    DIRECTION = 2

class Light(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_int),
        ('intensity', ctypes.c_float),
        ('position', Vector3)
    ]

# Canvas class
class Canvas(ctypes.Structure):
    _fields_ = [
        ('pixels', ctypes.POINTER(Color)),
        ('width', ctypes.c_int),
        ('height', ctypes.c_int)
    ]

# Render classes and constants
class RenderMode:
    WIREFRAME = 1
    FILL = 2

class ProjectionType:
    ISOMETRIC = 1
    PERSPECTIVE = 2

class Config(ctypes.Structure):
    _fields_ = [
        ('d', ctypes.c_float),
        ('viewSize', ctypes.c_float * 2),
        ('mode', ctypes.c_int),
        ('projection', ctypes.c_int)
    ]

# Library interface
_lib = _load_library()

render = _lib.Render
render.argtypes = [
    Config,
    Canvas,
    ctypes.POINTER(Triangle),
    ctypes.c_size_t,
    ctypes.POINTER(Light),
    ctypes.c_size_t
]
render.restype = None
