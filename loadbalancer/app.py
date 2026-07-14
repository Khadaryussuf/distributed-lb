import random
import string
import threading
import time
import requests
import docker
from flask import Flask, jsonify, request
from consistent_hash import ConsistentHashMap

app = Flask(__name__)

hash_map = ConsistentHashMap()
docker_client = docker.from_env()

SERVER_IMAGE = "lb-server:latest"
NETWORK_NAME = "net1"
DEFAULT_N = 3

replicas = {}
next_server_id = 1
next_request_id = 1


def generate_hostname():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"Server_{suffix}"


def spawn_container(hostname, server_id):
    docker_client.containers.run(
        SERVER_IMAGE,
        name=hostname,
        environment={"SERVER_ID": str(server_id)},
        network=NETWORK_NAME,
        detach=True,
    )


def remove_container(hostname):
    try:
        c = docker_client.containers.get(hostname)
        c.stop()
        c.remove()
    except docker.errors.NotFound:
        pass


def add_one_replica(hostname):
    global next_server_id
    server_id = next_server_id
    next_server_id += 1
    spawn_container(hostname, server_id)
    replicas[server_id] = hostname
    hash_map.add_server(server_id)
    return server_id


def remove_one_replica(server_id):
    hostname = replicas[server_id]
    remove_container(hostname)
    hash_map.remove_server(server_id)
    del replicas[server_id]


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
        add_one_replica(hostname)

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
        remove_one_replica(server_id)

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


def heartbeat_monitor():
    """
    Runs forever in the background. Every 5 seconds, checks each replica's
    /heartbeat endpoint. If one fails, removes it and spawns a replacement.
    """
    while True:
        time.sleep(5)
        for server_id, hostname in list(replicas.items()):
            try:
                r = requests.get(f"http://{hostname}:5000/heartbeat", timeout=3)
                if r.status_code != 200:
                    raise Exception("bad heartbeat")
            except Exception:
                print(f"[heartbeat] Server {server_id} ({hostname}) failed. Replacing...")
                try:
                    remove_one_replica(server_id)
                except Exception:
                    pass
                new_hostname = generate_hostname()
                add_one_replica(new_hostname)


if __name__ == "__main__":
    for _ in range(DEFAULT_N):
        add_one_replica(generate_hostname())

    monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    monitor_thread.start()

    app.run(host="0.0.0.0", port=5000)