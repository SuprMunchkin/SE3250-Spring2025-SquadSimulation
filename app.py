from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Moving Dot</title>
    <style>
        body {
            background-color: white;
        }
        #container {
            position: relative;
            width: 600px;
            height: 600px;
            border: 1px solid black;
            margin: 40px auto;
        }
        #dot {
            width: 20px;
            height: 20px;
            background-color: red;
            border-radius: 50%;
            position: absolute;
            left: 0;
            top: 0;
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
    const path = [
        [0, 0],
        [100, 50],
        [200, 100],
        [300, 200],
        [400, 300],
        [500, 400],
        [580, 580], // max corner
        [400, 300],
        [200, 100],
        [0, 0]
    ];
    let index = 0;

    function moveDot() {
        const [x, y] = path[index];
        dot.style.left = x + 'px';
        dot.style.top = y + 'px';
        index = (index + 1) % path.length; // loop
    }

    setInterval(moveDot, 1000);
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
