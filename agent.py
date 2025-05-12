import matplotlib.pyplot as plt
from random import uniform, choice, randint, random
import ipywidgets as widgets
from IPython.display import display, clear_output

class GoodUnit:
    def __init__(self, armor, energy, num_people):
        self.armor = armor
        self.energy = energy
        self.num_people = num_people
        self.history = []
        self.visited = set()
        self.move_counter = 0
        self.lethality = 0.90
        self.defense = 0.0
        self._adjust_for_armor()
        self._start_at_random_edge()
        self.exiting = False  # flag for exit mode

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

    def _start_at_random_edge(self):
        edge = choice(['left', 'right', 'top', 'bottom'])
        if edge == 'left':
            self.x = 0
            self.y = uniform(0, 1)
        elif edge == 'right':
            self.x = 1
            self.y = uniform(0, 1)
        elif edge == 'top':
            self.x = uniform(0, 1)
            self.y = 1
        else:
            self.x = uniform(0, 1)
            self.y = 0
        self.history.append((self.x, self.y))
        self.visited.add((self.x, self.y))

    def _get_closest_edge_point(self):
        distances = {
            (0, self.y): self.x,
            (1, self.y): 1 - self.x,
            (self.x, 0): self.y,
            (self.x, 1): 1 - self.y
        }
        return min(distances, key=distances.get)

    def _update_lethality(self):
        if self.energy > 0 and self.water > 0:
            self.lethality = 0.55
        elif self.energy > 0 or self.water > 0:
            self.lethality = 0.35
        else:
            self.lethality = 0.15

    def move(self):
        if self.energy <= 0 or self.exiting:
            target_x, target_y = self._get_closest_edge_point()
            dx = 0.05 if target_x > self.x else -0.05 if target_x < self.x else 0
            dy = 0.05 if target_y > self.y else -0.05 if target_y < self.y else 0

            self.x = min(max(self.x + dx, 0), 1)
            self.y = min(max(self.y + dy, 0), 1)

            self.history.append((self.x, self.y))
            self.visited.add((self.x, self.y))
            self.move_counter += 1
            self._update_lethality()

            return not (self.x in (0, 1) or self.y in (0, 1))

        directions = [(-0.05, 0), (0.05, 0), (0, -0.05), (0, 0.05)]
        possible_moves = []

        for dx, dy in directions:
            new_x = self.x + dx
            new_y = self.y + dy
            if 0 <= new_x <= 1 and 0 <= new_y <= 1:
                possible_moves.append((new_x, new_y))

        unvisited = [move for move in possible_moves if move not in self.visited]
        move_choices = unvisited if unvisited else possible_moves

        if not move_choices:
            return False

        self.x, self.y = choice(move_choices)
        self.history.append((self.x, self.y))
        self.visited.add((self.x, self.y))
        self.move_counter += 1

        self.water -= 0.01 * self.move_counter * self.num_people
        self.energy -= self.energy_depletion_factor * self.move_counter

        if self.water <= 0:
            self.water = 0
            self.energy -= 0.1

        if self.energy <= 0:
            self.energy = 0

        self._update_lethality()
        return True

class BadUnit:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.num_people = randint(30, 50)
        self.lethality = 0.35
        self.defense = 0.0

def battle(good_unit, bad_unit):
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

    battle_result = f"\n🛡️ Battle Summary:\n"
    battle_result += f" - Turns: {turns}\n"
    battle_result += f" - Good Unit Losses: {good_start - good_unit.num_people}\n"
    battle_result += f" - Bad Unit Losses: {bad_start - bad_unit.num_people}\n"

    if good_unit.num_people == 0:
        battle_result += "\n❌ The good unit has been eliminated!"
    elif good_unit.num_people <= 30:
        good_unit.exiting = True
    return battle_result

# Simulation runner
def run_simulation(armor, energy, num_people):
    unit = GoodUnit(armor, energy, num_people)
    bad_units = []
    battle_results = ""

    while True:
        # Move the good unit
        if not unit.move():
            break

        # 5% chance to spawn bad unit
        if random() <= 0.05:
            bad = BadUnit(unit.x, unit.y)
            bad_units.append(bad)
            battle_results += battle(unit, bad)  # Append battle results

            if not unit.num_people > 0:  # Good unit lost
                break

    # Print all battle summaries
    clear_output(wait=True)  # Clear previous outputs
    print(battle_results)  # Print all battle results

    # Plot the simulation path
    x_vals, y_vals = zip(*unit.history)
    plt.figure(figsize=(8, 8))
    plt.plot(x_vals, y_vals, 'bo-', markersize=4, alpha=0.7, label="Good Unit Path")

    if bad_units:
        bad_x = [b.x for b in bad_units]
        bad_y = [b.y for b in bad_units]
        plt.plot(bad_x, bad_y, 'rx', markersize=10, label="Bad Units")

    plt.title(f"Good Unit Path - Moves: {unit.move_counter}")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)
    plt.legend()
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.show()

    print(f"Total Moves: {unit.move_counter}")
    print(f"Unit Size (Remaining): {unit.num_people}")
    print(f"Final Energy: {unit.energy:.2f}")
    print(f"Final Water: {unit.water:.2f}")
    print(f"Lethality: {unit.lethality:.2f}")
    print(f"Defense: {unit.defense:.2f}")
    print(f"Bad Units Spawned: {len(bad_units)}")

# UI Widgets
armor_options = ['Light', 'Medium', 'Heavy']
armor_widget = widgets.Dropdown(options=armor_options, value='Light', description='Armor:')
energy_widget = widgets.FloatSlider(value=100, min=10, max=100, step=1, description='Energy:')
people_widget = widgets.IntSlider(value=5, min=30, max=50, step=1, description='People:')
run_button = widgets.Button(description="Run Simulation")
output = widgets.Output()

def on_button_click(b):
    with output:
        run_simulation(armor_widget.value, energy_widget.value, people_widget.value)

run_button.on_click(on_button_click)

# Display interface
display(armor_widget, energy_widget, people_widget, run_button, output)
