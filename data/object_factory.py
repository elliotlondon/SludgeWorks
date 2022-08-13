import json

from parts.entity import StaticObject


def create_static_object_from_json(path: str, request: str) -> StaticObject:
    f = open(path, 'r', encoding='utf-8')
    object_dict = json.load(f)

    for i in range(len(object_dict)):
        if request in object_dict[i]:
            data = object_dict[i][request]
            static_object = create_static_object(data)
            return static_object


def create_static_object(data) -> StaticObject:
    if 'properties' in data:
        properties = data['properties']
    else:
        properties = []
    static_object = StaticObject(
        char=data['char'],
        colour=(data['colour'][0], data['colour'][1], data['colour'][2]),
        name=data['name'],
        interact_message=data['interact_message'],
        description=data['description'],
        properties=properties
    )
    return static_object
