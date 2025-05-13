from agent import GoodUnit, BadUnit, battle
from random import random

def run_simulation(armor, energy, num_people):
    squad = GoodUnit(armor, energy, num_people)
    bad_units = []
    battle_results = []

    while True:
        # Move the good unit
        if not squad.move():
            break

        # 5% chance to spawn bad unit
        if random() <= 0.05:
            enemy = BadUnit(squad.x, squad.y)
            bad_units.append(enemy)
            result = battle(squad, enemy)  # Get raw battle results
            result["location"] = (squad.x, squad.y)  # Add combat location
            battle_results.append(result)

            if result["good_unit_eliminated"]:  # Good unit lost
                break

    # Prepare simulation results
    results = {
        "path": squad.history,
        "move_counter": squad.move_counter,
        "remaining_people": squad.num_people,
        "final_energy": squad.energy,
        "final_water": squad.water,
        "lethality": squad.lethality,
        "defense": squad.defense,
        "bad_units_spawned": len(bad_units),
        "battle_results": battle_results,  # List of raw battle results
    }
    return results