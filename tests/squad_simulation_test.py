import pytest
from models.squad_simulation import run_simulation

@pytest.fixture
def default_params():
    return {
        "blue_stock": 10,
        "red_stock": 20,
        "direction_deviation": 10,
        "armor_type": "Basilone Ballistic Insert",
        "environment": "Krulak’s Three Block War"
    }

def test_run_simulation_returns_dict(default_params):
     result = run_simulation(default_params, full_log=True)
     assert isinstance(result, dict)

def test_run_simulation_has_expected_keys(default_params):
    result = run_simulation(default_params, full_log=True)
    # Adjust these keys to match your actual simulation output
    expected_keys = ["blue", "red", "red_patrols, combat_log"]
    for key in expected_keys:
        assert key in result

def test_run_simulation_handles_minimal_params():
    params = {
        "blue_stock": 1,
        "red_stock": 1,
        "direction_deviation": 0,
        "armor_type": "Basilone Ballistic Insert",
        "environment": "Krulak’s Three Block War"
    }
    result = run_simulation(params, full_log=False)
    assert isinstance(result, dict)