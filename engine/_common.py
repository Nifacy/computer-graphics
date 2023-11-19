import moderngl
from functools import cache


@cache
def create_context() -> moderngl.Context:
    return moderngl.create_standalone_context()
