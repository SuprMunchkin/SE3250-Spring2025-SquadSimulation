import pytest
from models.blue_patrol import Patrol

@pytest.fixture
def patrol():
    params = {'blue_stock': 2, 'armor_type': 'Basilone Ballistic Insert'}
    return Patrol(params)

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