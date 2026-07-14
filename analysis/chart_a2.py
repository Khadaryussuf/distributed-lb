import requests
import matplotlib.pyplot as plt
from load_test import run_load_test

LOAD_BALANCER_URL = "http://localhost:5000"
NUM_REQUESTS = 10000
N_VALUES = [2, 3, 4, 5, 6]


def get_current_n():
    response = requests.get(f"{LOAD_BALANCER_URL}/rep", timeout=5)
    return response.json()["message"]["N"]


def set_replica_count(target_n):
    current_n = get_current_n()

    if target_n > current_n:
        diff = target_n - current_n
        requests.post(
            f"{LOAD_BALANCER_URL}/add",
            json={"n": diff},
            timeout=30
        )
    elif target_n < current_n:
        diff = current_n - target_n
        requests.delete(
            f"{LOAD_BALANCER_URL}/rm",
            json={"n": diff},
            timeout=30
        )
    # if equal, nothing to do


if __name__ == "__main__":
    average_loads = []

    for n in N_VALUES:
        print(f"\nSetting replica count to N={n}...")
        set_replica_count(n)

        actual_n = get_current_n()
        print(f"Confirmed N={actual_n}. Sending {NUM_REQUESTS} requests...")

        counts = run_load_test(num_requests=NUM_REQUESTS)
        total_successful = sum(counts.values())
        avg_load = total_successful / actual_n

        average_loads.append(avg_load)
        print(f"Total successful: {total_successful}, Average load per server: {avg_load:.2f}")

    plt.figure(figsize=(8, 5))
    plt.plot(N_VALUES, average_loads, marker="o", color="darkorange")
    plt.xlabel("Number of Servers (N)")
    plt.ylabel("Average Load per Server (requests)")
    plt.title(f"A-2: Average Load vs Number of Servers ({NUM_REQUESTS} requests each)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("a2_line_chart.png")
    print("\nSaved chart to a2_line_chart.png")