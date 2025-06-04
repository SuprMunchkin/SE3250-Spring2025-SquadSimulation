import numpy as np
import pandas as pd
from math import cos, sin, radians, exp
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

def _get_velocity(threat, distance):
    c1, c2, c3 = threat_library[threat]
    return c1 * distance**2 + c2 * distance + c3

def _get_defeat_probability(armor, threat, velocity):
    beta0, beta1 = armor_profiles[armor][threat]
    exponent = beta0 + velocity * beta1
    return np.exp(exponent) / (1 + np.exp(exponent))

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

    return blue_kills, hostile_kills

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

def run_simulation(params):
    start_time = 0
    stop_time = 4320
    dt = 1
    time_steps = np.arange(start_time, stop_time + dt, dt)

    # Initialize blue and hostile patrols
    # The origin is in the bottom left corner, direction 0 is to the right and rotates counter-clockwise.
    blue_patrol = {
        'stock': params['blue_stock'],
        'x': np.random.uniform(0, 5000),
        'y': np.random.uniform(0, 5000),
        'direction': np.random.uniform(0, 360),
        'm': np.random.normal(76.6571, 11.06765),
        'spawn_time': 0,
        'removal_time': float('inf'),
        'positions': [],
        'stock_history': [],
        'direction_history': [],
        'total_energy': 0,
        'active': True,
        'patrol_time': 0
    }
    blue_patrol['positions'].append((blue_patrol['x'], blue_patrol['y']))
    blue_patrol['stock_history'].append(blue_patrol['stock'])
    blue_patrol['direction_history'].append(blue_patrol['direction'])

    hostile_patrol = {
        'stock': params['hostile_stock'],
        'x': np.random.uniform(0, 5000),
        'y': np.random.uniform(0, 5000),
        'positions': [],
        'stock_history': [params['hostile_stock']],
        'spawn_time': 0,
        'removal_time': float('inf')
    }
    hostile_patrol['positions'].append((hostile_patrol['x'], hostile_patrol['y']))

    total_blue_kills = 0
    total_hostile_kills = 0
    positions = []
    hostile_positions = []

    # Simulate patrol movement and combat
    for t in time_steps:
        if not blue_patrol['active'] or hostile_patrol['stock'] <= 0:
            break

        deviation = params['direction_deviation']
        
        blue_patrol['direction'] = (blue_patrol['direction'] + np.random.uniform(-deviation, deviation)) % 360
        blue_patrol['direction_history'].append(blue_patrol['direction'])

        v = np.random.uniform(0.5, 1.4)
        move_distance = v * dt * 60
        blue_patrol['x'] += move_distance * cos(radians(blue_patrol['direction']))
        blue_patrol['y'] += move_distance * sin(radians(blue_patrol['direction']))
        blue_patrol['x'] = np.clip(blue_patrol['x'], 0, 5000)
        blue_patrol['y'] = np.clip(blue_patrol['y'], 0, 5000)
        blue_patrol['positions'].append((blue_patrol['x'], blue_patrol['y']))

        # This section "bounces" the patrols off the bounds of the area, to keep them from "sticking" to the edges.
        if blue_patrol['x'] == 0:
            blue_patrol['direction'] = 0
        elif blue_patrol['x'] == 5000:
            blue_patrol['direction'] = 180
        if blue_patrol['y'] == 0:    
            blue_patrol['direction'] = 90
        elif blue_patrol['y'] == 5000:
            blue_patrol['direction'] = 270

        distance = np.sqrt((blue_patrol['x'] - hostile_patrol['x'])**2 + (blue_patrol['y'] - hostile_patrol['y'])**2)
        prob_attack = min(1, 100 / distance if distance > 0 else 1)
        if distance <= 1000 and np.random.random() < prob_attack:
            blue_kills, hostile_kills = _attack(
                blue_patrol, hostile_patrol, params['environment'],
                params['armor_type'], distance
            )
            blue_patrol['stock'] -= blue_kills
            hostile_patrol['stock'] -= hostile_kills
            total_blue_kills += blue_kills
            total_hostile_kills += hostile_kills

            if blue_patrol['stock'] <= 0:
                blue_patrol['active'] = False
                blue_patrol['removal_time'] = t

        blue_patrol['stock_history'].append(blue_patrol['stock'])
        hostile_patrol['stock_history'].append(hostile_patrol['stock'])
        positions.append((blue_patrol['x'], blue_patrol['y']))
        hostile_positions.append((hostile_patrol['x'], hostile_patrol['y']))

    # Convert all positions to lists for JSON serialization
    blue_positions_list = [list(pos) for pos in blue_patrol['positions']]
    hostile_positions_list = [list(pos) for pos in hostile_patrol['positions']]
    time_steps_list = list(time_steps[:len(positions)])

    # Optionally, convert stock_history and direction_history if needed
    blue_stock_history = list(blue_patrol['stock_history'])
    blue_direction_history = list(blue_patrol['direction_history'])
    hostile_stock_history = list(hostile_patrol['stock_history'])

    # Prepare patrols for serialization
    blue_patrol_serializable = {
        **blue_patrol,
        'positions': blue_positions_list,
        'stock_history': blue_stock_history,
        'direction_history': blue_direction_history
    }
    hostile_patrol_serializable = {
        **hostile_patrol,
        'positions': hostile_positions_list,
        'stock_history': hostile_stock_history
    }

    result = {
        'blue': blue_patrol_serializable,
        'hostile': hostile_patrol_serializable,
        'positions': blue_positions_list,  # Use blue_patrol['positions']
        'hostile_positions': hostile_positions_list,  # Use hostile_patrol['positions']
        'total_blue_kills': int(total_blue_kills),
        'total_hostile_kills': int(total_hostile_kills),
        'time_steps': time_steps_list
    }
    return make_json_safe(result)
