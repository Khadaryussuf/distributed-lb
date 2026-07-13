import random
import string
from flask import Flask, jsonify, request
from consistent_hash import ConsistentHashMap

app = Flask(__name__)

hash_map = ConsistentHashMap()

# Tracks server_id -> hostname for every replica currently managed.
replicas = {}

# Simple counter to generate unique server IDs as we add servers.
next_server_id = 1


def generate_hostname():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"Server_{suffix}"


@app.route("/rep", methods=["GET"])
def get_replicas():
    return jsonify({
        "message": {
            "N": len(replicas),
            "replicas": list(replicas.values())
        },
        "status": "successful"
    }), 200


@app.route("/add", methods=["POST"])
def add_replicas():
    global next_server_id

    payload = request.get_json(force=True, silent=True)
    if payload is None or "n" not in payload:
        return jsonify({
            "message": "<Error> Invalid payload, expected JSON with 'n' field",
            "status": "failure"
        }), 400

    n = payload["n"]
    hostnames = payload.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    # Fill in any missing hostnames with randomly generated ones
    while len(hostnames) < n:
        hostnames.append(generate_hostname())

    for hostname in hostnames:
        replicas[next_server_id] = hostname
        hash_map.add_server(next_server_id)
        next_server_id += 1

    return jsonify({
        "message": {
            "N": len(replicas),
            "replicas": list(replicas.values())
        },
        "status": "successful"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)