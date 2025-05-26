import numpy as np
import pandas as pd
from math import cos, sin, radians, exp
import yaml
import os

# Load static variables from YAML in the config directory
yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)

# Threat library and profiles
threat_library = config["threat_library"]
armor_profiles = config["armor_profiles"]
threat_probs = config["threat_probs"]
fire_rates = config["fire_rates"]



def get_velocity(threat, distance):
    c1, c2, c3 = threat_library[threat]
    return c1 * distance**2 + c2 * distance + c3

def get_defeat_probability(armor, threat, velocity):
    beta0, beta1 = armor_profiles[armor][threat]
    exponent = beta0 + velocity * beta1
    return np.exp(exponent) / (1 + np.exp(exponent))

def attack(blue_patrol, hostile_patrol, env, armor, distance):
    if distance > 1000:
        return 0, 0
    prob_attack = min(1, 100 / distance if distance > 0 else 1)
    if np.random.random() > prob_attack:
        return 0, 0

    # Use fire_rates loaded from YAML
    blue_min_fire_rate = fire_rates["blue_min"]
    blue_max_fire_rate = fire_rates["blue_max"]
    hostile_min_fire_rate = fire_rates["hostile_min"]
    hostile_max_fire_rate = fire_rates["hostile_max"]

    # Blue shots
    blue_shots = np.random.randint(blue_min_fire_rate, blue_max_fire_rate + 1) * blue_patrol['stock']
    prob_blue_hit = exp(-0.002 * distance)
    blue_hits = sum(np.random.random() < prob_blue_hit for _ in range(blue_shots))
    hostile_kills = min(hostile_patrol['stock'], sum(np.random.normal(0.75, 0.05) > np.random.random() for _ in range(blue_hits)))

    # Hostile shots
    hostile_shots = np.random.randint(hostile_min_fire_rate, hostile_max_fire_rate + 1) * hostile_patrol['stock']
    hostile_threat = np.random.choice(list(threat_probs[env].keys()), p=list(threat_probs[env].values()))
    hostile_velocity = get_velocity(hostile_threat, distance)
    prob_hostile_hit = exp(-0.002 * distance)
    hostile_hits = sum(np.random.random() < prob_hostile_hit for _ in range(hostile_shots))
    hostile_defeats = sum(np.random.random() < get_defeat_probability(armor, hostile_threat, hostile_velocity) for _ in range(hostile_hits))
    blue_kills = min(blue_patrol['stock'], hostile_defeats)

    return blue_kills, hostile_kills

def run_simulation(config, params, fire_rates, verbose=False):
    start_time = 0
    stop_time = 4320
    dt = 1
    time_steps = np.arange(start_time, stop_time + dt, dt)

    # Initialize blue and hostile patrols
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
    blue_min_fire_rate = fire_rates["blue_min"]
    blue_max_fire_rate = fire_rates["blue_max"]
    hostile_min_fire_rate = fire_rates["hostile_min"]
    hostile_max_fire_rate = fire_rates["hostile_max"]

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

        distance = np.sqrt((blue_patrol['x'] - hostile_patrol['x'])**2 + (blue_patrol['y'] - hostile_patrol['y'])**2)
        if distance <= 1000:
            blue_kills, hostile_kills = attack(
                blue_patrol, hostile_patrol, params['environment'],
                params['armor_type'], distance, config, fire_rates
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

    return {
        'blue': blue_patrol,
        'hostile': hostile_patrol,
        'positions': positions,
        'hostile_positions': hostile_positions,
        'total_blue_kills': total_blue_kills,
        'total_hostile_kills': total_hostile_kills,
        'time_steps': time_steps[:len(positions)]
    }
