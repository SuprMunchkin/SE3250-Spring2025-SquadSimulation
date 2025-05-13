import matplotlib.pyplot as plt
from random import uniform, choice, randint, random
from IPython.display import display, clear_output
import math

class Unit:
    def __init__(self, x, y, num_people, lethality, defense):
        self.x = x
        self.y = y
        self.num_people = num_people
        self.lethality = lethality
        self.defense = defense
        self.history = [(x, y)]
        self.visited = {(x, y)}

    def get_coordinates(self):
        return self.x, self.y

    def get_numPeople(self):
        return self.num_people

    def get_lethality(self):
        return self.lethality

    def get_defense(self):
        return self.defense

    def move(self):
        dx = uniform(-0.05, 0.05)
        dy = uniform(-0.05, 0.05)
        self.x = min(max(self.x + dx, 0), 1)
        self.y = min(max(self.y + dy, 0), 1)
        self.history.append((self.x, self.y))
        self.visited.add((round(self.x, 2), round(self.y, 2)))
        return True

class GoodUnit(Unit):
    def __init__(self, armor, energy, num_people):
        super().__init__(0, 0, num_people, lethality=0.90, defense=0.0)  # Start at the top-left corner
        self.armor = armor
        self.energy = energy
        self.move_counter = 0
        self.exiting = False
        self.angle = 0  # Start angle for polar coordinates
        self.radius = 0  # Start radius at 0
        self.max_radius = uniform(0.5, 1)  # Random maximum radius
        print(f"Max radius: {self.max_radius}")
        self.increasing = True  # Flag to indicate whether the radius is increasing
        self._adjust_for_armor()

    def _adjust_for_armor(self):
        if self.armor == 'Light':
            self.water = 5.0 * 3 * self.num_people
            self.energy_depletion_factor = 0.03
            self.defense = 0.20
        elif self.armor == 'Medium':
            self.water = 3.0 * 3 * self.num_people
            self.energy_depletion_factor = 0.05
            self.defense = 0.35
        elif self.armor == 'Heavy':
            self.water = 1.0 * 3 * self.num_people
            self.energy_depletion_factor = 0.07
            self.defense = 0.50

    def move(self):
        print(f"Move from: radius={self.radius}, angle={self.angle}, increasing={self.increasing}")

        if self.energy <= 0 or self.exiting:
            print(f"Stopping movement: energy={self.energy}, exiting={self.exiting}")
            return False

        # Adjust the radius
        if self.increasing:
            self.radius += uniform(0.2,0.4)  # Gradually increase the radius
            if self.radius >= self.max_radius or self.angle >= math.pi / 4:
                self.increasing = False  # Start decreasing the radius
        else:
            self.radius -= uniform(0.2,0.4)  # Gradually decrease the radius
            if self.radius <= 0 or self.angle >= math.pi / 2:
                self.radius = 0
                self.history.append((0,0))
                self.visited.add((0,0))
                self.move_counter += 1
                print("Returned to start.")
                return False  # Stop movement when the radius reaches 0

        # Increment the angle to trace out a circular path
        self.angle += uniform(0.1, 0.4)  # Increment angle by a small random value
        print(f"Move to: radius={self.radius}, angle={self.angle}, increasing={self.increasing}")

        # Convert polar coordinates to Cartesian coordinates
        new_x = self.radius * math.cos(self.angle)
        new_y = self.radius * math.sin(self.angle)

        # Ensure the new position is within bounds
        new_x = min(max(new_x, 0), 1)
        new_y = min(max(new_y, 0), 1)

        # Update position and history
        self.x, self.y = new_x, new_y
        self.history.append((self.x, self.y))
        self.visited.add((round(self.x, 2), round(self.y, 2)))
        self.move_counter += 1

        # Decrease water and energy
        self.water -= 0.01 * self.num_people
        self.energy -= self.energy_depletion_factor

        if self.water <= 0:
            self.water = 0
            self.energy -= 0.1

        if self.energy <= 0:
            self.energy = 0

        print(f"Move: x={self.x}, y={self.y}, energy={self.energy}, water={self.water}")
        return True

class BadUnit(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, num_people=randint(30, 50), lethality=0.35, defense=0.0)

def battle(good_unit: Unit, bad_unit: Unit):
    turns = 0
    good_start = good_unit.num_people
    bad_start = bad_unit.num_people

    while good_unit.num_people > 0 and bad_unit.num_people > 0:
        turns += 1
        # Good attacks
        damage = good_unit.num_people * max(0, good_unit.lethality - bad_unit.defense)
        bad_unit.num_people -= int(damage)
        bad_unit.num_people = max(0, bad_unit.num_people)
        if bad_unit.num_people == 0:
            break

        # Bad attacks
        damage = bad_unit.num_people * max(0, bad_unit.lethality - good_unit.defense)
        good_unit.num_people -= int(damage)
        good_unit.num_people = max(0, good_unit.num_people)

    # Prepare battle results as a dictionary
    battle_result = {
        "turns": turns,
        "good_unit_losses": good_start - good_unit.num_people,
        "bad_unit_losses": bad_start - bad_unit.num_people,
        "good_unit_remaining": good_unit.num_people,
        "bad_unit_remaining": bad_unit.num_people,
        "good_unit_eliminated": good_unit.num_people == 0,
        "good_unit_exiting": good_unit.num_people <= 30,
    }

    # Update the good unit's state if necessary
    if good_unit.num_people <= 30:
        good_unit.exiting = True

    return battle_result
