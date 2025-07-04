import numpy as np
from math import dist

# Configure logging
import logging
import pprint
pp = pprint.PrettyPrinter(indent=4)
logging.basicConfig(
    filename='simulation.log',        # Log file name
    level=logging.INFO,               # Log level (INFO, DEBUG, etc.)
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Open config file
import os
import yaml
yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
armor_profiles = config["armor_profiles"]
map_size = config["map_size"]
terrain_library = config["terrain_library"]

class Patrol:
    def __init__(self, params, full_log=True):
        global map_size
        self.full_log = full_log
        map_size = params.get("map_size", map_size)
        self.current_position = [
            np.random.uniform(0, map_size), 
            np.random.uniform(0, map_size)
        ]
        self.position_history = [self.current_position]
        self.direction = np.random.uniform(0, 360)
        self.move_speed = 0 # m/dt
        self.spawn_time = 0
        self.removal_time = float('inf')
        self.patrol_time = 0
        self.patrol_distance = 0
        self.shots = 0
        self.hostiles_killed = 0
        self.terrain_change_interval = np.random.randint(10)
        self.terrain_change_counter = 0
        self.current_terrain = np.random.choice(list(terrain_library.keys()))
        self.terrain_history = [self.current_terrain]
        self.grade = np.random.normal(0, 3)
        armor = params['armor_type']
        if armor not in armor_profiles:
            raise ValueError(f"Armor type '{armor}' not found in armor profiles.")
        self.squad_exhaustion = 0
        self.squad_data = []  # Stores data for active soldiers
        for _ in range(params['blue_stock']):
            soldier_mass = np.random.normal(76.6571, 11.06765)
            soldier_load = 20.6497926 + armor_profiles[armor]['Mass'] # Base Combat Load (kg) (Fish and Scharre, 2018, p. 13)
            self.squad_data.append({
                'soldier': soldier_mass,
                'load': soldier_load,
                'joules_expended': 0, 
                'exhaustion_level': 0,
                'removal_time': None,
                'exhausted': False,
                'Killed': False
            })
        self.casualties = []    #stores the data for dead and exhausted soldiers
        self.stock_history = [[self.get_stock(), 0]]
        self.exhaustion_data = [[s['exhaustion_level'] for s in self.squad_data]]

    def move(self, move_distance, deviation):
        
        self.direction = (self.direction + np.random.uniform(-deviation, deviation)) % 360
        traveled = move_distance
        x = self.current_position[0] + move_distance * np.cos(np.radians(self.direction))
        y = self.current_position[1] + move_distance * np.sin(np.radians(self.direction))
        x = np.clip(x, 0, map_size)
        y = np.clip(y, 0, map_size)
        new_position = [x,y]
        traveled = dist(self.current_position, new_position)

        # Edge bounce logic
        bounced = False
        if x <= 0:
            logging.debug(f"Bounce off west wall at {new_position}")
            self.direction = 0 + np.random.uniform(-deviation, deviation)
            bounced = True
        elif x >= map_size:
            logging.debug(f"Bounce off east wall at {new_position}")
            self.direction = 180 + np.random.uniform(-deviation, deviation)
            bounced = True

        # Catches the edge case when the patrol is directly on a corner.
        if bounced: 
            if y <= 0:
                logging.debug(f"Bounce off south-west corner at {new_position}")
                self.direction = 45 + np.random.uniform(-deviation, deviation)
            elif y >= map_size:
                logging.debug(f"Bounce off north-east corner at {new_position}")
                self.direction = 225 + np.random.uniform(-deviation, deviation)
        else:
            if y <= 0:
                logging.debug(f"Bounce off south wall at {new_position}")
                self.direction = 90 + np.random.uniform(-deviation, deviation)
                bounced = True
            elif y >= map_size:
                logging.debug(f"Bounce off north wall at {new_position}")
                self.direction = 270 + np.random.uniform(-deviation, deviation)
                bounced = True

        if bounced:
            # Move again in the new direction to use the full move distance.
            x = self.current_position[0] + (move_distance-traveled) * np.cos(np.radians(self.direction))
            y = self.current_position[1] + (move_distance-traveled) * np.sin(np.radians(self.direction))
            x = np.clip(x, 0, map_size)
            y = np.clip(y, 0, map_size)
            traveled += dist(new_position, [x,y])

        new_position = [float(x), float(y)]
        self.patrol_distance += traveled
        self.move_speed = traveled 
        self.current_position = new_position
        self.position_history.append(new_position)
        self._update_terrain()
        return

    def update_patrol_time(self, sim_time):
        self.patrol_time = sim_time - self.spawn_time

    def get_stock(self):
        return int(len(self.squad_data))
    
    def take_casualties(self, casualties, sim_time):
        list_survivors = self.squad_data[casualties:]
        list_casulties = self.squad_data[:casualties]
        for soldier in list_casulties:
            soldier['removal_time'] = sim_time
        self.squad_data = list_survivors
        self.casualties.extend(list_casulties)
        self.stock_history.append([self.get_stock(), sim_time])
        return

    def to_dict(self, full_log=True):
        pos_hist = [list(pos) for pos in self.position_history] if full_log else [list(self.position_history[0]), list(self.position_history[-1])]
        stock_hist = [list(stock) for stock in self.stock_history]
        return {
            'stock': self.get_stock(),
            'current_position': list(self.current_position),
            'direction': self.direction,
            'spawn_time': self.spawn_time,
            'removal_time': self.removal_time,
            'position_history': pos_hist,
            'stock_history': stock_hist,
            'exhaustion_data': self.exhaustion_data,
            'patrol_time': self.patrol_time,
            'patrol_distance': self.patrol_distance,
            'shots': self.shots,
            'hostiles_killed': self.hostiles_killed,
            'exhaustion': self.squad_exhaustion
        }

    def set_exhaustion(self):
        """
        Updates the exhaustion state for the patrol.
        """
        # Calculate exhaustion threshold based on patrol time (in minutes)
        data = self.squad_data
        speed = self.move_speed 
        terrain_factor = terrain_library[self.current_terrain][0]
        grade = self.grade
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


        exhaustion_data = [s['exhaustion_level'] for s in data]
        exhaustion_data.insert(0, self.get_exhaustion_threshold())
        if self.full_log:
            self.exhaustion_data.append(exhaustion_data)
        self.squad_exhaustion = float(np.mean(exhaustion_data))
        return 
  
    def get_exhaustion_threshold(self):
        """
        Calculate the exhaustion threshold based on the patrol time.
        """
        patrol_time = ( self.patrol_time / 60 ) # Convert to hours
        power_max = 715.0154 * (patrol_time) ** -0.3869002
        return power_max 

    def is_exhausted(self):
        """
        Check if the patrol is exhausted based on the exhaustion level.
        """
        return self.squad_exhaustion >= self.get_exhaustion_threshold()

    def step(self, deviation):
        self.direction = (self.direction + np.random.uniform(-deviation, deviation)) % 360
        # Calculate move speed and distance. Adjust speed based on terrain factor
        move_speed = np.random.uniform(0.8, 1.4) / terrain_library[self.current_terrain][0]  
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
        self.grade = np.random.normal(0, 3)
        if self.terrain_change_counter >= self.terrain_change_interval:
            terrain_roll = np.random.randint(1, 101)
            for terrain_name, values in terrain_library.items():
                prob = int(values[1] * 100)
                if terrain_roll <= prob :
                    self.current_terrain = terrain_name
                    logging.debug(f"changing terrain to: {terrain_name} based on roll: {float(terrain_roll)} < prob: {prob}")
                    break
                else:
                    terrain_roll -= prob
            self.terrain_change_counter = 0
            self.terrain_change_interval = np.random.randint(10)

        self.terrain_change_counter += 1    
        if self.full_log:
            self.terrain_history.append(self.current_terrain)
