import random
import string
import requests
from flask import Flask, jsonify, request
from consistent_hash import ConsistentHashMap

app = Flask(__name__)

hash_map = ConsistentHashMap()

replicas = {}
next_server_id = 1
next_request_id = 1


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


@app.route("/rm", methods=["DELETE"])
def remove_replicas():
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
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    ids_to_remove = []
    for hostname in hostnames:
        for server_id, existing_hostname in replicas.items():
            if existing_hostname == hostname:
                ids_to_remove.append(server_id)
                break

    remaining_ids = [sid for sid in replicas.keys() if sid not in ids_to_remove]
    while len(ids_to_remove) < n and remaining_ids:
        chosen = random.choice(remaining_ids)
        ids_to_remove.append(chosen)
        remaining_ids.remove(chosen)

    for server_id in ids_to_remove:
        hash_map.remove_server(server_id)
        del replicas[server_id]

    return jsonify({
        "message": {
            "N": len(replicas),
            "replicas": list(replicas.values())
        },
        "status": "successful"
    }), 200


@app.route("/<path:path>", methods=["GET"])
def route_request(path):
    global next_request_id

    if len(replicas) == 0:
        return jsonify({
            "message": "<Error> No server replicas available",
            "status": "failure"
        }), 400

    request_id = next_request_id
    next_request_id += 1
    server_id = hash_map.get_server(request_id)
    hostname = replicas[server_id]

    target_url = f"http://{hostname}:5000/{path}"

    try:
        response = requests.get(target_url, timeout=5)

        # If the backend server itself couldn't find this endpoint,
        # return the assignment's specific expected error format.
        if response.status_code == 404:
            return jsonify({
                "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
                "status": "failure"
            }), 400

        return response.content, response.status_code, response.headers.items()

    except requests.exceptions.RequestException:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)