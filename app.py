from flask import Flask, render_template_string, jsonify, request
from simulation import run_simulation
from app.models.agent import GoodUnit, BadUnit, battle
from random import random
import os

app = Flask(__name__)

def load_html():
    with open(os.path.join(os.path.dirname(__file__), "view/simulation.html")) as f:
        return f.read()

@app.route("/")
def index():
    return load_html()

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

@app.route("/run_simulation")
def run_simulation_endpoint():
    armor = request.args.get("armor", "Medium")
    energy = int(request.args.get("energy", 100))
    num_people = int(request.args.get("num_people", 40))
    results = run_simulation(armor, energy, num_people)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)