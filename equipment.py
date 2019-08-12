from equipment_slots import EquipmentSlots


class Equipment:
    def __init__(self, main_hand=None, off_hand=None, head=None, torso=None, hands=None, legs=None, feet=None,
                 left_hand=None, right_hand=None):
        self.main_hand = main_hand
        self.off_hand = off_hand
        self.head = head
        self.torso = torso
        self.hands = hands
        self.legs = legs
        self.feet = feet
        self.left_hand = left_hand
        self.right_hand = right_hand

    def __iter__(self):
        for attr in self.__dict__.items():
            yield attr

    @property
    def damage_dice(self):
        damage_dice = 0

        if self.main_hand and self.main_hand.equippable:
            damage_dice = self.main_hand.equippable.damage_dice

        return damage_dice

    @property
    def damage_sides(self):
        damage_sides = 0

        if self.main_hand and self.main_hand.equippable:
            damage_sides = self.main_hand.equippable.damage_sides

        return damage_sides

    @property
    def strength_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.strength_bonus

        return bonus

    @property
    def dexterity_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.dexterity_bonus

        return bonus

    @property
    def vitality_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.vitality_bonus

        return bonus

    @property
    def intellect_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.intellect_bonus

        return bonus

    @property
    def perception_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.perception_bonus

        return bonus

    @property
    def armour_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.armour_bonus

        return bonus

    def toggle_equip(self, equippable_entity):
        results = []
        slot = equippable_entity.equippable.slot
        for x in vars(EquipmentSlots):
            if getattr(EquipmentSlots, x) == slot:
                if getattr(self, x.lower()) == equippable_entity:
                    setattr(self, x.lower(), None)
                    results.append({'dequipped': equippable_entity})

                else:
                    if getattr(self, x.lower()) == equippable_entity:
                        results.append({'dequipped': equippable_entity})

                    setattr(self, x.lower(), equippable_entity)
                    results.append({'equipped': equippable_entity})
                    break

        return results


class Equippable:
    def __init__(self, slot, damage_dice=0, damage_sides=0,
                 strength_bonus=0, dexterity_bonus=0, vitality_bonus=0, intellect_bonus=0, perception_bonus=0,
                 armour_bonus=0):
        self.slot = slot
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.strength_bonus = strength_bonus
        self.dexterity_bonus = dexterity_bonus
        self.vitality_bonus = vitality_bonus
        self.intellect_bonus = intellect_bonus
        self.perception_bonus = perception_bonus
        self.armour_bonus = armour_bonus

    def __iter__(self):
        for attr in self.__dict__.items():
            yield attr
