"""Own tests. Run from the repository root: python3 tests/test_my_cases.py
Expected answers are justified in comments; non-unique answers are checked by validity."""
import json
import pathlib
import random
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "Python"))
import algorithms as A  # noqa: E402

passed = failed = 0


def check(name, cond, info=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", name)
    else:
        failed += 1
        print("FAIL", name, info)


# ---------------------------------------------------------------- validators
def mst_ok(n, edges, res, cost, comps):
    ids = res["edge_ids"]
    if len(set(ids)) != len(ids) or any(not 0 <= i < len(edges) for i in ids):
        return False
    p = list(range(n))

    def find(x):
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    total = 0
    for i in ids:
        u, v, w = edges[i]
        a, b = find(u), find(v)
        if a == b:
            return False  # cycle inside the forest
        p[a] = b
        total += w
    return total == res["cost"] == cost and res["components"] == comps and n - len(ids) == comps


def topo_ok(n, edges, res, acyclic):
    if res["acyclic"] != acyclic:
        return False
    if not acyclic:
        return res["order"] == []
    pos = {v: k for k, v in enumerate(res["order"])}
    return len(pos) == n == len(res["order"]) and all(pos[u] < pos[v] for u, v in edges)


def scc_ok(n, edges, res, groups):
    comp = res["component"]
    if len(comp) != n:
        return False
    parts = {}
    for v, c in enumerate(comp):
        parts.setdefault(c, set()).add(v)
    if {frozenset(s) for s in parts.values()} != {frozenset(g) for g in groups}:
        return False
    cond = [tuple(x) for x in res["condensation"]]
    want = {(comp[u], comp[v]) for u, v in edges if comp[u] != comp[v]}
    return len(cond) == len(set(cond)) and set(cond) == want


def dag_ok(n, edges, source, res, expected_dist=None):
    """Certificate: exact distances + valid parent edges + no relaxable edge."""
    if res["acyclic"] is not True:
        return False
    d, par = res["distance"], res["parent_edge"]
    if len(d) != n or len(par) != n or d[source] != 0 or par[source] != -1:
        return False
    if expected_dist is not None and d != expected_dist:
        return False
    for v in range(n):
        if v == source:
            continue
        if d[v] is None:
            if par[v] != -1:
                return False
            continue
        i = par[v]
        if not 0 <= i < len(edges) or edges[i][1] != v:
            return False
        u, _, w = edges[i]
        if d[u] is None or d[u] + w != d[v]:
            return False
    for u, v, w in edges:
        if d[u] is not None and (d[v] is None or d[v] > d[u] + w):
            return False
    return True


def route_ok(edges, source, target, res, route):
    d = res["distance"]
    if d[target] is None:
        return route is None
    vs, es = route["vertices"], route["edge_ids"]
    if vs[0] != source or vs[-1] != target or len(es) != len(vs) - 1:
        return False
    total = 0
    for k, e in enumerate(es):
        if edges[e][0] != vs[k] or edges[e][1] != vs[k + 1]:
            return False
        total += edges[e][2]
    return total == d[target]


# ---------------------------------------------------------------- DSU
r = A.dsu({"n": 5, "operations": [[0, 1], [1, 0], [2, 2], [3, 4], [1, 3]]})
# 5 comps; union(0,1)->4,2; repeat->4,2; self->4,2; union(3,4)->3,2; union(1,3)->2,4
check("dsu mixed", r["states"] == [[4, 2], [4, 2], [4, 2], [3, 2], [2, 4]], r)
check("dsu empty", A.dsu({"n": 0, "operations": []})["states"] == [])

# ---------------------------------------------------------------- MST
E = [[0, 1, -5], [0, 1, 3], [2, 2, -100], [1, 2, 4]]
# loop (-100) is never taken, parallel 3 is a cycle; take -5 and 4; vertex 3 isolated
for name, f in (("kruskal", A.kruskal), ("prim", A.prim)):
    check(name + " negative/loop/parallel/isolate", mst_ok(4, E, f({"n": 4, "edges": E}), -1, 2))
    T = [[0, 1, 1], [1, 2, 1], [0, 2, 1]]  # tie: any 2 edges, cost 2
    check(name + " tied optima", mst_ok(3, T, f({"n": 3, "edges": T}), 2, 1))
    B = [[0, 1, 10**9], [1, 2, 10**9], [0, 2, -10**9]]  # best: -1e9 + 1e9 = 0
    check(name + " boundary weights", mst_ok(3, B, f({"n": 3, "edges": B}), 0, 1))
    check(name + " empty graph", mst_ok(0, [], f({"n": 0, "edges": []}), 0, 0))
    check(name + " only isolates", mst_ok(3, [], f({"n": 3, "edges": []}), 0, 3))
    bad = {"cost": 0, "edge_ids": [0, 0], "components": 1}  # invalid witness (repeated edge)
    check(name + " validator rejects invalid witness",
          not mst_ok(2, [[0, 1, 0]], bad, 0, 1))

random.seed(12345)
n = 100000
chain = [[i, i + 1, random.randint(-10**9, 10**9)] for i in range(n - 1)]
exact = sum(e[2] for e in chain)  # a tree: the only spanning tree is the chain itself
for name, f in (("kruskal", A.kruskal), ("prim", A.prim)):
    check(name + " n=100000 chain exact", mst_ok(n, chain, f({"n": n, "edges": chain}), exact, 1))
big = chain + [[random.randrange(n), random.randrange(n), random.randint(-10**9, 10**9)]
               for _ in range(250000 - len(chain))]
rk, rp = A.kruskal({"n": n, "edges": big}), A.prim({"n": n, "edges": big})
check("full limit m=250000: kruskal==prim cost, both valid",
      rk["cost"] == rp["cost"] and mst_ok(n, big, rk, rk["cost"], 1) and mst_ok(n, big, rp, rk["cost"], 1))

ops = [[i, i + 1] for i in range(n - 1)] + [[random.randrange(n), random.randrange(n)]
                                             for _ in range(250000 - (n - 1))]
st = A.dsu({"n": n, "operations": ops})["states"]
check("dsu full limit (250000 ops)", len(st) == 250000 and st[n - 2] == [1, n] and st[-1] == [1, n])

# ---------------------------------------------------------------- SCC
S = [[0, 1], [1, 2], [2, 0], [2, 3], [3, 4], [4, 3], [0, 1], [5, 5]]
check("scc groups + duplicates + self loop",
      scc_ok(6, S, A.scc({"n": 6, "edges": S}), [{0, 1, 2}, {3, 4}, {5}]))
check("scc empty", scc_ok(0, [], A.scc({"n": 0, "edges": []}), []))
dc = [[i, i + 1] for i in range(n - 1)]
rs = A.scc({"n": n, "edges": dc})
check("scc deep chain n=100000", len(set(rs["component"])) == n and len(rs["condensation"]) == n - 1)
rs = A.scc({"n": n, "edges": dc + [[n - 1, 0]]})
check("scc deep cycle (1 component)", len(set(rs["component"])) == 1 and rs["condensation"] == [])

# ---------------------------------------------------------------- topo
check("topo parallel+isolated", topo_ok(4, [[0, 1], [0, 1], [2, 3]], A.topo({"n": 4, "edges": [[0, 1], [0, 1], [2, 3]]}), True))
check("topo self loop", topo_ok(2, [[1, 1]], A.topo({"n": 2, "edges": [[1, 1]]}), False))
C = [[0, 1], [2, 3], [3, 2]]
check("topo disconnected cycle", topo_ok(4, C, A.topo({"n": 4, "edges": C}), False))
check("topo deep chain", topo_ok(n, dc, A.topo({"n": n, "edges": dc}), True))
check("topo deep cycle", topo_ok(n, dc + [[n - 1, 0]], A.topo({"n": n, "edges": dc + [[n - 1, 0]]}), False))
check("topo validator rejects reversed order",
      not topo_ok(3, [[0, 1], [1, 2]], {"acyclic": True, "order": [2, 1, 0]}, True))

# ---------------------------------------------------------------- DAG + route helper
D = [[0, 1, 2], [0, 1, 1], [1, 2, -3], [0, 2, 5], [3, 4, 1]]
res = A.dag({"n": 5, "edges": D, "source": 0})
# 0->1 best 1 (edge 1); 1->2 gives -2 (edge 2) < 5; 3,4 unreachable
check("dag distances", dag_ok(5, D, 0, res, [0, 1, -2, None, None]) and res["parent_edge"] == [-1, 1, 2, -1, -1], res)
rt = A.route(D, 0, 2, res["distance"], res["parent_edge"])
check("route reachable target", rt == {"vertices": [0, 1, 2], "edge_ids": [1, 2]} and route_ok(D, 0, 2, res, rt), rt)
rt = A.route(D, 0, 0, res["distance"], res["parent_edge"])
check("route source", rt == {"vertices": [0], "edge_ids": []}, rt)
rt = A.route(D, 0, 3, res["distance"], res["parent_edge"])
check("route unreachable target", rt is None and route_ok(D, 0, 3, res, rt))
Tt = [[0, 1, 1], [0, 1, 1], [1, 2, 1], [0, 2, 2]]  # ties: dist[1]=1 (edge 0 or 1), dist[2]=2 (edge 2 or 3)
res = A.dag({"n": 3, "edges": Tt, "source": 0})
rt = A.route(Tt, 0, 2, res["distance"], res["parent_edge"])
check("dag + route tied/parallel", dag_ok(3, Tt, 0, res, [0, 1, 2]) and route_ok(Tt, 0, 2, res, rt))
Cy = [[0, 1, 1], [2, 3, 1], [3, 2, 1]]  # cycle NOT reachable from source, still must be rejected
check("dag cycle unreachable from source",
      A.dag({"n": 4, "edges": Cy, "source": 0}) == {"acyclic": False, "distance": [], "parent_edge": []})
check("dag singleton", dag_ok(1, [], 0, A.dag({"n": 1, "edges": [], "source": 0}), [0]))
check("dag validator rejects wrong witness",
      not dag_ok(3, [[0, 1, 1], [1, 2, 1]], 0,
                 {"acyclic": True, "distance": [0, 1, 2], "parent_edge": [-1, 0, 0]}))
dd = [[i, i + 1, 1] for i in range(n - 1)]
res = A.dag({"n": n, "edges": dd, "source": 0})
rt = A.route(dd, 0, n - 1, res["distance"], res["parent_edge"])
check("dag deep chain + route", dag_ok(n, dd, 0, res, list(range(n))) and route_ok(dd, 0, n - 1, res, rt))
full = dd + [[(a := random.randrange(n - 1)), random.randrange(a + 1, n), random.randint(-10**9, 10**9)]
             for _ in range(250000 - len(dd))]
res = A.dag({"n": n, "edges": full, "source": 0})
check("dag full limit m=250000", dag_ok(n, full, 0, res))

# ---------------------------------------------------------------- repeated mixed requests via main.py
reqs = [
    {"task": "ping", "n": 0},
    {"task": "dsu", "n": 5, "operations": [[0, 1], [1, 0], [2, 2], [3, 4], [1, 3]]},
    {"task": "kruskal", "n": 4, "edges": E},
    {"task": "prim", "n": 4, "edges": E},
    {"task": "scc", "n": 6, "edges": S},
    {"task": "topo", "n": 4, "edges": C},
    {"task": "dag", "n": 5, "edges": D, "source": 0},
    {"task": "dag", "n": 4, "edges": Cy, "source": 0},
]
lines = [json.dumps(q) for q in reqs]
(ROOT / "tests" / "my_cases.jsonl").write_text("\n".join(lines * 2) + "\n", encoding="utf-8")
out = subprocess.run([sys.executable, str(ROOT / "src" / "Python" / "main.py")],
                     input="\n".join(lines * 2) + "\n", capture_output=True, text=True, encoding="utf-8")
got = [json.loads(x) for x in out.stdout.splitlines()]
check("main.py: one result line per request", len(got) == 2 * len(reqs), out.stderr)
check("main.py: ping preserved", got[0] == {"status": "ready"})
check("main.py: state reset (2nd batch equals 1st)",
      got[:len(reqs)] == got[len(reqs):] or
      all(a == b for k, (a, b) in enumerate(zip(got[:len(reqs)], got[len(reqs):])) if k not in (2, 3)))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)