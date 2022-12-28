import json
from typing import List

import parts.ai
import parts.mutations
from parts.entity import Actor, Corpse
from parts.equipment import Equipment
from parts.fighter import Fighter
from parts.inventory import Inventory
from parts.level import Level


def create_monster_from_json(path: str, request: str) -> Actor:
    f = open(path, encoding='utf-8')
    monster_dict = json.load(f)

    if request in monster_dict:
        data = monster_dict[request]
        monster = create_monster(data)
        return monster

def create_all_monsters_from_json(path: str) -> List[Actor]:
    f = open(path, encoding='utf-8')
    monster_dict = json.load(f)

    monsters = []
    for i in range(len(monster_dict)):
        name = list(monster_dict.keys())[i]
        data = monster_dict[name]
        monster = create_monster(data)
        monsters.append(monster)
    return monsters


def create_monster(data: dict) -> Actor:
    # Unpack non-json values
    if data['ai_cls'] == "HostileEnemy":
        ai_cls = parts.ai.HostileEnemy
    elif data['ai_cls'] == "NPC":
        ai_cls = parts.ai.NPC
    elif data['ai_cls'] == "HostileStationary":
        ai_cls = parts.ai.HostileStationary
    elif data['ai_cls'] == "PassiveStationary":
        ai_cls = parts.ai.PassiveStationary
    elif data['ai_cls'] == "PlantKeeper":
        ai_cls = parts.ai.PlantKeeper
    else:
        raise NotImplementedError()

    # Provide equipment
    if data['equipment'] == "equipment":
        equipment = Equipment()
    else:
        raise NotImplementedError()

    # Load blood/internal fluids
    if "blood" in data:
        blood = data["blood"]
    else:
        blood = "Blood"

    monster = Actor(
        char=data['char'],
        colour=(data['colour'][0], data['colour'][1], data['colour'][2]),
        tag=data['tag'],
        name=data['name'],
        ai_cls=ai_cls,
        equipment=equipment,
        fighter=Fighter(
            hp=data['fighter']['hp'],
            max_hp=data['fighter']['max_hp'],
            damage_dice=data['fighter']['damage_dice'],
            damage_sides=data['fighter']['damage_sides'],
            strength=data['fighter']['strength'],
            dexterity=data['fighter']['dexterity'],
            vitality=data['fighter']['vitality'],
            intellect=data['fighter']['intellect'],
            perception=data['fighter']['perception'],
            armour=data['fighter']['armour'],
            dodges=data['fighter']['dodges'],
        ),
        corpse=Corpse(
            char=data['corpse']['char'],
            colour=(data['corpse']['colour'][0], data['corpse']['colour'][1], data['corpse']['colour'][2]),
            name=data['corpse']['name'],
            description=data['corpse']['description']
        ),
        inventory=Inventory(
            capacity=data['inventory']['capacity']
        ),
        level=Level(
            level_up_base=data['level']['level_up_base'],
            xp_given=data['level']['xp_given']
        ),
        description=data['description'],
        blood=blood
    )

    # Append drop table if it has one
    if 'drop_table' in data:
        monster.drop_table = data['drop_table']
    else:
        monster.drop_table = {}

    # Load abilities/mutations
    if 'abilities' in data:
        monster.abilities = []
        for ability in data['abilities']:
            ability_obj = None
            if ability == "Shove":
                ability_obj = parts.mutations.Shove()
            elif ability == "Bite":
                ability_obj = parts.mutations.Bite(data['abilities']['Bite']['damage'],
                                                   data['abilities']['Bite']['turns'],
                                                   data['abilities']['Bite']['difficulty'],
                                                   data['abilities']['Bite']['cooldown'])
            elif ability == "MemoryWipe":
                ability_obj = parts.mutations.MemoryWipe(data['abilities']['MemoryWipe']['cooldown'])
            elif ability == "Bludgeon":
                ability_obj = parts.mutations.Bludgeon(data['abilities']['Bludgeon']['damage'],
                                                       data['abilities']['Bludgeon']['sides'],
                                                       data['abilities']['Bludgeon']['turns'],
                                                       data['abilities']['Bludgeon']['difficulty'],
                                                       data['abilities']['Bludgeon']['cooldown'])
            monster.abilities.append(ability_obj)
    if 'mutations' in data:
        monster.mutations = []
        for mutation in data['mutations']:
            # if mutation == "Entomb":
            monster.mutations.append(mutation)
    return monster
