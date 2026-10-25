"""Kruskal vs Prim benchmark. Run from the repository root:
python3 tests/benchmark.py"""
import gc
import pathlib
import platform
import random
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "Python"))
import algorithms as A  # noqa: E402

SEED = 2026
RUNS = 5          # timed runs per method per size (>= 3 required)
WARMUP = 1        # untimed warm-up runs per method per size
SIZES = [(1000, 5000), (10000, 50000), (100000, 250000)]  # (n, m)


def make_graph(n, m, rng):
    """Connected graph: random spanning tree + random extra edges."""
    edges = [[rng.randrange(i), i, rng.randint(-10**9, 10**9)] for i in range(1, n)]
    while len(edges) < m:
        edges.append([rng.randrange(n), rng.randrange(n), rng.randint(-10**9, 10**9)])
    return edges


def measure(func, request):
    for _ in range(WARMUP):
        func(request)
    times = []
    for _ in range(RUNS):
        gc.collect()
        t0 = time.perf_counter()
        result = func(request)
        times.append(time.perf_counter() - t0)
    return times, result


print("Environment:", platform.platform())
print("Machine:", platform.machine(), "| Processor:", platform.processor())
print("Python:", sys.version.split()[0], "| Timer: time.perf_counter")
print(f"Seed: {SEED} | warm-up runs: {WARMUP} | timed runs: {RUNS}")
print("Timing boundary: only the call algorithms.kruskal(request) / algorithms.prim(request);")
print("graph generation, JSON parsing and process start-up are excluded.\n")

rng = random.Random(SEED)
rows = []
for n, m in SIZES:
    request = {"n": n, "edges": make_graph(n, m, rng)}
    tk, rk = measure(A.kruskal, request)
    tp, rp = measure(A.prim, request)
    assert rk["cost"] == rp["cost"] and rk["components"] == rp["components"], "methods disagree"
    rows.append((n, m, tk, tp, rk["cost"]))
    print(f"n={n}, m={m}, cost={rk['cost']}")
    print("  kruskal runs (s):", [round(t, 4) for t in tk], "median:", round(statistics.median(tk), 4))
    print("  prim    runs (s):", [round(t, 4) for t in tp], "median:", round(statistics.median(tp), 4))

print("\n| n | m | Kruskal median (s) | Prim median (s) |")
print("|---|---|---|---|")
for n, m, tk, tp, _ in rows:
    print(f"| {n} | {m} | {statistics.median(tk):.4f} | {statistics.median(tp):.4f} |")