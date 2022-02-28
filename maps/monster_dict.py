from lib.fighter import Fighter
from lib.ai import *
from lib.inventory import Inventory
from lib.equipment import Equipment
from maps.item_dict import *


'''
COMMON ENEMIES 
'''


# PLANTS
def whip_vine(x, y):
    fighter_component = Fighter(current_hp=4, max_hp=4, damage_dice=1, damage_sides=2, armour=1,
                                strength=14, dexterity=6, vitality=10, intellect=0, perception=0, xp=25,
                                dodges=False)
    ai_component = Stationary()
    monster = Entity(x, y, 'V', libtcod.light_grey, 'Whip Vine',
                  'What at first appears to be no more than a dead, waist-height bush in actuality '
                  'represents a highly specialized carnivorous plant that flays the skin off any creature '
                  'that wanders into its path.',
                  blocks=True, render_order=RenderOrder.PLANT, fighter=fighter_component, ai=ai_component,
                  faction='Plants')
    return monster


def phosphorescent_dahlia(x, y):
    fighter_component = Fighter(current_hp=1, max_hp=1, damage_dice=0, damage_sides=0, armour=0,
                                strength=0, dexterity=0, vitality=10, intellect=0, perception=16, xp=0,
                                dodges=False)
    ai_component = PassiveStationary()
    monster = Entity(x, y, 'd', libtcod.light_azure, 'Phosphorescent Dahlia',
                  'A common but perplexing sight within the SludgeWorks is to observe a brilliant flash of blue light, '
                  'instantaneously illuminating an entire cave section like a flash of lightning. The phosphorescent '
                  'dahlia is a well-known source of such flashes in this spectral region; a delicate plant which has '
                  'developed what some consider a visually offensive method of attracting pollinators.',
                  blocks=False, render_order=RenderOrder.PLANT, fighter=fighter_component, ai=ai_component,
                  regenerates=False, faction='Plants')
    return monster


# SCAVENGERS
def wretch(x, y):
    fighter_component = Fighter(current_hp=4, max_hp=4, damage_dice=1, damage_sides=3, armour=0,
                                strength=14, dexterity=10, vitality=12, intellect=8, perception=10, xp=30,
                                dodges=True)
    equipment_component = Equipment(())
    inventory_component = Inventory(10)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'w', libtcod.darker_red, 'Wretch',
                  'A stunted human swaddled in filthy rags and long since driven feral by the SludgeWorks.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  inventory=inventory_component, equipment=equipment_component,
                  regenerates=True, faction='Scavengers', errasticity=25)
    monster.inventory.spawn_with(monster, iron_dagger(monster.x, monster.y))
    return monster


def sludge_fiend(x, y):
    fighter_component = Fighter(current_hp=6, max_hp=6, damage_dice=1, damage_sides=5, armour=0,
                                strength=16, dexterity=8, vitality=10, intellect=6, perception=8, xp=50,
                                dodges=True)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'f', libtcod.red, 'Sludge Fiend',
                  'The irony of attempting to retain one\'s humanity whilst simultaneously seeking to consume '
                  'all mutagenic material in one\'s path seems to be lost on this poor unfortunate. Tattered clothing '
                  'drips off this mutant\'s twisted form like a bullet-shredded cape; obsidian spikes protrude '
                  'in clusters from its emaciated and discoloured torso.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Scavengers', errasticity=50)
    return monster


def thresher(x, y):
        fighter_component = Fighter(current_hp=26, max_hp=26, damage_dice=2, damage_sides=6, armour=3,
                                    strength=20, dexterity=12, vitality=12, intellect=5, perception=8, xp=275,
                                    dodges=True)
        ai_component = AimlessWanderer()
        monster = Entity(x, y, 'T', libtcod.dark_azure, 'Thresher',
                      'A colossal ogre-like hominid covered in patches of matted hair and littered with scars. This '
                      'creature tirelessly searches it\'s surroundings for new objects to smash together with a '
                      'joyous, childlike expression.',
                      blocks=True, fighter=fighter_component, render_order=RenderOrder.ACTOR, ai=ai_component,
                      regenerates=True, faction='Scavengers', errasticity=75)
        return monster


# BEASTS
def moire_beast(x, y):
    fighter_component = Fighter(current_hp=14, max_hp=14, damage_dice=3, damage_sides=2, armour=1,
                                strength=10, dexterity=16, vitality=12, intellect=10, perception=10, xp=200,
                                dodges=True)
    ai_component = Aggressive()
    monster = Entity(x, y, 'M', libtcod.light_grey, 'Moire Beast',
                  'The hide of this squat quadruped is an affront to the senses; dense and intricate greyscale '
                  'patterns constantly shift epileptically upon the beast\'s surface like a surrealist '
                  'interpretation of a zebra. The gleam of it\'s fluorescent yellow, feline irises serve as the only '
                  'ubiquitous reference point on this beast\'s wildly fluctuating, migraine-inducing form.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Beasts')
    return monster


def lupine_terror(x, y):
    fighter_component = Fighter(current_hp=16, max_hp=16, damage_dice=4, damage_sides=2, armour=1,
                                strength=8, dexterity=14, vitality=10, intellect=6, perception=14, xp=200,
                                dodges=True)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'L', libtcod.dark_grey, 'Lupine Terror',
                  'Evolutionary forces have twisted what must undeniably once have been a feral wolf into a horrific '
                  'vision of fangs and matted, grey fur. This monstrosity walks upright in emulation of nature\'s most '
                  'infamous apex predators as blood-tinged saliva hangs from it\'s constantly masticating jaws.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Beasts', errasticity=50)
    return monster


def bloodseeker(x, y):
    """
    If you see a bloodseeker, you should seriously consider running for your life. These guys are not afraid to
    completely destroy even high-powered players.
    Their cruelest ability is to have a chance to confiscate metal weapons from the player if stabbing/thrusting
    attacks are used, and due to their Ironmonger ability, these weapons will be permanently destroyed and also buff
    the Bloodseeker. They are also able to slam the player multiple spaces in their attacking direction,
    causing a stun. Their regeneration rate is insane, but is negated if they are on fire. They are immune to fear,
    poison and disease. Generally a fucking nightmare.
    """
    fighter_component = Fighter(current_hp=82, max_hp=82, damage_dice=6, damage_sides=8, armour=6,
                                strength=30, dexterity=20, vitality=18, intellect=14, perception=14, xp=1000,
                                dodges=False)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'B', libtcod.light_crimson, 'Bloodseeker',
                  'An asymmetric monstrosity the size of a bear with a grinning, skinless snout. Rusted weaponry from '
                  'previous encounters juts from it\'s hide like gruesome jewellery, with pale, twisted flesh creeping '
                  'up the hilts. The creature\'s eyes are consumed by feral rage as it prowls the caverns, twitching '
                  'from the eternal	state of pain inflicted by its inherent regeneration.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Beast', errasticity=100)
    return monster


# CULTISTS
def risen_sacrifice(x, y):
    """
    Although essentially a trash mob, these guys do not regenerate but have a large amount of HP. When coupled with
    celebrants (who have group-heal abilities for those of the same faction) these guys turn into horrid tanks that
    can easily overwhelm the player.
    """
    fighter_component = Fighter(current_hp=randint(3, 7), max_hp=20, damage_dice=1, damage_sides=4, armour=0,
                                strength=12, dexterity=12, vitality=10, intellect=10, perception=10, xp=40,
                                dodges=True)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'r', libtcod.lightest_fuchsia, 'Risen Sacrifice',
                  'For those who have never encountered them, it is very easy to dismiss the Cult of Eternity as '
                  'a sect of aimless madmen with an obsessive focus upon human sacrifice. Those who have seen the '
                  'radiant bodies of the recently sacrificed reanimating joyfully, with blood still flowing from their '
                  'mortal wounds would strongly disagree with this statement.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  faction='Cultists', errasticity=34)
    return monster


def eternal_celebrant(x, y):
    fighter_component = Fighter(current_hp=8, max_hp=8, damage_dice=2, damage_sides=2, armour=1,
                                strength=10, dexterity=12, vitality=18, intellect=16, perception=10, xp=160,
                                dodges=True)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'c', libtcod.lightest_purple, 'Eternal Cult Celebrant',
                  'The celebrant\'s dour, puckered form desperately hauls itself through the scratch-marked tunnels '
                  'towards the blissful murmurs of his newly-risen flock. \"Sweet children, where are you?\" he cries '
                  'out; a worn, sacrificial dagger trembles within his hand, piercing the suffocating darkness in '
                  'search of replies.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  faction='Cultists', errasticity=100)
    return monster


def eternal_kidnapper(x, y):
    fighter_component = Fighter(current_hp=10, max_hp=10, damage_dice=2, damage_sides=4, armour=0,
                                strength=20, dexterity=10, vitality=12, intellect=10, perception=18, xp=200,
                                dodges=True)
    equipment_component = Equipment(())
    inventory_component = Inventory(10)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'k', libtcod.light_fuchsia, 'Eternal Cult Kidnapper',
                  'By far the most notorious member of the Cult of Eternity and arguably serving the most '
                  'necessary role within their hierarchy. Their mission is simple: Kidnap the most virginal '
                  'entrants into the SludgeWorks so that the flow of flesh into the Palace of Hedonism is '
                  'constant and plentiful. The way they creep through the caverns with their threatening iron '
                  'blackjack makes this intention undeniably clear.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  equipment=equipment_component, inventory=inventory_component,
                  regenerates=True, faction='Cultists', errasticity=67)
    monster.inventory.spawn_with(monster, leather_armour(x, y))
    monster.inventory.spawn_with(monster, iron_buckler(x, y))
    return monster


# CLEANSING HAND
def cleansing_hand_crusader(x, y):
    fighter_component = Fighter(current_hp=22, max_hp=22, damage_dice=1, damage_sides=4, armour=0,
                                strength=22, dexterity=16, vitality=14, intellect=12, perception=12, xp=350,
                                dodges=True)
    equipment_component = Equipment(())
    inventory_component = Inventory(10)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'C', libtcod.yellow, 'Cleansing Hand Crusader',
                  'The staple foot soldier of the Cleansing Hand. With his bucket helm, emblazoned tabard and well-'
                  'maintained platemail it is easy to see how these defenders of the faith are commonly known as '
                  'crusaders. Their tactics, however, as anything but medieval - intimidatingly rigorous discipline '
                  'combined with years of experience slaying deformed monstrosities leaves the crusaders fully able '
                  'to hold their own against many daily challenges experienced within the SludgeWorks.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  equipment=equipment_component, inventory=inventory_component,
                  regenerates=True, faction='Cleansing Hand', errasticity=67)
    monster.inventory.spawn_with(monster, steel_cuirass(x, y))
    monster.inventory.spawn_with(monster, steel_longsword(x, y))
    monster.inventory.spawn_with(monster, steel_greatshield(x, y))
    return monster


def cleansing_hand_purifier(x, y):
    fighter_component = Fighter(current_hp=32, max_hp=32, damage_dice=1, damage_sides=5, armour=0,
                                strength=24, dexterity=14, vitality=16, intellect=10, perception=14, xp=425,
                                dodges=True)
    equipment_component = Equipment(())
    inventory_component = Inventory(10)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'P', libtcod.dark_yellow, 'Cleansing Hand Purifier',
                  'The purifier breathes deeply and calmly as his mail-clad fists tighten around the hilt of his '
                  'terrifying, studded morningstar. Although you cannot see any human flesh underneath his plated and '
                  'visored form you can be assured that what lies within is utterly untouched by the corrupting '
                  'influence of the SludgeWorks, and utterly devoted to preventing further horrific incursions into '
                  'Cleansing Hand territory. Never again will the last bastion of purity be defiled by such entropy.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  equipment=equipment_component, inventory=inventory_component,
                  regenerates=True, faction='Cleansing Hand', errasticity=14)
    monster.inventory.spawn_with(monster, steel_cuirass(x, y))
    monster.inventory.spawn_with(monster, steel_mace(x, y))
    monster.inventory.spawn_with(monster, steel_greatshield(x, y))
    return monster


def cleansing_hand_duelist(x, y):
    fighter_component = Fighter(current_hp=22, max_hp=22, damage_dice=4, damage_sides=4, armour=2,
                                strength=16, dexterity=22, vitality=14, intellect=16, perception=16, xp=200,
                                dodges=True)
    ai_component = Aggressive()
    monster = Entity(x, y, 'a', libtcod.lighter_yellow, 'Cleansing Hand Duelist',
                  'Distinct from the stalwart and dour-faced Cleansing Hand Paladin sect, the members of the '
                  'Ascetic Church have a slightly different interpretation of the discipline required to overcome the '
                  'threat of their imminent demise. Glacial patience, staunch traditionalism and a complete lack of '
                  'fear has led to a collective which has perfected the art of Zweihander duelling. This master\'s '
                  'Alber stance enthusiastically goads the degenerated masses directly into his flawless riposte.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Cleansing Hand')
    return monster


# HORRORS
def hunchback(x, y):
    fighter_component = Fighter(current_hp=12, max_hp=12, damage_dice=1, damage_sides=8, armour=1,
                                strength=18, dexterity=6, vitality=8, intellect=12, perception=10, xp=150,
                                dodges=True)
    ai_component = Aggressive()
    monster = Entity(x, y, 'H', libtcod.brass, 'Hunchback',
                  'A stunted and broken humanoid draped in tattered linen stained with the characteristic ochre '
                  'of dried blood. It\'s face is completely concealed by a tapered hood; the glint of a wicked '
                  'kirpan scatters all nearby light. Echoes of guttural chanting reverberate off the cave '
                  'walls as it glacially stumbles forward towards its next target.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Horrors', errasticity=10)
    return monster


'''
UNIQUE ENEMIES
'''


# CLEANSING HAND
def alfonrice(x, y):
    """
    Although not head of the duellist sect, Alfonrice is their most skilled member. He frequently makes use of
    cleaving and parrying and primarily deals with thrusting attacks, meaning that your armour is likely to not be of
    great help against his 40+ damage crits. If you manage to disarm him though he's basically useless and can just
    be spammed to death. Upon death he drops his swordbreaker, which is an offhand weapon which considerably improves
    parry chance, str and dex bonus, but has no armour rating.
    """
    fighter_component = Fighter(current_hp=42, max_hp=42, damage_dice=8, damage_sides=4, armour=6,
                                strength=28, dexterity=28, vitality=18, intellect=16, perception=18, xp=1550)
    ai_component = AimlessWanderer()
    monster = Entity(x, y, 'A', libtcod.light_yellow, 'Alfonrice, the Spinning Blade',
                  'The Cleansing Hand\'s most pious duelist Alfonrice earned his moniker not from the constant'
                  'twirling of his offhand swordbreaker, but from his proficiency in dispatching hordes of filthy '
                  'horrors with a single cleave of his cruciform broadsword. He grits his teeth in anticipation, '
                  'anxious to cut down the next prospective entrant to the Most Holy Bastion.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Cleansing Hand', errasticity=50)
    return monster


def teague(x, y):
    """
    Teague is meant to be an optional, powerful boss which is positioned behind a hidden, breakable wall in a certain
    part of the Cleansing Hand Bastion's main cathedral. He was one of the earliest leaders of the Cleansing Hand, but
    became corrupted by the SludgeWorks. As he was so revered, his personal guard locked him away and spread the story
    that he committed suicide to preserve the purity, serving as a martyr and inspiration to all crusaders. He is
    remembered by an ornate statue within the cathedral and is worshipped as a martyr.
    If the player is able to both detect and commune telepathically with him he will implore them to free him with
    promises of great power, and under certain conditions he will reveal some dark secrets about the Cleansing Hand, and
    the weaknesses of some of their leaders. He may be willing to cooperate if the player is very pure but hostile to
    the Cleansing Hand.
    Teague is particularly dangerous as he regenerates very quickly, is an expert in hand-to-hand combat and uses
    abilities which can pull the player towards him and his melee attacks have a chance of setting the player on fire.
    His most infamous technique is his ability to steal mutations from the player, making him spiral out of control
    very quickly when facing impure players and probably spelling certain doom. When killed, if the player is impure,
    all mutations which he has are passed onto the player, including those which were stolen.
    If encountered by the cleansing hand they have a high chance of fleeing in fear or worshipping him, which allows
    basically allows him to annihilate them and absorb their power.
    """
    fighter_component = Fighter(current_hp=64, max_hp=64, damage_dice=4, damage_sides=4, armour=0,
                                strength=20, dexterity=20, vitality=20, intellect=20, perception=20, xp=2500)
    ai_component = Aggressive()
    monster = Entity(x, y, 'T', libtcod.darkest_yellow, 'Teague the Martyr',
                  'The remnants of a dust-drenched, threadbare robe cling desperately to Teague\'s gaunt, hollow form '
                  'as he slowly pivots towards you. Despite decades of imprisonment, his skin is unblemished and pure '
                  'like that of a newborn child, and he calmly stares you down with unabashed superiority. One could '
                  'say that his entire life has been building up to this moment, and you are all that stands in the '
                  'way between him and complete control of the Bastion. The crusader\'s greatest shame and most '
                  'defiled heiromonk bows elegantly, politely inviting you to be cleansed by his own hands.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Cleansing Hand')
    return monster


# CULTISTS
def dymacia(x, y):
    fighter_component = Fighter(current_hp=48, max_hp=48, damage_dice=1, damage_sides=6, armour=2,
                                strength=20, dexterity=20, vitality=24, intellect=30, perception=26, xp=2000)
    ai_component = Aggressive()
    monster = Entity(x, y, 'D', libtcod.darkest_fuchsia, 'Dymacia, Effigy of Perfection',
                  'Lovingly adorned with countless rosaries, letters of worship and symbolic mirrors, Dymanikos '
                  'effortlessly demonstrates her ability to command unfaltering loyalty in her followers. At least '
                  'eight feet tall, her towering stature is coupled with an inhumanly soothing voice that fills the '
                  'cathedral with a pure, monotone chant. This woman appears to be wholly unarmed, but you are not so '
                  'easily deceived to think this she has ascended to a position of such power due to her weaknesses.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  regenerates=True, faction='Cultists')
    return monster
