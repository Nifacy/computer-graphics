import numpy

from . import scene
from ._renderer import Config, CanvasSize, Renderer, RenderMode, ProjectionType


class Engine:
    def __init__(self, render_config: Config):
        self._render_config = render_config
        self._renderer = Renderer(render_config)
    
    def render(self, canvas_size: CanvasSize, s: scene.Scene) -> numpy.ndarray:
        triangles, lights = scene.dump_scene(s)
        rendered_data = self._renderer.render(canvas_size, triangles, lights)
        return rendered_data

    @property
    def render_config(self) -> Config:
        return self._render_config
