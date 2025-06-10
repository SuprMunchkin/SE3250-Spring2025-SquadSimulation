import pytest
import models.squad_simulation as squad_sim

def test_module_importable():
    assert hasattr(squad_sim, 'run_simulation')
    assert callable(squad_sim.run_simulation)

def test_run_simulation_basic():
    params = {
        "blue_stock": 5,
        "red_stock": 10,
        "direction_deviation": 5,
        "armor_type": "Basilone Ballistic Insert",
        "environment": "Krulak’s Three Block War"
    }
    result = squad_sim.run_simulation(params, full_log=True)
    assert isinstance(result, dict)
    # Check for some expected keys (adjust as needed)
    for key in ["blue", "red"]:
        assert key in result

def test_run_simulation_multiple_runs():
    params = {
        "blue_stock": 3,
        "red_stock": 3,
        "direction_deviation": 2,
        "armor_type": "Chesty Ballistic Insert",
        "environment": "Pershing’s Ghost"
    }
    results = [squad_sim.run_simulation(params, full_log=False) for _ in range(5)]
    assert all(isinstance(r, dict) for r in results)