import pytest
from models.blue_patrol import Patrol

@pytest.fixture
def patrol():
    params = {
        'armor_type': 'Basilone Ballistic Insert',
        'blue_stock': 20
    }
    return Patrol(params, full_log=False)

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
    assert result > 0

def test_is_exhausted_true(patrol):
    patrol.patrol_time = 60
    patrol.squad_exhaustion = 1000
    assert patrol.is_exhausted() is True

def test_is_exhausted_false(patrol):
    patrol.patrol_time = 60
    patrol.squad_exhaustion = 0
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
 