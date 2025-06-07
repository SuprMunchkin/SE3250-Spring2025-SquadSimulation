import numpy as np
import pandas as pd
from math import cos, sin, radians, exp, dist
import yaml
import os
import sys

yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
 
threat_library = config["threat_library"]
armor_profiles = config["armor_profiles"]
threat_probs = config["threat_probs"]
fire_rates = config["fire_rates"]
map_size = config["map_size"]
stop_time = config["stop_time"] 
 
# This is for projectile velocity calculation, not the patrol velocity.
def _get_velocity(threat, distance):
    c1, c2, c3 = threat_library[threat]
    return c1 * distance**2 + c2 * distance + c3
 
def _get_defeat_probability(armor, threat, velocity):
    beta0, beta1 = armor_profiles[armor][threat]
    exponent = beta0 + velocity * beta1
    return np.exp(exponent) / (1 + np.exp(exponent))
 
def _move(start, distance, direction, bound=map_size):
    """Moves a point a certain distance in a given direction and records the position and distance traveled.
    Does not allow the point to leave an area defined by the bound parameter, which defaults to the global variable: map_size.
    Args:
        location (float, float): starting location, coordinates should be in (x,y) format.
        distance (float): The distance to move the patrol.
        direction (float): The direction to move the patrol in degrees. 0 degrees is to the right and the degrees rotate counter-clockwise.
        bound (int): Maximum value each coordinate can take. Defaults to a global variable.
    Retruns
        end (float, float): The end position of the point.
        travel (float): The distance the point traveled.
    """
    x = start[0]
    y = start[1]
    
    x += distance * cos(radians(direction))
    y += distance * sin(radians(direction))
    x = np.clip(x, 0, map_size)
    y = np.clip(y, 0, map_size)

    end = (x,y)
    travel = dist(start, end) 

    return end, travel
 
 
def _attack(blue_patrol, hostile_patrol, env, armor, distance):
    # Blue shots
    blue_shots = np.random.randint(fire_rates["blue_min"], fire_rates["blue_max"] + 1) * blue_patrol['stock']
    prob_blue_hit = exp(-0.002 * distance)
    blue_hits = sum(np.random.random() < prob_blue_hit for _ in range(blue_shots))
    hostile_kills = min(hostile_patrol['stock'], sum(np.random.normal(0.75, 0.05) > np.random.random() for _ in range(blue_hits)))

    # Hostile shots
    hostile_shots = np.random.randint(fire_rates["hostile_min"], fire_rates["hostile_max"] + 1) * hostile_patrol['stock']
    hostile_threat = np.random.choice(list(threat_probs[env].keys()), p=list(threat_probs[env].values()))
    hostile_velocity = _get_velocity(hostile_threat, distance)
    prob_hostile_hit = exp(-0.002 * distance)
    hostile_hits = sum(np.random.random() < prob_hostile_hit for _ in range(hostile_shots))
    hostile_defeats = sum(np.random.random() < _get_defeat_probability(armor, hostile_threat, hostile_velocity) for _ in range(hostile_hits))
    blue_kills = min(blue_patrol['stock'], hostile_defeats)

    # Return shots and kills for both sides
    return {
        'blue_kills': blue_kills,
        'hostile_kills': hostile_kills,
        'blue_shots': blue_shots,
        'hostile_shots': hostile_shots
    }

def make_json_safe(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    if isinstance(obj, (list, tuple)):
        return [make_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, np.ndarray):
        return make_json_safe(obj.tolist())
    return obj
 
def run_simulation(params, map=True):
    """ Simulates a patrol operation between blue and hostile forces on a terrain defined by the map_size parmeter. 
    Origin is at the bottom left corner, direction 0 is to the right and rotates counter-clockwise.
    Args:
        params (dict): Simulation parameters including blue and hostile stock, environment, armor type, and direction deviation.
        Plot (bool): Whether the return dictionary contains the full position history or just total distance traveled. 
            True allows plotting the path of the squad on a map for visualization.
            False is less memory intensive and faster for multiple iterations (i.e. Monte Carlo simulations)
            Defaults to True. 
    Returns:
        dict: A dictionary containing the simulation results including patrol positions, stock history, and total kills."""

    sim_time = 0
    dt = 1

    blue_patrol = {
        'stock': params['blue_stock'],
        'current_position': (np.random.uniform(0, map_size), np.random.uniform(0, map_size)),
        'direction': np.random.uniform(0, 360),
        'm': np.random.normal(76.6571, 11.06765),
        'spawn_time': 0,
        'removal_time': float('inf'),
        'positions': [],
        'stock_history': [],
        'total_energy': 0,
        'patrol_time': 0,
        'patrol_distance': 0,
        'shots': 0,
        'kills': 0 
    }

    blue_patrol['positions'].append((blue_patrol['current_position']))
    blue_patrol['stock_history'].append(blue_patrol['stock'])

    hostile_patrol = {
        'stock': params['hostile_stock'],
        'current_position': (np.random.uniform(0, map_size), np.random.uniform(0, map_size)),
        'stock_history': [params['hostile_stock']],
        'spawn_time': 0,
        'removal_time': float('inf'),
        'shots': 0,
        'kills': 0,
    }

    combat_log = []

    # Simulate patrol movement and combat
    while sim_time < stop_time and blue_patrol['stock'] > 0 and hostile_patrol['stock'] > 0:
        sim_time += dt
        blue_position = (blue_patrol['current_position'])

        # Movement section
        deviation = params['direction_deviation']
        blue_patrol['direction'] = (blue_patrol['direction'] + np.random.uniform(-deviation, deviation)) % 360

        #TODO: implement v = velocity roll (from uniform distribution by terrain factor) x [1-(total_exhaustion_percentage / 2)]
        v = np.random.uniform(0.5, 1.4)
        move_distance = v * dt * 60
        blue_position, move_distance = _move(blue_position, move_distance, blue_patrol['direction'] )
        blue_patrol['patrol_distance'] += move_distance
        blue_patrol['current_position'] = blue_position
        if map:
            blue_patrol['positions'].append(blue_position)

        # This block "bounces" the patrols off the bounds of the area, to keep them from "sticking" to the edges.
        if blue_position[0] == 0:
            blue_patrol['direction'] = 0 + np.random.uniform(-deviation, deviation)
        elif blue_position[0] == map_size:
            blue_patrol['direction'] = 180 + np.random.uniform(-deviation, deviation)
        if blue_position[1] == 0:    
            blue_patrol['direction'] = 90 + np.random.uniform(-deviation, deviation)
        elif blue_position[1] == map_size:
            blue_patrol['direction'] = 270 + np.random.uniform(-deviation, deviation)

        #Combat section
        distance_to_enemy = dist(blue_patrol['current_position'], hostile_patrol['current_position'])
        if distance_to_enemy != 0:
            prob_attack = 1 / np.sqrt(distance_to_enemy)
        else:
            prob_attack = 1
        if distance_to_enemy <= 1000 and np.random.random() < prob_attack:
            attack_result = _attack(
                blue_patrol, hostile_patrol, params['environment'],
                params['armor_type'], distance_to_enemy
            )
            blue_patrol['stock'] -= attack_result['blue_kills']
            hostile_patrol['stock'] -= attack_result['hostile_kills']
            blue_patrol['kills'] += attack_result['blue_kills']
            hostile_patrol['kills'] += attack_result['hostile_kills']
            blue_patrol['shots'] = attack_result['blue_shots']
            hostile_patrol['shots'] = attack_result['hostile_shots']

            # Log this combat event
            combat_log.append({
                'combat_time': sim_time,
                'blue_shots': attack_result['blue_shots'],
                'hostile_shots': attack_result['hostile_shots'],
                'blue_kills': attack_result['blue_kills'],
                'hostile_kills': attack_result['hostile_kills'],
                'blue_position': list(blue_patrol['current_position']),
                'hostile_position': list(hostile_patrol['current_position']),
                'distance': distance_to_enemy
            })

            if blue_patrol['stock'] <= 0:
                blue_patrol['active'] = False
                blue_patrol['removal_time'] = sim_time

        blue_patrol['stock_history'].append(blue_patrol['stock'])
        hostile_patrol['stock_history'].append(hostile_patrol['stock'])
        
        blue_patrol['patrol_time'] += dt
        
    
    # Convert all positions to lists for JSON serialization
    blue_positions_list = [list(pos) for pos in blue_patrol['positions']]

    # Optionally, convert stock_history if needed
    blue_stock_history = list(blue_patrol['stock_history'])
    hostile_stock_history = list(hostile_patrol['stock_history'])
 
    # Prepare patrols for serialization
    blue_patrol_serializable = {
        **blue_patrol,
        'positions': blue_positions_list,
        'stock_history': blue_stock_history,
    }

    hostile_patrol_serializable = {
        **hostile_patrol,
        'stock_history': hostile_stock_history
    }
 
    result = {
        'blue': blue_patrol_serializable,
        'hostile': hostile_patrol_serializable,
        'blue_positions': blue_positions_list,   # Will only contain blue spawn position if plot=False.
        'combat_log': combat_log 
    }

    return make_json_safe(result)