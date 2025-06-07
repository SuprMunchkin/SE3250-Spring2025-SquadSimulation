import numpy as np
from math import cos, sin, radians, dist
import os
import yaml

# Load config (if needed for armor_profiles)
yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
armor_profiles = config["armor_profiles"]
map_size = config["map_size"]

def move(start, distance, direction, bound=map_size):
    x = start[0]
    y = start[1]
    x += distance * cos(radians(direction))
    y += distance * sin(radians(direction))
    x = np.clip(x, 0, bound)
    y = np.clip(y, 0, bound)
    end = (x, y)
    travel = dist(start, end)
    return end, travel

class Patrol:
    def __init__(self, params):
        self.stock = params['blue_stock']
        self.current_position = (np.random.uniform(0, map_size), np.random.uniform(0, map_size))
        self.direction = np.random.uniform(0, 360)
        # Directly initialize exhaustion_data here
        armor = params['armor_type']
        squad_size = params['blue_stock']
        if armor not in armor_profiles:
            raise ValueError(f"Armor type '{armor}' not found in armor profiles.")
        self.exhaustion_data = []
        for _ in range(squad_size):
            soldier_mass = np.random.normal(76.6571, 11.06765)
            soldier_load = 20.6497926 + armor_profiles[armor]['Mass']
            self.exhaustion_data.append({
                'soldier': soldier_mass,
                'load': soldier_load,
                'joules_expended': 0, 
                'exhaustion_level': 0
            })
        self.spawn_time = 0
        self.removal_time = float('inf')
        self.position_history = [self.current_position]
        self.stock_history = [(self.stock, 0)]
        self.total_energy = 0
        self.patrol_time = 0
        self.patrol_distance = 0
        self.shots = 0
        self.kills = 0
        self.exhaustion = 0

    def move(self, move_distance, deviation):
        self.direction = (self.direction + np.random.uniform(-deviation, deviation)) % 360
        new_position, traveled = move(self.current_position, move_distance, self.direction, bound=map_size)
        # Edge bounce logic
        x, y = new_position
        bounced = False
        if x <= 0:
            self.direction = 0 + np.random.uniform(-deviation, deviation)
            bounced = True
        elif x >= map_size:
            self.direction = 180 + np.random.uniform(-deviation, deviation)
            bounced = True
        if y <= 0:
            self.direction = 90 + np.random.uniform(-deviation, deviation)
            bounced = True
        elif y >= map_size:
            self.direction = 270 + np.random.uniform(-deviation, deviation)
            bounced = True
        if bounced:
            # Optionally, move again in the new direction to avoid sticking to the edge
            new_position, traveled = move(self.current_position, move_distance, self.direction, bound=map_size)
        self.patrol_distance += traveled
        self.current_position = new_position
        self.position_history.append(new_position)
        return traveled

    def update_patrol_time(self, sim_time):
        self.patrol_time = sim_time - self.spawn_time

    def log_stock(self, sim_time):
        self.stock_history.append((self.stock, sim_time))

    def to_dict(self, full_log=True):
        pos_hist = [list(pos) for pos in self.position_history] if full_log else [list(self.position_history[0]), list(self.position_history[-1])]
        stock_hist = [list(stock) for stock in self.stock_history]
        return {
            'stock': self.stock,
            'current_position': list(self.current_position),
            'direction': self.direction,
            'exhaustion_data': self.exhaustion_data,
            'spawn_time': self.spawn_time,
            'removal_time': self.removal_time,
            'position_history': pos_hist,
            'stock_history': stock_hist,
            'total_energy': self.total_energy,
            'patrol_time': self.patrol_time,
            'patrol_distance': self.patrol_distance,
            'shots': self.shots,
            'kills': self.kills,
            'exhaustion': self.exhaustion
        }

    def set_exhaustion(self, move_speed):
        """
        Updates the exhaustion state for the patrol and returns True if exhaustion threshold is reached.
        """
        # Calculate exhaustion threshold based on patrol time (in minutes)
        patrol_time = self.patrol_time
        exhaustion_threshold = max(0, (
            -0.0841 * (patrol_time/60)**4 + 2.9025*(patrol_time/60)**3 -
            41.059*(patrol_time/60)**2 + 195.14*(patrol_time/60) + 294.05
        ))

        data = self.exhaustion_data
        speed = move_speed
        grade = np.random.normal(0, 6)  # Random terrain factor (0 to 6)
        eta = 1  # Energy expenditure factor
        D = 1 if grade < 0 else 0

        for soldier in data:
            mass = soldier['soldier']
            load = soldier['load']
            # Pandolf-Santee equation (Watts)
            P = (
                1.5 * mass +
                2.0 * (mass + load) * (load / mass)**2 +
                eta * (mass + load) * (1.5 * speed**2 + 0.35 * speed * grade) -
                D * eta * (
                    (grade * speed * (mass + load) / 3.5) -
                    ((mass + load) * (grade + 6)**2 / mass) +
                    (25 - speed**2)
                )
            )
            energy_expended = P * 60
            soldier['joules_expended'] += energy_expended
            average_power_output = energy_expended / (patrol_time * 60) if patrol_time > 0 else 0
            soldier['exhaustion_level'] = average_power_output / exhaustion_threshold if exhaustion_threshold > 0 else 0

        self.exhaustion = np.mean([s['exhaustion_level'] for s in data])
        # Return True if patrol is exhausted
        return self.exhaustion >= exhaustion_threshold

    def step(self, dt, deviation, map_size):
        # Update direction with deviation
        self.direction = (self.direction + np.random.uniform(-deviation, deviation)) % 360
        # Calculate move speed and distance
        move_speed = np.random.uniform(0.5, 1.4)
        move_distance = move_speed * dt * 60
        # Move and update position
        traveled = self.move(move_distance, deviation)
        return move_speed, move_distance, traveled

    def bounce_if_at_edge(self, map_size, deviation):
        if self.current_position[0] == 0:
            self.direction = 0 + np.random.uniform(-deviation, deviation)
        elif self.current_position[0] == map_size:
            self.direction = 180 + np.random.uniform(-deviation, deviation)
        if self.current_position[1] == 0:
            self.direction = 90 + np.random.uniform(-deviation, deviation)
        elif self.current_position[1] == map_size:
            self.direction = 270 + np.random.uniform(-deviation, deviation)