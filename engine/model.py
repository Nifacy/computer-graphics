from itertools import starmap

from . import types, scene


def _calculate_normal(edges: tuple[types.Vector3, types.Vector3, types.Vector3]) -> types.Vector3:
    v, w = edges[1] - edges[0], edges[2] - edges[0]
    return v.cross(w).normalize()


def load(filepath: str) -> scene.Mesh:
    materials = dict()
    vertexes = []
    faces = []

    current_material = ''

    with open(filepath, 'r') as file:
        for line in map(str.strip, file):
            if not line:
                continue

            object_type, *data = line.split()

            if object_type == 'v':
                vertexes.append(tuple(map(float, data)))
            
            elif object_type == 'usemtl':
                current_material = data[0]
            
            elif object_type == 'f':
                faces.append((current_material, tuple(map(int, data))))
            
            elif object_type == 'newmtl':
                alias = data[0]
                _, *data = file.readline().strip().split()
                materials[alias] = tuple(map(float, data))

        materials = {alias: types.Color(*map(lambda x: int(x * 255), data[:3]), data[3] if len(data) == 4 else 1.0) for alias, data in materials.items()}

        vertexes = tuple(starmap(types.Vector3, vertexes))
        normal = _calculate_normal(vertexes)
        faces = [
            types.Triangle(
                points=tuple(map(lambda i: vertexes[i - 1 if i >= 0 else i], point_indexes)),
                normals=(normal, normal, normal),
                color=materials.get(material_alias, types.Color(0, 0, 0)),
            )
            for material_alias, point_indexes in faces
        ]
    
    return scene.Mesh(faces)
