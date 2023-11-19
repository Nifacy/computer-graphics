from pathlib import Path
import moderngl
from functools import cache


_CURDIR_PATH = Path(__file__).parent.absolute()
_SHADERS_STORAGE_PATH = _CURDIR_PATH / Path('shaders')


class ShaderNotFound(Exception):
    __tmp: str = "Can't load shader {name!r}, because it doesn't exist"

    def __init__(self, shader_name: str) -> None:
        self.shader_name = shader_name
        super().__init__(self.__tmp.format(name=shader_name))


@cache
def create_context() -> moderngl.Context:
    return moderngl.create_standalone_context()


def load_shader(shader_name: str) -> moderngl.Program:
    shader_path = _SHADERS_STORAGE_PATH / Path(shader_name)
    vertex_shader_path = _SHADERS_STORAGE_PATH / Path(f'{shader_name}/vertex.glsl')
    fragment_shader_path = _SHADERS_STORAGE_PATH / Path(f'{shader_name}/fragment.glsl')

    if not shader_path.exists():
        raise ShaderNotFound(shader_name)
    
    shaders_data = {}

    if vertex_shader_path.exists():
        with vertex_shader_path.open('r', encoding='utf-8') as shader_file:
            shaders_data['vertex_shader'] = shader_file.read()

    if fragment_shader_path.exists():
        with fragment_shader_path.open('r', encoding='utf-8') as shader_file:
            shaders_data['fragment_shader'] = shader_file.read()
    
    return create_context().program(**shaders_data)
