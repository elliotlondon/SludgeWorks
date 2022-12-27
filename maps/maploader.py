import random
import copy

import maps.game_map
from data.object_factory import create_static_object_from_json
from data.item_factory import create_item_from_json
from data.monster_factory import create_monster_from_json

import pandas as pd

from config.exceptions import DataLoadError

from maps.game_map import GameMap
import maps.tiles

from core.engine import Engine


class MapLoader():
    """Assistant object for loading and decoding prefabs and hand-made levels so that they can be created using
    the maps.game_map.GameWorld class."""
    def __init__(self):
        self.mapfile = None

    def load_map_from_file(self, fname: str):
        # Attempt to load the map in .csv format according to the supplied filename str.
        try:
            self.mapfile = pd.read_csv(f"data/prefabs/{fname}.csv")
        except FileNotFoundError:
            raise FileNotFoundError(f"Map prefab file '{fname}' not found.")

    def convert_mapfile(self, engine: Engine) -> GameMap:
        # Convert a loaded mapfile dataframe into a GameMap object
        map_width = self.mapfile.shape[1]
        map_height = self.mapfile.shape[0]

        # First, create a GameMap of the same size as the loaded map
        new_map = GameMap(engine, map_width, map_height)

        # Iterate over all cells to generate the tiles and objects in the corresponding game_map coords
        for i in range(map_width):
            for j in range(map_height):
                # Get cell value
                cell_value = self.mapfile.values[j, i]
                if type(cell_value) == float:
                    continue
                else:
                    cell_value.split()

                # Go through all tiles and generate what is needed, first floor tiles
                if 'dirt' in cell_value:
                    new_map.tiles[i, j] = random.choice(maps.tiles.floor_tiles_1)
                elif 'verdant' in cell_value:
                    new_map.tiles[i, j] = random.choice(maps.tiles.verdant_tiles_1)
                elif 'muddy_wall' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.muddy_wall
                elif 'chasm_wall' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.chasm_wall
                elif 'rubble' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.rubble
                elif 'wooden_wall' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.wooden_wall
                elif 'metal_bars' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.metal_bars
                elif 'bridge' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.bridge
                elif 'water' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.water
                elif 'blood' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.blood
                elif 'hole' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.hole
                elif 'pit' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.pit
                elif 'waterfall' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.waterfall
                else:
                    raise DataLoadError(f'Tile could not be loaded from corresponding given str {cell_value}')

                if 'stairs' in cell_value:
                    new_map.tiles[i, j] = maps.tiles.down_stairs
                    new_map.downstairs_location = (i, j)

                # Now check additional cell values and spawn/create appropriately
                if 'player' in cell_value:
                    engine.player.place(*(i, j), new_map)
                elif 'metal_door_top' in cell_value:
                    door_top = copy.deepcopy(
                        create_static_object_from_json(f"data/static_objects/core_objects.json", 'metal_door_top'))
                    door_top.spawn_quietly(new_map, i, j)
                elif 'metal_door_side' in cell_value:
                    door_top = copy.deepcopy(
                        create_static_object_from_json(f"data/static_objects/core_objects.json", 'metal_door_top'))
                    door_top.spawn_quietly(new_map, i, j)
                elif 'door_top' in cell_value:
                    door_top = copy.deepcopy(
                        create_static_object_from_json(f"data/static_objects/core_objects.json", 'shanty_door_top'))
                    door_top.spawn_quietly(new_map, i, j)
                elif 'door_side' in cell_value:
                    door_side = copy.deepcopy(
                        create_static_object_from_json(f"data/static_objects/core_objects.json",
                                                       'shanty_door_side'))
                    door_side.spawn_quietly(new_map, i, j)
                elif 'trash' in cell_value:
                    trash = copy.deepcopy(
                        create_item_from_json(f"data/items/other.json", 'trash'))
                    trash.spawn_quietly(new_map, i, j)

        new_map.accessible = new_map.calc_accessible()
        return new_map
