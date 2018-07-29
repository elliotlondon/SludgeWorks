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

    @property
    def damage_dice(self):
        damage_dice = 0

        if self.main_hand and self.main_hand.equippable:
            damage_dice = self.main_hand.equippable.damage_dice
        if self.off_hand and self.off_hand.equippable:
            damage_dice = self.off_hand.equippable.damage_dice

        return damage_dice

    @property
    def damage_sides(self):
        damage_sides = 0

        if self.main_hand and self.main_hand.equippable:
            damage_sides = self.main_hand.equippable.damage_sides
        if self.off_hand and self.off_hand.equippable:
            damage_sides = self.off_hand.equippable.damage_sides

        return damage_sides

    @property
    def strength_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.strength_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.strength_bonus
        if self.head and self.head.equippable:
            bonus += self.head.equippable.strength_bonus
        if self.torso and self.torso.equippable:
            bonus += self.torso.equippable.strength_bonus
        if self.hands and self.hands.equippable:
            bonus += self.main_hand.equippable.strength_bonus
        if self.legs and self.legs.equippable:
            bonus += self.legs.equippable.strength_bonus
        if self.feet and self.feet.equippable:
            bonus += self.feet.equippable.strength_bonus
        if self.left_hand and self.left_hand.equippable:
            bonus += self.left_hand.equippable.strength_bonus
        if self.right_hand and self.right_hand.equippable:
            bonus += self.right_hand.equippable.strength_bonus

        return bonus

    @property
    def agility_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.agility_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.agility_bonus
        if self.head and self.head.equippable:
            bonus += self.head.equippable.agility_bonus
        if self.torso and self.torso.equippable:
            bonus += self.torso.equippable.agility_bonus
        if self.hands and self.hands.equippable:
            bonus += self.main_hand.equippable.agility_bonus
        if self.legs and self.legs.equippable:
            bonus += self.legs.equippable.agility_bonus
        if self.feet and self.feet.equippable:
            bonus += self.feet.equippable.agility_bonus
        if self.left_hand and self.left_hand.equippable:
            bonus += self.left_hand.equippable.agility_bonus
        if self.right_hand and self.right_hand.equippable:
            bonus += self.right_hand.equippable.agility_bonus

        return bonus

    @property
    def vitality_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.vitality_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.vitality_bonus
        if self.head and self.head.equippable:
            bonus += self.head.equippable.vitality_bonus
        if self.torso and self.torso.equippable:
            bonus += self.torso.equippable.vitality_bonus
        if self.hands and self.hands.equippable:
            bonus += self.main_hand.equippable.vitality_bonus
        if self.legs and self.legs.equippable:
            bonus += self.legs.equippable.vitality_bonus
        if self.feet and self.feet.equippable:
            bonus += self.feet.equippable.vitality_bonus
        if self.left_hand and self.left_hand.equippable:
            bonus += self.left_hand.equippable.vitality_bonus
        if self.right_hand and self.right_hand.equippable:
            bonus += self.right_hand.equippable.vitality_bonus

        return bonus

    @property
    def intellect_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.intellect_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.intellect_bonus
        if self.head and self.head.equippable:
            bonus += self.head.equippable.intellect_bonus
        if self.torso and self.torso.equippable:
            bonus += self.torso.equippable.intellect_bonus
        if self.hands and self.hands.equippable:
            bonus += self.main_hand.equippable.intellect_bonus
        if self.legs and self.legs.equippable:
            bonus += self.legs.equippable.intellect_bonus
        if self.feet and self.feet.equippable:
            bonus += self.feet.equippable.intellect_bonus
        if self.left_hand and self.left_hand.equippable:
            bonus += self.left_hand.equippable.intellect_bonus
        if self.right_hand and self.right_hand.equippable:
            bonus += self.right_hand.equippable.intellect_bonus

        return bonus

    @property
    def perception_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.perception_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.perception_bonus
        if self.head and self.head.equippable:
            bonus += self.head.equippable.perception_bonus
        if self.torso and self.torso.equippable:
            bonus += self.torso.equippable.perception_bonus
        if self.hands and self.hands.equippable:
            bonus += self.main_hand.equippable.perception_bonus
        if self.legs and self.legs.equippable:
            bonus += self.legs.equippable.perception_bonus
        if self.feet and self.feet.equippable:
            bonus += self.feet.equippable.perception_bonus
        if self.left_hand and self.left_hand.equippable:
            bonus += self.left_hand.equippable.perception_bonus
        if self.right_hand and self.right_hand.equippable:
            bonus += self.right_hand.equippable.perception_bonus

        return bonus

    def toggle_equip(self, equippable_entity):
        results = []

        slot = equippable_entity.equippable.slot
        if slot == EquipmentSlots.MAIN_HAND:
            if self.main_hand == equippable_entity:
                self.main_hand = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.main_hand:
                    results.append({'dequipped': self.main_hand})

                self.main_hand = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.OFF_HAND:
            if self.off_hand == equippable_entity:
                self.off_hand = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.off_hand:
                    results.append({'dequipped': self.off_hand})

                self.off_hand = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.HEAD:
            if self.head == equippable_entity:
                self.head = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.head:
                    results.append({'dequipped': self.head})

                self.head = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.TORSO:
            if self.torso == equippable_entity:
                self.torso = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.torso:
                    results.append({'dequipped': self.torso})

                self.torso = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.HANDS:
            if self.hands == equippable_entity:
                self.hands = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.hands:
                    results.append({'dequipped': self.hands})

                self.hands = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.LEGS:
            if self.legs == equippable_entity:
                self.legs = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.legs:
                    results.append({'dequipped': self.legs})

                self.legs = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.FEET:
            if self.feet == equippable_entity:
                self.feet = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.feet:
                    results.append({'dequipped': self.feet})

                self.feet = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.LEFT_HAND:
            if self.left_hand == equippable_entity:
                self.left_hand = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.left_hand:
                    results.append({'dequipped': self.left_hand})

                self.left_hand = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.RIGHT_HAND:
            if self.right_hand == equippable_entity:
                self.right_hand = None
                results.append({'dequipped': equippable_entity})
            else:
                if self.right_hand:
                    results.append({'dequipped': self.right_hand})

                self.right_hand = equippable_entity
                results.append({'equipped': equippable_entity})

        return results


class Equippable:
    def __init__(self, slot, damage_dice=0, damage_sides=0,
                 strength_bonus=0, agility_bonus=0, vitality_bonus=0, intellect_bonus=0, perception_bonus=0):
        self.slot = slot
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.strength_bonus = strength_bonus
        self.agility_bonus = agility_bonus
        self.vitality_bonus = vitality_bonus
        self.intellect_bonus = intellect_bonus
        self.perception_bonus = perception_bonus
