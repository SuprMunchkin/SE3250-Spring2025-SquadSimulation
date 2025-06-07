from flask import Flask, jsonify, request
import os
from models.squad_simulation import run_simulation

app = Flask(__name__)

def load_html():
    html_path = os.path.join(os.path.dirname(__file__), "view/simulation.html")
    with open(html_path) as f:
        return f.read()

@app.route("/")
def index():
    return load_html()

@app.route("/run_simulation")
def run_simulation_endpoint():
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
    results = run_simulation(params, full_log=True)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)