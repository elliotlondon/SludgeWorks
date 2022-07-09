from random import randint

import tcod

from parts.ai import HostileEnemy, NPC, HostileStationary, PassiveStationary
from parts.entity import Actor
from parts.equipment import Equipment
from parts.fighter import Fighter
from parts.inventory import Inventory
from parts.level import Level

# Player
player = Actor(char="@", colour=(255, 255, 255), name="Player",
               ai_cls=HostileEnemy, equipment=Equipment(),
               fighter=Fighter(hp=30, max_hp=30, damage_dice=1, damage_sides=2, strength=12, dexterity=12, vitality=12,
                               intellect=12, perception=12, armour=0, xp=0, dodges=True),
               inventory=Inventory(capacity=26), level=Level(level_up_base=100))

# NPCs
gilbert = Actor(char="@", colour=tcod.green, name="Gilbert",
                ai_cls=NPC, equipment=Equipment(),
                fighter=Fighter(hp=10, max_hp=10, damage_dice=1, damage_sides=2, strength=10, dexterity=10, vitality=10,
                                intellect=10, perception=12, armour=0, xp=0, dodges=True),
                inventory=Inventory(capacity=12), level=Level(xp_given=100))

# Plants
whip_vine = Actor(char='V', colour=(150, 50, 100), name='Whip Vine', ai_cls=HostileStationary, equipment=Equipment(),
                  fighter=Fighter(hp=4, max_hp=4, damage_dice=1, damage_sides=2, armour=1,
                                  strength=14, dexterity=6, vitality=10, intellect=0, perception=0, xp=25,
                                  dodges=False),
                  inventory=Inventory(capacity=0),
                  level=Level(xp_given=25))
bluebell = Actor(char='b', colour=tcod.light_azure, name='Glowing Bluebells',
                 ai_cls=PassiveStationary, equipment=Equipment(),
                 fighter=Fighter(hp=1, max_hp=1, damage_dice=0, damage_sides=0, armour=0,
                                 strength=0, dexterity=0, vitality=10, intellect=0, perception=16, xp=0,
                                 dodges=False),
                 inventory=Inventory(capacity=0),
                 level=Level(xp_given=0))

# Scavengers
wretch = Actor(char='w', colour=(127, 0, 0), name="Wretch",
               ai_cls=HostileEnemy, equipment=Equipment(),
               fighter=Fighter(hp=4, max_hp=4, damage_dice=1, damage_sides=3, armour=0,
                               strength=14, dexterity=10, vitality=12, intellect=8, perception=10, xp=30,
                               dodges=True),
               inventory=Inventory(capacity=8),
               level=Level(xp_given=30))
sludge_fiend = Actor(char='f', colour=(255, 0, 0), name="Sludge Fiend",
                     ai_cls=HostileEnemy, equipment=Equipment(),
                     fighter=Fighter(hp=6, max_hp=6, damage_dice=1, damage_sides=5, armour=0,
                                     strength=16, dexterity=8, vitality=10, intellect=6, perception=8, xp=50,
                                     dodges=True),
                     inventory=Inventory(capacity=8),
                     level=Level(xp_given=50))
thresher = Actor(char='T', colour=(0, 95, 191), name="Thresher",
                 ai_cls=HostileEnemy, equipment=Equipment(),
                 fighter=Fighter(hp=26, max_hp=26, damage_dice=2, damage_sides=6, armour=3,
                                 strength=20, dexterity=12, vitality=12, intellect=5, perception=8, xp=275,
                                 dodges=True),
                 inventory=Inventory(capacity=8),
                 level=Level(xp_given=275))
moire_beast = Actor(char='M', colour=tcod.light_grey, name="Moire Beast",
                    ai_cls=HostileEnemy, equipment=Equipment(),
                    fighter=Fighter(hp=14, max_hp=14, damage_dice=3, damage_sides=2, armour=1,
                                    strength=10, dexterity=16, vitality=12, intellect=10, perception=10, xp=200,
                                    dodges=True),
                    inventory=Inventory(capacity=0),
                    level=Level(xp_given=200))
lupine_terror = Actor(char='L', colour=tcod.dark_grey, name="Lupine Terror",
                      ai_cls=HostileEnemy, equipment=Equipment(),
                      fighter=Fighter(hp=16, max_hp=16, damage_dice=4, damage_sides=2, armour=1,
                                      strength=8, dexterity=14, vitality=10, intellect=6, perception=14, xp=200,
                                      dodges=True),
                      inventory=Inventory(capacity=0),
                      level=Level(xp_given=200))
bloodseeker = Actor(char='B', colour=tcod.light_crimson, name="Bloodseeker",
                    ai_cls=HostileEnemy, equipment=Equipment(),
                    fighter=Fighter(hp=82, max_hp=82, damage_dice=6, damage_sides=8, armour=6,
                                    strength=30, dexterity=20, vitality=18, intellect=14, perception=14, xp=1000,
                                    dodges=False),
                    inventory=Inventory(capacity=0),
                    level=Level(xp_given=1000))

# Cultists
risen_sacrifice = Actor(char='r', colour=tcod.lightest_fuchsia, name="Risen Sacrifice",
                        ai_cls=HostileEnemy, equipment=Equipment(),
                        fighter=Fighter(hp=randint(3, 7), max_hp=20, damage_dice=1, damage_sides=4, armour=0,
                                        strength=12, dexterity=12, vitality=10, intellect=10, perception=10, xp=40,
                                        dodges=True),
                        inventory=Inventory(capacity=8),
                        level=Level(xp_given=40))
celebrant = Actor(char='c', colour=tcod.lightest_purple, name="Eternal Cult Celebrant",
                  ai_cls=HostileEnemy, equipment=Equipment(),
                  fighter=Fighter(hp=8, max_hp=8, damage_dice=2, damage_sides=2, armour=1,
                                  strength=10, dexterity=12, vitality=18, intellect=16, perception=10, xp=160,
                                  dodges=True),
                  inventory=Inventory(capacity=8),
                  level=Level(xp_given=160))
kidnapper = Actor(char='K', colour=tcod.light_fuchsia, name="Eternal Cult Kidnapper",
                  ai_cls=HostileEnemy, equipment=Equipment(),
                  fighter=Fighter(hp=10, max_hp=10, damage_dice=2, damage_sides=4, armour=0,
                                  strength=20, dexterity=10, vitality=12, intellect=10, perception=18, xp=200,
                                  dodges=True),
                  inventory=Inventory(capacity=8),
                  level=Level(xp_given=200))

# Crusaders
crusader = Actor(char='C', colour=tcod.yellow, name="Cleansing Hand Crusader",
                 ai_cls=HostileEnemy, equipment=Equipment(),
                 fighter=Fighter(hp=22, max_hp=22, damage_dice=1, damage_sides=4, armour=0,
                                 strength=22, dexterity=16, vitality=14, intellect=12, perception=12, xp=350,
                                 dodges=True),
                 inventory=Inventory(capacity=8),
                 level=Level(xp_given=350))
purifier = Actor(char='P', colour=tcod.dark_yellow, name="Cleansing Hand Purifier",
                 ai_cls=HostileEnemy, equipment=Equipment(),
                 fighter=Fighter(hp=32, max_hp=32, damage_dice=1, damage_sides=5, armour=0,
                                 strength=24, dexterity=14, vitality=16, intellect=10, perception=14, xp=425,
                                 dodges=True),
                 inventory=Inventory(capacity=8),
                 level=Level(xp_given=425))
duelist = Actor(char='D', colour=tcod.lighter_yellow, name="Cleansing Hand Duelist",
                ai_cls=HostileEnemy, equipment=Equipment(),
                fighter=Fighter(hp=22, max_hp=22, damage_dice=4, damage_sides=4, armour=2,
                                strength=16, dexterity=22, vitality=14, intellect=16, perception=16, xp=200,
                                dodges=True),
                inventory=Inventory(capacity=8),
                level=Level(xp_given=250))

# Horrors
hunchback = Actor(char='H', colour=tcod.brass, name="Hunchback",
                  ai_cls=HostileEnemy, equipment=Equipment(),
                  fighter=Fighter(hp=12, max_hp=12, damage_dice=1, damage_sides=8, armour=1,
                                  strength=18, dexterity=6, vitality=8, intellect=12, perception=10, xp=150,
                                  dodges=True),
                  inventory=Inventory(capacity=8),
                  level=Level(xp_given=150))

# Bosses / Uniques
alanwric = Actor(char='A', colour=tcod.light_yellow, name="Alanwric the Spinning Blade",
                 ai_cls=HostileEnemy, equipment=Equipment(),
                 fighter=Fighter(hp=42, max_hp=42, damage_dice=8, damage_sides=4, armour=6,
                                 strength=28, dexterity=28, vitality=18, intellect=16, perception=18, xp=1550),
                 inventory=Inventory(capacity=12),
                 level=Level(xp_given=1550))
teague = Actor(char='T', colour=tcod.darkest_yellow, name="Teague the Martyr",
               ai_cls=HostileEnemy, equipment=Equipment(),
               fighter=Fighter(hp=64, max_hp=64, damage_dice=4, damage_sides=4, armour=0,
                               strength=20, dexterity=20, vitality=20, intellect=20, perception=20, xp=2500),
               inventory=Inventory(capacity=12),
               level=Level(xp_given=2500))
dymacia = Actor(char='D', colour=tcod.darkest_fuchsia, name="Cultist Queen Dymacia",
                ai_cls=HostileEnemy, equipment=Equipment(),
                fighter=Fighter(hp=48, max_hp=48, damage_dice=1, damage_sides=6, armour=2,
                                strength=20, dexterity=20, vitality=24, intellect=30, perception=26, xp=2000),
                inventory=Inventory(capacity=12),
                level=Level(xp_given=2000))
