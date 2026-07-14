import matplotlib.pyplot as plt
from load_test import run_load_test

NUM_REQUESTS = 10000

print(f"Running A-1 experiment: {NUM_REQUESTS} requests against N=3 servers...")
counts = run_load_test(num_requests=NUM_REQUESTS)

servers = sorted(counts.keys())
request_counts = [counts[s] for s in servers]

plt.figure(figsize=(8, 5))
plt.bar(servers, request_counts, color="steelblue")
plt.xlabel("Server ID")
plt.ylabel("Number of Requests Handled")
plt.title(f"A-1: Request Distribution Across N=3 Servers ({NUM_REQUESTS} requests)")
plt.tight_layout()
plt.savefig("a1_bar_chart.png")
print("Saved chart to a1_bar_chart.png")

print("\nRaw counts:")
for s, c in zip(servers, request_counts):
    print(f"  Server {s}: {c} requests")