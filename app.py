from flask import Flask, jsonify, request
import os
import numpy as np
from models.squad_simulation import run_simulation
import pprint

pp = pprint.PrettyPrinter(indent=4)

app = Flask(__name__)

def load_html(filename):
    html_path = os.path.join(os.path.dirname(__file__), f"view/{filename}")
    with open(html_path) as f:
        return f.read()

@app.route("/")
def landing():
    return load_html("landing.html")

@app.route("/simulation")
def simulation_page():
    return load_html("simulation.html")

@app.route("/run_simulation")
def run_simulation_endpoint():
    blue_stock = int(request.args.get("blue_stock", 10))
    red_stock = int(request.args.get("red_stock", 40))
    direction_deviation = int(request.args.get("direction_deviation", 10))
    armor_type = request.args.get("armor_type", "Basilone Ballistic Insert")
    environment = request.args.get("environment", "Krulak’s Three Block War")
    params = {
        "blue_stock": blue_stock,
        "red_stock": red_stock,
        "direction_deviation": direction_deviation,
        "armor_type": armor_type,
        "environment": environment
    }
    results = run_simulation(params, full_log=True)
    #pp.pprint(results)
    return jsonify(results)

@app.route("/monte_carlo")
def monte_carlo_page():
    return load_html("monte_carlo.html")

@app.route("/run_monte_carlo")
def run_monte_carlo_endpoint():
    num_runs = int(request.args.get("num_runs", 100))
    blue_stock = int(request.args.get("blue_stock", 10))
    red_stock = int(request.args.get("red_stock", 10))
    direction_deviation = int(request.args.get("direction_deviation", 10))
    armor_type = request.args.get("armor_type", "Basilone Ballistic Insert")
    environment = request.args.get("environment", "Krulak’s Three Block War")
    params = {
        "blue_stock": blue_stock,
        "red_stock": red_stock,
        "direction_deviation": direction_deviation,
        "armor_type": armor_type,
        "environment": environment
    }
    results = []
    for _ in range(num_runs):
        sim_result = run_simulation(params, full_log=False)
        results.append(sim_result)
    squad_exhaustion = [r['blue']['exhaustion'] for r in results]
    distance_traveled = [r['blue']['patrol_distance'] for r in results]  # or the correct field
    blue_kills = [r['blue']['kills'] for r in results]
    red_kills = [r['red']['kills'] for r in results]
    
    return jsonify({
        "num_runs": num_runs,
        "patrol_distance": distance_traveled,
        "blue_kills": blue_kills,
        "red_kills": red_kills,
        "squad_exhaustion": squad_exhaustion,
        "distance_traveled": distance_traveled,
        "all_results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)