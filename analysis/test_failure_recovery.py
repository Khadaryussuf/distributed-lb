import requests
import time
import docker

LOAD_BALANCER_URL = "http://localhost:5000"
docker_client = docker.from_env()


def get_replicas():
    response = requests.get(f"{LOAD_BALANCER_URL}/rep", timeout=5)
    return response.json()["message"]["replicas"]


def wait_for_recovery(original_replicas, killed_hostname, timeout=30):
    """
    Polls /rep every second until the replica list changes
    (i.e., the killed server is replaced), or timeout is reached.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_replicas = get_replicas()

        if killed_hostname not in current_replicas and len(current_replicas) == len(original_replicas):
            elapsed = time.time() - start_time
            return elapsed, current_replicas

        time.sleep(1)

    return None, get_replicas()


if __name__ == "__main__":
    print("=== A-3: Failure Recovery Test ===\n")

    print("Step 1: Checking current replicas via /rep...")
    original_replicas = get_replicas()
    print(f"Current replicas: {original_replicas}\n")

    if len(original_replicas) == 0:
        print("No replicas running. Start the stack first.")
        exit(1)

    target_hostname = original_replicas[0]
    print(f"Step 2: Killing server container '{target_hostname}' to simulate failure...")
    container = docker_client.containers.get(target_hostname)
    container.kill()
    print(f"Killed '{target_hostname}'.\n")

    print("Step 3: Polling /rep to detect recovery...")
    elapsed, new_replicas = wait_for_recovery(original_replicas, target_hostname)

    if elapsed is not None:
        print(f"\nRecovery detected after {elapsed:.2f} seconds.")
        print(f"New replica list: {new_replicas}")
    else:
        print("\nRecovery NOT detected within timeout. Something may be wrong.")

    print("\nStep 4: Verifying routing still works...")
    response = requests.get(f"{LOAD_BALANCER_URL}/home", timeout=5)
    print(f"Response from /home: {response.json()}")