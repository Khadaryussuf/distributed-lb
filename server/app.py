import os
from flask import Flask, jsonify

app = Flask(__name__)

# Read the server's ID from an environment variable.
# If it's not set (e.g. testing locally), default to "unknown".
SERVER_ID = os.environ.get("SERVER_ID", "unknown")

@app.route("/home", methods=["GET"])
def home():
    return jsonify({
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful"
    }), 200

@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)