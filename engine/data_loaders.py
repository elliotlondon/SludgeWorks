import os
import shelve
import shutil


def save_game(player, entities, game_map, message_log, game_state):
    if not os.path.isfile('savegames\savegame.dat'):
        os.makedirs('savegames')
    with shelve.open('savegames/savegame', 'n') as data_file:
        data_file['player_index'] = entities.index(player)
        data_file['entities'] = entities
        data_file['game_map'] = game_map
        data_file['message_log'] = message_log
        data_file['game_state'] = game_state


def load_game():
    if not os.path.isfile('savegames/savegame.dat'):
        raise FileNotFoundError

    with shelve.open('savegames/savegame', 'r') as data_file:
        player_index = data_file['player_index']
        entities = data_file['entities']
        game_map = data_file['game_map']
        message_log = data_file['message_log']
        game_state = data_file['game_state']
    player = entities[player_index]

    return player, entities, game_map, message_log, game_state


def delete_char_save():
    if not os.path.isdir('savegames'):
        return
    shutil.rmtree('savegames')
