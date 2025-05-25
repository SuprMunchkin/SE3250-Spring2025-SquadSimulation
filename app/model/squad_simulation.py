import numpy as np
import pandas as pd
from math import cos, sin, radians, exp
import yaml
import os

# Load static variables from YAML in the config directory
yaml_path = os.path.join(os.path.dirname(__file__), "../../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)

# Threat library and profiles
threat_library = config["threat_library"]
armor_profiles = config["armor_profiles"]
threat_probs = config["threat_probs"]

def get_velocity(threat, distance):
    c1, c2, c3 = threat_library[threat]
    return c1 * distance**2 + c2 * distance + c3

def get_defeat_probability(armor, threat, velocity):
    beta0, beta1 = armor_profiles[armor][threat]
    exponent = beta0 + velocity * beta1
    return np.exp(exponent) / (1 + np.exp(exponent))

def attack(blue_patrol, hostile_patrol, env, armor, distance, blue_min_fire_rate, blue_max_fire_rate, hostile_min_fire_rate, hostile_max_fire_rate):
    if distance > 1000:
        return 0, 0
    prob_attack = min(1, 100 / distance if distance > 0 else 1)
    if np.random.random() > prob_attack:
        return 0, 0

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

def run_simulation(
    unit_size,
    armor,
    terrain_percentages,
    direction_deviation,
    grade_std,
    hostile_stock,
    env,
    blue_min_fire_rate,
    blue_max_fire_rate,
    hostile_min_fire_rate,
    hostile_max_fire_rate,
    verbose=True
):
    # ...move your simulation logic here, using the above utility functions...
    # Return results (e.g., positions, metrics, etc.)
    pass