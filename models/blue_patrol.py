import numpy as np
from math import cos, sin, radians, dist
import os
import yaml

# Load config
yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
armor_profiles = config["armor_profiles"]
map_size = config["map_size"]
terrain_library = config["terrain_library"]

class Patrol:
    def __init__(self, params, full_log=True):
        self.full_log = full_log
        self.stock = params['blue_stock']
        self.stock_history = [(self.stock, 0)]
        self.current_position = (np.random.uniform(0, map_size), np.random.uniform(0, map_size))
        self.position_history = [self.current_position]
        self.direction = np.random.uniform(0, 360)
        self.move_speed = 0 # m/dt
        self.spawn_time = 0
        self.removal_time = float('inf')
        self.patrol_time = 0
        self.patrol_distance = 0
        self.shots = 0
        self.kills = 0
        self.terrain_change_interval = np.random.randint(1, 11)
        self.terrain_change_counter = 0
        self.current_terrain = np.random.choice(list(terrain_library.keys()))
        self.terrain_history = [self.current_terrain]
        armor = params['armor_type']
        if armor not in armor_profiles:
            raise ValueError(f"Armor type '{armor}' not found in armor profiles.")
        self.squad_exhaustion = 0
        self.squad_data = []
        for _ in range(self.stock):
            soldier_mass = np.random.normal(76.6571, 11.06765)
            soldier_load = 20.6497926 + armor_profiles[armor]['Mass'] # Base Combat Load (kg) (Fish and Scharre, 2018, p. 13)
            self.squad_data.append({
                'soldier': soldier_mass,
                'load': soldier_load,
                'joules_expended': 0, 
                'exhaustion_level': 0
            })
        self.exhaustion_data = []

    def move(self, move_distance, deviation):
        self.direction = (self.direction + np.random.uniform(-deviation, deviation)) % 360
        # Calculate new position
        x = self.current_position[0] + move_distance * np.cos(np.radians(self.direction))
        y = self.current_position[1] + move_distance * np.sin(np.radians(self.direction))
        x = np.clip(x, 0, map_size)
        y = np.clip(y, 0, map_size)
        new_position = (x, y)
        traveled = dist(self.current_position, new_position)
        # Edge bounce logic
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
            # Move again in the new direction to use the full move distance.
            x = self.current_position[0] + move_distance * np.cos(np.radians(self.direction))
            y = self.current_position[1] + move_distance * np.sin(np.radians(self.direction))
            x = np.clip(x, 0, map_size)
            y = np.clip(y, 0, map_size)
            new_position = (x, y)
            traveled += dist(self.current_position, new_position)
        self.patrol_distance += traveled
        self.move_speed = traveled 
        self.current_position = new_position
        self.position_history.append(new_position)
        self._update_terrain()
        return

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
            'exhaustion_data': self.squad_data,
            'spawn_time': self.spawn_time,
            'removal_time': self.removal_time,
            'position_history': pos_hist,
            'stock_history': stock_hist,
            'exhaustion_data': self.squad_data,
            'patrol_time': self.patrol_time,
            'patrol_distance': self.patrol_distance,
            'shots': self.shots,
            'kills': self.kills,
            'exhaustion': self.squad_exhaustion
        }

    def set_exhaustion(self):
        """
        Updates the exhaustion state for the patrol.
        """
        # Calculate exhaustion threshold based on patrol time (in minutes)
        data = self.squad_data
        speed = self.move_speed
        grade = np.random.normal(0, 6) 
        terrain_factor = terrain_library[self.current_terrain][0] # Terrain factor from the library
        downhill_adjustment = 1 if grade < 0 else 0 

        for soldier in data:
            mass = soldier['soldier']
            load = soldier['load']
            # Pandolf-Santee equation (Watts)
            P = (
                1.5 * mass +
                2.0 * (mass + load) * (load / mass)**2 +
                terrain_factor * (mass + load) * (1.5 * speed**2 + 0.35 * speed * grade) -
                downhill_adjustment * terrain_factor * (
                    (grade * speed * (mass + load) / 3.5) -
                    ((mass + load) * (grade + 6)**2 / mass) +
                    (25 - speed**2)
                )
            )
            energy_expended = P * 60
            soldier['joules_expended'] += energy_expended

            # The 60x is to convert the output to Joules per hour
            average_power_output = ( soldier['joules_expended'] * 60 ) / (self.patrol_time) if self.patrol_time > 0 else 0
            
            # Next we have to convert to Kcal to compare against the exhaustion level.
            average_power_output = average_power_output / 4184

            exhaustion_threshold = self.get_exhaustion_threshold()
            soldier['exhaustion_level'] = average_power_output / exhaustion_threshold if exhaustion_threshold > 0 else 0

        
        self.squad_exhaustion = np.mean([s['exhaustion_level'] for s in data])
        # TODO : Add logic to record exhaustion data if not full_log.
        if self.full_log:
            self.exhaustion_data.append(self.squad_exhaustion)
        return 
  
    def get_exhaustion_threshold(self):
        """
        Calculate the exhaustion threshold based on the patrol time.
        """
        patrol_time = self.patrol_time / 60 # Convert to hours
        P_MAX = 715.0154 * (patrol_time) ** -0.3869002
        return P_MAX 

    def is_exhausted(self):
        """
        Check if the patrol is exhausted based on the exhaustion level.
        """
        return self.squad_exhaustion >= self.get_exhaustion_threshold()

    def step(self, deviation):
        self.direction = (self.direction + np.random.uniform(-deviation, deviation)) % 360
        # Calculate move speed and distance. Adjust speed based on terrain factor
        move_speed = np.random.uniform(0.5, 1.4) / terrain_library[self.current_terrain][0]  
        # Adjust speed based on exhaustion level
        move_speed *= ( 1 - ( self.squad_exhaustion / (2 * self.get_exhaustion_threshold()) ) )
        # Multiply by 60 to convert to meters per minute because the simulation runs in minutes.
        # Speed has to remain in meters per second for the exhaustion calculations.
        move_distance = move_speed * 60
        self.move(move_distance, deviation)
        return

    def _update_terrain(self):
        """
        Change the terrain type for the patrol.
        """
        self.terrain_change_counter += 1
        if self.terrain_change_counter >= self.terrain_change_interval:
            terrain_roll = np.random.randint(1, 101)
            for terrain_name, values in terrain_library.items():
                if values[1] <= terrain_roll:
                    self.current_terrain = terrain_name
                    break

        self.terrain_change_counter = 0
        self.terrain_change_interval = np.random.randint(1, 11)
        if self.full_log:
            self.terrain_history.append(self.current_terrain)
