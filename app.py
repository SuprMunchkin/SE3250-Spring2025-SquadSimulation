from flask import Flask, render_template_string, jsonify
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
    <title>Squad Simulation</title>
    <style>
        #container {
            position: relative;
            width: 600px;
            height: 600px;
            margin: 40px auto;
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
    </style>
</head>
<body>
    <div id="container">
        <div id="dot"></div>
    </div>

    <script>
        const dot = document.getElementById('dot');
        let path = [];
        let index = 0;

        function moveDot() {
            if (path.length === 0) return;
            const [x, y] = path[index];
            dot.style.left = x + 'px';
            dot.style.top = y + 'px';
            index = (index + 1) % path.length;
        }

        fetch('/path')
            .then(res => res.json())
            .then(data => {
                path = data;
                setInterval(moveDot, 1000);
            });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/path")
def get_path():
    # This is a mock path for demonstration purposes.
    # We'll want to replace this with logic to generate a path.
    path = [
        [0, 0],
        [100, 50],
        [200, 100],
        [300, 200],
        [400, 300],
        [500, 400],
        [580, 580]
    ]
    return jsonify(path)

#This is a hack to shutdown the app after x seconds, so it doesn't just run forever.
def shutdown_later(timeout_seconds):
    def shutdown():
        time.sleep(timeout_seconds)
        print(f"\n[INFO] Auto-shutdown triggered after {timeout_seconds} seconds.")
        sys.exit(0)  # forcefully exit the Flask dev server
    threading.Thread(target=shutdown, daemon=True).start()

if __name__ == "__main__":
    #shutdown_later(60)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)