import requests
import concurrent.futures
import re
import sys

LOAD_BALANCER_URL = "http://localhost:5000"


def send_one_request(_):
    """
    Sends a single GET request to /home, and extracts the server ID
    from the response text (e.g. "Hello from Server: 2" -> "2").
    Returns the server ID as a string, or None if the request failed.
    """
    try:
        response = requests.get(f"{LOAD_BALANCER_URL}/home", timeout=5)
        match = re.search(r'Server:\s*([^"]+)', response.text)
        if match:
            return match.group(1).strip()
        return None
    except requests.exceptions.RequestException:
        return None


def run_load_test(num_requests=10000, max_workers=50):
    """
    Fires num_requests concurrently (up to max_workers at a time),
    and returns a dictionary counting how many landed on each server.
    """
    counts = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(send_one_request, range(num_requests))

        for server_id in results:
            if server_id is None:
                continue
            counts[server_id] = counts.get(server_id, 0) + 1

    return counts


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    print(f"Sending {n} requests to {LOAD_BALANCER_URL}/home ...")

    counts = run_load_test(num_requests=n)

    print("\nResults:")
    for server_id, count in sorted(counts.items()):
        print(f"  Server {server_id}: {count} requests")

    print(f"\nTotal successful responses: {sum(counts.values())} / {n}")