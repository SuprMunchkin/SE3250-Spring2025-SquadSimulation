from flask import Flask, render_template_string, jsonify, request
from selib import *
import os
import threading
import time
import sys


app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Simulation Control</title>
    <style>
        body {
            font-family: sans-serif;
            text-align: center;
        }
        #container {
            position: relative;
            width: 600px;
            height: 600px;
            margin: 20px auto;
            border: 1px solid black;
            background-color: white;
        }
        #dot {
            width: 20px;
            height: 20px;
            background-color: red;
            border-radius: 50%;
            position: absolute;
            transition: left 0.2s ease, top 0.2s ease;
        }
        #controls {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h2>Soldier Simulation</h2>
    <div id="container">
        <div id="dot"></div>
    </div>

    <div id="controls">
        <button onclick="startSimulation()">Start</button>
        <button onclick="stopSimulation()">Stop</button>
        <select id="pathSelect">
            <option value="default">Default Path</option>
            <option value="zigzag">Zigzag</option>
        </select>
        <p id="status">Status: Idle</p>
    </div>

    <script>
        const dot = document.getElementById('dot');
        const status = document.getElementById('status');
        let path = [];
        let index = 0;
        let intervalId = null;

        function moveDot() {
            if (path.length === 0) return;
            const [x, y] = path[index];
            dot.style.left = x + 'px';
            dot.style.top = y + 'px';
            index = (index + 1) % path.length;
        }

        function startSimulation() {
            stopSimulation(); // in case it's already running
            const selectedPath = document.getElementById('pathSelect').value;
            fetch(`/path?name=${selectedPath}`)
                .then(res => res.json())
                .then(data => {
                    path = data;
                    index = 0;
                    intervalId = setInterval(moveDot, 1000);
                    status.textContent = "Status: Running";
                });
        }

        function stopSimulation() {
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
                status.textContent = "Status: Stopped";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/path")
def get_path():
    name = request.args.get("name", "default")
    if name == "zigzag":
        path = [[0, 0], [100, 100], [0, 200], [100, 300], [0, 400], [100, 500]]
    else:
        path = [[0, 0], [100, 50], [200, 100], [300, 200], [400, 300], [580, 580]]
    return jsonify(path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)