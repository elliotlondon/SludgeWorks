import math


class Level:
    def __init__(self, current_level=1, current_xp=0):
        self.current_level = current_level
        self.current_xp = current_xp

    @property
    def experience_to_next_level(self):
        return math.floor(100*2*self.current_level*math.exp(1)/3 + self.current_level*math.exp(1))

    def add_xp(self, xp):
        self.current_xp += xp

        if self.current_xp > self.experience_to_next_level:
            self.current_xp -= self.experience_to_next_level
            self.current_level += 1

            return True
        else:
            return False
