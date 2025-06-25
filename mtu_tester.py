import subprocess, time, statistics, requests, argparse
from ping3 import ping

# --- CLI setup ---
parser = argparse.ArgumentParser(
    description="MTU tester: measure best MTU based on latency and upload performance."
)
parser.add_argument("--ping", type=str, default="1.1.1.1", help="IP to ping (default: 1.1.1.1)")
parser.add_argument("--url", type=str, default="http://localhost:8080/post", help="Target upload URL")
parser.add_argument("--repeats", type=int, default=3, help="Number of upload repeats per MTU")
parser.add_argument("--min-mtu", type=int, default=1200, help="Minimum MTU to test")
parser.add_argument("--max-mtu", type=int, default=1500, help="Maximum MTU to test")
parser.add_argument("--step", type=int, default=20, help="MTU step size")
args = parser.parse_args()

# --- Config ---
MTU_RANGE = range(args.min_mtu, args.max_mtu + 1, args.step)
PAYLOAD_SIZES = [1024, 10240, 102400, 1048576, 5242880]
REPEATS = args.repeats
TEST_URL = args.url
PING_IP = args.ping

# Detect interface
INTERFACE = subprocess.check_output(
    "route get default | awk '/interface: / {print $2}'", shell=True
).decode().strip()

UPLOAD_STATS = {size: [] for size in PAYLOAD_SIZES}
results = []

for mtu in MTU_RANGE:
    print(f"\n▶️ Testing MTU: {mtu}")
    subprocess.run(f"sudo ifconfig {INTERFACE} mtu {mtu}", shell=True, stdout=subprocess.DEVNULL)
    time.sleep(1)

    # Ping test
    pings = []
    print(f"  ↪️ Pinging {PING_IP}...", end="", flush=True)
    for _ in range(5):
        latency = ping(PING_IP, timeout=2)
        if latency:
            pings.append(latency)
        print(".", end="", flush=True)
    if not pings:
        print(" ❌ All pings failed")
        continue
    avg_ping = statistics.mean(pings)
    print(f" ✅ Avg: {round(avg_ping * 1000, 2)} ms")

    # Upload test
    upload_summary = {}
    for size in PAYLOAD_SIZES:
        payload = b"x" * size
        times = []
        print(f"  ⬆️ Uploading {size // 1024} KB", flush=True)
        for _ in range(REPEATS):
            try:
                t0 = time.time()
                r = requests.post(TEST_URL, data=payload, timeout=10)
                dt = time.time() - t0
                if r.ok:
                    times.append(dt)
                    print(f"    ✅ {round(dt, 2)}s", flush=True)
                else:
                    times.append(float("inf"))
                    print("    ❌ Response error", flush=True)
            except Exception:
                times.append(float("inf"))
                print("    ❌ Exception", flush=True)

        times = [t for t in times if t != float("inf")]
        if times:
            avg_time = statistics.mean(times)
            UPLOAD_STATS[size].append(avg_time)
            upload_summary[size] = round(avg_time, 4)
        else:
            upload_summary[size] = float("inf")

    if all(v == float("inf") for v in upload_summary.values()):
        print("  🚫 All uploads failed")
        continue

    score = avg_ping + statistics.mean(
        [v for v in upload_summary.values() if v != float("inf")]
    )
    results.append((mtu, round(avg_ping, 4), upload_summary, round(score, 4)))

# Calculate medians
medians = {
    size: round(statistics.median(times), 4)
    for size, times in UPLOAD_STATS.items() if times
}

# Output summary
results.sort(key=lambda x: x[3])
print(f"\n{'MTU':<6} {'Ping(ms)':<10} {'Score':<8} Uploads (sec | %Δ vs median):")

for mtu, ping_ms, upload_summary, score in results:
    line = f"{mtu:<6} {round(ping_ms * 1000):<10} {score:<8.2f}"
    for size in PAYLOAD_SIZES:
        val = upload_summary.get(size, float("inf"))
        if val == float("inf"):
            line += f" [{size//1024}KB: ❌] "
        else:
            median = medians.get(size, 0.0001)
            delta = ((val - median) / median) * 100
            line += f" [{size//1024}KB: {val:.2f}s | {delta:+.1f}%] "
    print(line)
