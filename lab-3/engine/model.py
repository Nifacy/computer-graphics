from itertools import starmap
from engine import models


def load(filepath: str) -> models.Mesh:
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


        materials = {alias: models.Color(*map(lambda x: int(x * 255), data)) for alias, data in materials.items()}
        vertexes = tuple(starmap(models.Point, vertexes))
        faces = [
            models.Triangle(
                points=tuple(map(lambda i: vertexes[i - 1 if i >= 0 else i], point_indexes)),
                color=materials.get(material_alias, models.Color(0, 0, 0)),
            )
            for material_alias, point_indexes in faces
        ]
    
    return models.Mesh(faces)
