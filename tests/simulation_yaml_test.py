import pytest

# Open config file
import os
import yaml
yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)

def test_terrain_probabilities():
    prob = 0
    for env in config['terrain_library'].values():
        prob += env[1]
    assert prob == 1

def test_threat_probs():
    for env in config['threat_probs'].values():
        prob = 0
        for p in env.values():
            prob += p
        assert int(prob) == 1
    
def test_threat_charastics():
    velocity = 0
    distance = 1000
    for threat in config['threat_library'].values():
        velocity = threat[0]*distance**2 + threat[1]*distance + threat[2]
        # Velocity at 1000m (max range of simulation) needs to still be postive to be valid
        assert velocity > 0
        # Threat[2] should be muzzle velocity, so that should be less than velocity at 1000m 
        assert velocity < threat[2]
