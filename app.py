from flask import Flask, render_template_string, jsonify, request
from simulation import run_simulation
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Simulation Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
        }
        #simulation-container {
            margin: 20px auto;
            position: relative;
            width: 600px;
            height: 600px;
            border: 1px solid black;
            background-color: #f0f0f0;
        }
        canvas {
            position: absolute;
            top: 0;
            left: 0;
        }
    </style>
</head>
<body>
    <h1>Simulation Control</h1>
    <form id="simulation-form">
        <label for="armor">Armor:</label>
        <select id="armor" name="armor">
            <option value="Light">Light</option>
            <option value="Medium" selected>Medium</option>
            <option value="Heavy">Heavy</option>
        </select>
        <br>
        <label for="energy">Energy:</label>
        <input type="number" id="energy" name="energy" value="100" min="10" max="100">
        <br>
        <label for="num_people">Number of People:</label>
        <input type="number" id="num_people" name="num_people" value="40" min="30" max="50">
        <br>
        <button type="button" onclick="startSimulation()">Run Simulation</button>
    </form>
    <div id="simulation-container">
        <canvas id="simulation-canvas" width="600" height="600"></canvas>
    </div>
    <pre id="results"></pre>
    <script>
        const canvas = document.getElementById('simulation-canvas');
        const ctx = canvas.getContext('2d');
        const resultsElement = document.getElementById('results');
        let path = [];
        let combats = [];
        let index = 0;
        let animationFrameId = null;
        let frameDelay = 5; // Number of frames to wait before moving to the next point
        let frameCounter = 0;

        function drawUnit(x, y) {
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas

            // Draw combat locations that have already occurred
            combats.slice(0, index).forEach(([cx, cy]) => {
                ctx.fillStyle = 'red'; // Red for combat locations
                ctx.beginPath();
                ctx.arc(cx * canvas.width, cy * canvas.height, 5, 0, Math.PI * 2); // Small red circle
                ctx.fill();
            });

            // Draw the good unit
            ctx.fillStyle = 'blue'; // Blue for the good unit
            ctx.beginPath();
            ctx.arc(x * canvas.width, y * canvas.height, 10, 0, Math.PI * 2); // Larger blue circle
            ctx.fill();
        }

        function moveUnit() {
            if (index >= path.length) {
                cancelAnimationFrame(animationFrameId); // Stop the animation
                return;
            }

            // Increment the frame counter and only move the unit after the delay
            if (frameCounter === 0) {
                const [x, y] = path[index];
                drawUnit(x, y);

                // Check if a combat occurred at this location
                if (combats[index]) {
                    combats.push(combats[index]); // Add combat location dynamically
                }

                index++;
            }

            frameCounter = (frameCounter + 1) % frameDelay; // Reset the counter after the delay
            animationFrameId = requestAnimationFrame(moveUnit); // Schedule the next frame
        }

        function startSimulation() {
            stopSimulation(); // Stop any ongoing simulation
            const form = document.getElementById('simulation-form');
            const formData = new FormData(form);
            const params = new URLSearchParams(formData).toString();
            fetch(`/run_simulation?${params}`)
                .then(response => response.json())
                .then(data => {
                    path = data.path;
                    combats = data.battle_results.map(battle => battle.location); // Extract combat locations
                    index = 0;
                    resultsElement.textContent = formatResults(data);
                    animationFrameId = requestAnimationFrame(moveUnit); // Start the animation
                });
        }

        function stopSimulation() {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId); // Cancel the animation
                animationFrameId = null;
            }
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
        }

        function formatResults(data) {
            let output = `Simulation Results:\n`;
            output += `Moves: ${data.move_counter}\n`;
            output += `Remaining People: ${data.remaining_people}\n`;
            output += `Final Energy: ${data.final_energy}\n`;
            output += `Final Water: ${data.final_water}\n`;
            output += `Lethality: ${data.lethality}\n`;
            output += `Defense: ${data.defense}\n`;
            output += `Bad Units Spawned: ${data.bad_units_spawned}\n\n`;

            output += `Battle Results:\n`;
            data.battle_results.forEach((battle, index) => {
                output += `  Battle ${index + 1}:\n`;
                output += `    Turns: ${battle.turns}\n`;
                output += `    Good Unit Losses: ${battle.good_unit_losses}\n`;
                output += `    Bad Unit Losses: ${battle.bad_unit_losses}\n`;
                output += `    Good Unit Remaining: ${battle.good_unit_remaining}\n`;
                output += `    Bad Unit Remaining: ${battle.bad_unit_remaining}\n`;
                output += `    Location: (${battle.location[0].toFixed(2)}, ${battle.location[1].toFixed(2)})\n`;
                if (battle.good_unit_eliminated) {
                    output += `    ❌ The good unit has been eliminated!\n`;
                } else if (battle.good_unit_exiting) {
                    output += `    ⚠️ The good unit is exiting!\n`;
                }
                output += `\n`;
            });

            return output;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML

@app.route("/run_simulation")
def run_simulation_endpoint():
    armor = request.args.get("armor", "Medium")
    energy = int(request.args.get("energy", 100))
    num_people = int(request.args.get("num_people", 40))
    results = run_simulation(armor, energy, num_people)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)