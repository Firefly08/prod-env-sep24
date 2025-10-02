from flask import Flask, render_template_string
import psutil
import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoring Dashboard</title>
    <meta http-equiv="refresh" content="5" />
    <style>
        body { font-family: Arial; background: #f0f0f0; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px #ccc; max-width: 400px; margin: auto; }
        h2 { color: #333; }
    </style>
</head>
<body>
    <div class="card">
        <h2>System Monitoring Dashboard</h2>
        <p><strong>Time:</strong> {{ time }}</p>
        <p><strong>CPU Usage:</strong> {{ cpu }}%</p>
        <p><strong>Memory Usage:</strong> {{ memory }}%</p>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(HTML, cpu=cpu, memory=memory, time=now)

if __name__ == "__main__":
    app.run(debug=False)