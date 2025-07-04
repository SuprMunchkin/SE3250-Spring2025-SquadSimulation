import pytest
from models.blue_patrol import Patrol
import os
import yaml

# Pull in the config to test the movement aginst the map border.
yaml_path = os.path.join(os.path.dirname(__file__), "../config/simulation.yaml")
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
map_size = config["map_size"]
terrain_lib = config["terrain_library"]

@pytest.fixture
def patrol():
    params = {
        'armor_type': 'Basilone Ballistic Insert',
        'blue_stock': 20
    }
    return Patrol(params, full_log=True)

def test_patrol_creation():
    params = {
        'armor_type': 'Basilone Ballistic Insert',
        'blue_stock': 20
    }
    patrol = Patrol(params)
    assert len(patrol.squad_data) == 20
    assert patrol.get_stock() == 20
    assert hasattr(patrol, 'current_position')
    assert hasattr(patrol, 'position_history')
    assert patrol.position_history[0] == patrol.current_position

def test_exhaustion_threshold(patrol):
    patrol.patrol_time = 120  # 2 hours
    result = patrol.get_exhaustion_threshold()
    assert isinstance(result, float)
    assert result < 546.9
    assert result > 546.8

    patrol.patrol_time = 1
    result = patrol.get_exhaustion_threshold()
    assert result > 3485
    assert result < 3486

def test_is_exhausted_true(patrol):
    patrol.patrol_time = 120
    patrol.squad_exhaustion = 600
    assert patrol.is_exhausted() is True

def test_is_exhausted_false(patrol):
    patrol.patrol_time = 120
    patrol.squad_exhaustion = 500
    assert patrol.is_exhausted() is False

def test_to_dict_keys(patrol):
    d = patrol.to_dict()
    assert isinstance(d, dict)
    for key in ['stock', 'current_position', 'direction', 'patrol_time']:
        assert key in d

def test_take_casualties(patrol):
    assert patrol.get_stock() == 20
    patrol.take_casualties(5, 1)
    assert len(patrol.squad_data) == 15
    assert patrol.get_stock() == 15
    assert len(patrol.casualties) == 5

def test_update_terrain(patrol):
    assert patrol.terrain_change_counter == 0
    patrol.terrain_change_interval = 1
    patrol.current_terrain = 'light_brush'
    patrol._update_terrain()
    assert patrol.current_terrain == 'light_brush'
    assert patrol.terrain_change_counter == 1
    assert patrol.terrain_change_interval == 1
    # Make sure all terrain types show up when the simulation goes for long enough.
    for _ in range(1000):
        patrol.terrain_change_interval = 0
        patrol._update_terrain()
    assert len(patrol.terrain_history) == 1002
    assert set(patrol.terrain_history) == set(terrain_lib)

def test_set_exhaustion(patrol):
        patrol.squad_data = [{
                'soldier': 75,
                'load': (20.6497926 + 8.3043963255),
                'joules_expended': 0, 
                'exhaustion_level': 0,
                'removal_time': None,
                'exhausted': False,
                'Killed': False
            }, {
                'soldier': 80,
                'load': (20.6497926 + 8.3043963255),
                'joules_expended': 0, 
                'exhaustion_level': 0,
                'removal_time': None,
                'exhausted': False,
                'Killed': False
            }]
        patrol.current_terrain = 'loose_sand' 
        patrol.move_speed = 1/2.1
        patrol.grade = 1
        patrol.patrol_time = 1
        patrol.set_exhaustion()
        assert patrol.squad_data[0]['joules_expended'] > 15000
        assert patrol.squad_data[0]['joules_expended'] < 15500
        assert patrol.squad_data[1]['joules_expended'] > 15500
        assert patrol.squad_data[1]['joules_expended'] < 16000
        assert patrol.squad_data[0]['exhaustion_level'] < 0.07
        assert patrol.squad_data[0]['exhaustion_level'] > 0.06
        assert patrol.squad_data[1]['exhaustion_level'] < 0.07
        assert patrol.squad_data[1]['exhaustion_level'] > 0.06
        assert patrol.squad_data[0]['joules_expended']  < patrol.squad_data[1]['joules_expended']
        assert patrol.squad_data[0]['exhaustion_level'] < patrol.squad_data[1]['exhaustion_level']
        assert patrol.exhaustion_data[0][0] == 0
        assert patrol.exhaustion_data[0][1] == 0
        # These indicies are off by 1 because the threshold data is stored in slot 0.
        assert patrol.exhaustion_data[1][1] < 0.07
        assert patrol.exhaustion_data[1][1] > 0.06
        assert patrol.exhaustion_data[1][2] < 0.07
        assert patrol.exhaustion_data[1][2] > 0.06

        patrol.grade = -2
        patrol.set_exhaustion()
        patrol.patrol_time += 1
        assert patrol.squad_data[0]['joules_expended'] > 27000
        assert patrol.squad_data[0]['joules_expended'] < 27500
        assert patrol.squad_data[0]['exhaustion_level'] < 0.12
        assert patrol.squad_data[0]['exhaustion_level'] > 0.11
        assert patrol.squad_data[0]['joules_expended']  < patrol.squad_data[1]['joules_expended']
        assert patrol.squad_data[0]['exhaustion_level'] < patrol.squad_data[1]['exhaustion_level']
        assert patrol.exhaustion_data[patrol.patrol_time][1] < 0.12
        assert patrol.exhaustion_data[patrol.patrol_time][1] > 0.11

        patrol.grade = 10
        patrol.set_exhaustion()
        patrol.patrol_time += 1
        assert patrol.squad_data[0]['joules_expended'] > 61750
        assert patrol.squad_data[0]['joules_expended'] < 62250
        assert patrol.squad_data[0]['exhaustion_level'] < 0.17
        assert patrol.squad_data[0]['exhaustion_level'] > 0.16
        assert patrol.squad_data[0]['joules_expended']  < patrol.squad_data[1]['joules_expended']
        assert patrol.squad_data[0]['exhaustion_level'] < patrol.squad_data[1]['exhaustion_level']


def test_move(patrol):
    #Testing simple move logic
    patrol.current_position = [0,0]
    patrol.direction = 45
    patrol.move(10, 0)
    assert patrol.current_position[0] < 7.08
    assert patrol.current_position[0] > 7.06
    assert patrol.current_position[1] < 7.08
    assert patrol.current_position[1] > 7.06
    assert patrol.move_speed > 9.9
    assert patrol.move_speed < 10.1

    #Testing bounce corner logic
    patrol.current_position = [0,0]
    patrol.direction = 225
    patrol.move(10, 0)
    assert patrol.current_position[0] < 7.08
    assert patrol.current_position[0] > 7.06
    assert patrol.current_position[1] < 7.08
    assert patrol.current_position[1] > 7.06
    assert patrol.move_speed > 9.9
    assert patrol.move_speed < 10.1

    #Testing bounce against west wall
    patrol.current_position = [0,100]
    patrol.direction = 180
    patrol.move(10, 0)
    assert patrol.current_position[0] < 10.1
    assert patrol.current_position[0] > 9.9
    assert patrol.current_position[1] < 100.1
    assert patrol.current_position[1] > 99.9
    assert patrol.move_speed > 9.9
    assert patrol.move_speed < 10.1

    #Testing bounce against south wall
    patrol.current_position = [100,0]
    patrol.direction = 270
    patrol.move(10, 0)
    assert patrol.current_position[0] < 100.1
    assert patrol.current_position[0] > 99.9
    assert patrol.current_position[1] < 10.1
    assert patrol.current_position[1] > 9.9
    assert patrol.move_speed > 9.9
    assert patrol.move_speed < 10.1

    #Testing bounce against east wall
    patrol.current_position = [map_size,100]
    patrol.direction = 0
    patrol.move(10, 0)
    assert patrol.current_position[0] < (map_size - 10) + 0.1
    assert patrol.current_position[0] > (map_size - 10) - 0.1
    assert patrol.current_position[1] < 100.1
    assert patrol.current_position[1] > 99.9
    assert patrol.move_speed > 9.9
    assert patrol.move_speed < 10.1
    
    #Testing bounce against north wall
    patrol.current_position = [100, map_size]
    patrol.direction = 90
    patrol.move(10, 0)
    assert patrol.current_position[0] < 100.1
    assert patrol.current_position[0] > 99.9
    assert patrol.current_position[1] < (map_size - 10) + 0.1
    assert patrol.current_position[1] > (map_size - 10) - 0.1
    assert patrol.move_speed > 9.9
    assert patrol.move_speed < 10.1
 