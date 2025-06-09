import numpy as np
import pandas as pd
from math import cos, sin, radians, exp, dist
import yaml
import os
import sys
from .blue_patrol import Patrol

yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
 
threat_library = config["threat_library"]
armor_profiles = config["armor_profiles"]
threat_probs = config["threat_probs"]
terrain_library = config["terrain_library"]
fire_rates = config["fire_rates"]
map_size = config["map_size"]
stop_time = config["stop_time"]

 
# This is for projectile velocity calculation, not the patrol velocity.
def _projectile_velocity(threat, distance):
    c1, c2, c3 = threat_library[threat]
    return c1 * distance**2 + c2 * distance + c3

def _get_defeat_probability(armor, threat, velocity):
    beta0, beta1 = armor_profiles[armor][threat]
    exponent = beta0 + velocity * beta1
    return np.exp(exponent) / (1 + np.exp(exponent))

def _attack(blue_patrol, red_patrol, env, armor, distance):
    # Blue shots
    blue_shots = np.random.randint(fire_rates["blue_min"], fire_rates["blue_max"] + 1) * blue_patrol.get_stock()
    prob_blue_hit = exp(-0.002 * distance)
    blue_hits = sum(np.random.random() < prob_blue_hit for _ in range(blue_shots))
    if env == 'Krulak’s Three Block War':
        red_kills = min(red_patrol['stock'], blue_hits)
    elif env == 'Pershing’s Ghost':
        red_kills = min(red_patrol['stock'], sum(np.random.normal(0.75, 0.05) > np.random.random() for _ in range(blue_hits)))
    elif env == 'Nightmare from Mattis Street':
        red_kills = min(red_patrol['stock'], sum(np.random.normal(0.25, 0.05) > np.random.random() for _ in range(blue_hits)))
    else:
        # Unknown env? treat it as the easiest. Need to figure out a way to throw an exception here.
        red_kills = min(red_patrol['stock'], blue_hits)
        
    # red shots
    red_shots = np.random.randint(fire_rates["red_min"], fire_rates["red_max"] + 1) * red_patrol['stock']
    red_threat = np.random.choice(list(threat_probs[env].keys()), p=list(threat_probs[env].values()))
    red_velocity = _projectile_velocity(red_threat, distance)
    prob_red_hit = exp(-0.002 * distance)
    red_hits = sum(np.random.random() < prob_red_hit for _ in range(red_shots))
    red_defeats = sum(np.random.random() < _get_defeat_probability(armor, red_threat, red_velocity) for _ in range(red_hits))
    blue_kills = min(blue_patrol.get_stock(), red_defeats)

    # Return shots and kills for both sides
    return {
        'blue_kills': blue_kills,
        'red_kills': red_kills,
        'blue_shots': blue_shots,
        'red_shots': red_shots
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

def spawn_red_patrol(params, sim_time):
    """ Spawns a red patrol at a random position on the map with the given stock.
    Args:
        params (dict): Simulation parameters including red stock.
    Returns:
        dict: A dictionary representing the red patrol with its stock and position."""
    return {
        'stock': params['red_stock'],
        'current_position': (np.random.uniform(0, map_size), np.random.uniform(0, map_size)),
        'stock_history': [(params['red_stock'], 0)],
        'spawn_time': sim_time,
        'removal_time': None,
        'shots': 0,
        'kills': 0,
    }

def run_simulation(params, full_log=True):
    """ Simulates a patrol operation between blue and red forces on a terrain defined by the map_size parmeter. 
    Origin is at the bottom left corner, direction 0 is to the right and rotates counter-clockwise.
    Args:
        params (dict): Simulation parameters including blue and red stock, environment, armor type, and direction deviation.
        full_log (bool): Whether the return dictionary contains the full position history or just total distance traveled. 
            True allows plotting the path of the squad on a map for visualization.
            False is less memory intensive and faster for multiple iterations (i.e. Monte Carlo simulations)
            Defaults to True. 
    Returns:
        dict: A dictionary containing the simulation results."""

    sim_time = 0
    dt = 1

    red_patrols = [spawn_red_patrol(params, sim_time)]

    blue_patrol = Patrol(params, full_log)

    blue_patrol.position_history.append((blue_patrol.current_position))
    blue_patrol.stock_history.append((blue_patrol.get_stock(), 0))

    combat_log = []

    # Simulate patrol movement and combat
    while sim_time < stop_time and blue_patrol.get_stock() > 0 and red_patrols[0]['stock'] > 0:
        sim_time += dt
        blue_patrol.patrol_time = sim_time - blue_patrol.spawn_time

        deviation = params['direction_deviation']
        blue_patrol.step(deviation)

        #Combat section
        distance_to_enemy = dist(blue_patrol.current_position, red_patrols[0]['current_position'])
        if distance_to_enemy != 0:
            prob_attack = 1 / np.sqrt(distance_to_enemy)
        else:
            prob_attack = 1

        if distance_to_enemy <= 1000 and np.random.random() < prob_attack:
            attack_result = _attack(
                blue_patrol, red_patrols[0], params['environment'],
                params['armor_type'], distance_to_enemy
            )
            blue_patrol.set_stock(blue_patrol.get_stock()- attack_result['blue_kills'], sim_time)
            red_patrols[0]['stock'] -= attack_result['red_kills']
            blue_patrol.kills += attack_result['blue_kills']
            red_patrols[0]['kills'] += attack_result['red_kills']
            blue_patrol.shots = attack_result['blue_shots']
            red_patrols[0]['shots'] = attack_result['red_shots']
            # set_stock logs the stock history, so we don't need to do it here.
            red_patrols[0]['stock_history'].append((red_patrols[0]['stock'], sim_time))

            if blue_patrol.get_stock() <= 0:
                blue_patrol.removal_time = sim_time
                break # Blue patrol is defeated, end simulation
            if red_patrols[0]['stock'] <= 0:
                red_patrols[0]['removal_time'] = sim_time
                red_patrols.insert(0, spawn_red_patrol(params, sim_time)) 
            if full_log:
                # Log all details of this combat event
                combat_log.append({
                    'combat_time': sim_time,
                    'blue_shots': attack_result['blue_shots'],
                    'red_shots': attack_result['red_shots'],
                    'blue_kills': attack_result['blue_kills'],
                    'red_kills': attack_result['red_kills'],
                    'blue_position': list(blue_patrol.current_position),
                    'red_position': list(red_patrols[0]['current_position']),
                    'distance': distance_to_enemy
                })
        else:
            # Exhaustion checks only happen if the patrol is not engaged in combat.
            blue_patrol.set_exhaustion()
            if blue_patrol.is_exhausted():
                blue_patrol.removal_time = sim_time
                break # Blue patrol is exhausted, end simulation
        
    
    # Convert all tuples to lists for JSON serialization
    blue_patrol.position_history = [list(pos) for pos in blue_patrol.position_history]
    blue_patrol.stock_history = [list(stock) for stock in blue_patrol.stock_history]
    for patrol in red_patrols:
        patrol['stock_history'] = [list(stock) for stock in patrol['stock_history']]
        patrol['current_position'] = list(patrol['current_position'])

    result = {
        'blue': blue_patrol.to_dict(full_log=full_log),
        'red': red_patrols[0],
        'red_patrols': red_patrols,
        'combat_log': combat_log # will be empty if full_log is False.
    }

    return make_json_safe(result)

