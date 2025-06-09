from flask import Flask, jsonify, request
import os
from models.squad_simulation import run_simulation

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
    # Example: calculate average of a result field called 'score'
    scores = [r.get('score', 0) for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0
    return jsonify({
        "num_runs": num_runs,
        "avg_score": avg_score,
        "all_results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)