# Assignment 3: Graph Algorithms. Analysis

Language: Python 3.14.0 (requirement: 3.12+). All DFS traversals are iterative (explicit stacks), so there is no recursion anywhere in the solution.

Notation: `n` vertices, `m` edges, `α` is the inverse Ackermann function (practically ≤ 4).

## 1. Build, run and test commands

No compilation step (Python). Run everything from the repository root.

```sh
python3 tools/run.py --setup                                   # setup check
python3 tools/run.py --check                                   # 36 public cases + state reset
python3 tests/test_my_cases.py                                 # own tests (41 checks)
python3 tools/run.py --input tests/my_cases.jsonl              # actual outputs of own JSON Lines cases
python3 tests/benchmark.py | tee tests/benchmark_results.txt   # Kruskal vs Prim benchmark
```

Files: `src/Python/algorithms.py` (six methods + `route` helper), `src/Python/main.py` (supplied JSON Lines adapter), `tests/test_my_cases.py`, `tests/my_cases.jsonl`, `tests/my_cases_actual.txt`, `tests/test_results.txt`, `tests/benchmark.py`, `tests/benchmark_results.txt`.

## 2. Common design notes

**State reset.** Every method reads only its own `request` and builds all structures (parent arrays, adjacency lists, heaps, visited arrays) as local variables. There are no module-level mutable variables or caches, so one request cannot affect the next. `main.py` handles each input line independently and `ping` is answered without touching algorithm state. The `state reset` check of `tools/run.py` and the test "main.py: state reset" (two identical batches in one process give identical results, except that Kruskal/Prim may legally differ in tied edges, so those two lines are compared only by validity in the unit tests) confirm this.

**Deep graphs.** CPython's recursion limit (about 1000 by default) would fail on a chain of 100000 vertices. All DFS passes use an explicit stack plus a per-vertex iterator index `it[u]` that remembers how many outgoing edges of `u` were already examined. A vertex is popped (finished) when `it[u]` reaches the end of its adjacency list. This gives the same finish order as recursive DFS. Memory for the stack is O(n).

**Integers.** Python integers are arbitrary precision, so sums of up to 250000 weights of magnitude 10⁹ (up to about 2.5·10¹⁴) cannot overflow.

## 3. Methods

### 3.1 dsu

**Steps.** `parent[i]=i`, `size[i]=1`, `components=n`, `largest=1` (0 if `n=0`). For each pair `[u,v]`: find both roots (with path compression); if they differ, attach the smaller tree to the larger (union by size), update `size`, decrement `components`, update `largest = max(largest, size[root])`. Append `[components, largest]` after every operation, including no-op unions (self union, repeated union).

**Invariants.** (1) Each tree of the forest is exactly one component. (2) `size[r]` equals the number of vertices in the tree with root `r` for every root `r`. (3) `components` equals the number of roots. (4) `largest` equals the maximum size over all roots; sizes only grow when trees merge, so keeping a running maximum is enough.

**Correctness.** Find returns the representative of the set; union merges two distinct sets only when the roots differ. Invariants 1-4 hold initially and are preserved by every operation, so the state recorded after each operation is exact.

**Boundaries.** `n=0` with no operations returns `[]`; `[u,u]`; repeated pairs; 250000 operations (tested).

**Complexity.** Time O((n + k) α(n)) for `k` operations; memory O(n + k) including the output.

### 3.2 kruskal

**Steps.** Sort edge indices by weight (stable, so ties keep input order), scan them, and take an edge if its endpoints are in different DSU sets (union by size + path compression). Return `cost`, the original `edge_ids` and `components = n - len(edge_ids)`.

**Invariants.** Before processing an edge, the chosen edges form a forest that is contained in some minimum spanning forest (MSF) of the whole graph, and the DSU sets are exactly the components of the chosen forest.

**Correctness.** Cut property: when an edge `e` is the lightest edge that connects two different components of the current forest, some MSF contains the chosen edges plus `e`. Edges skipped because both endpoints are already connected would close a cycle, and the heaviest edge on a cycle can be excluded from an MSF. Negative weights need no special handling because only the order matters. At the end every component of the graph is spanned, so the result is an MSF. Isolated vertices are counted in `components`.

**Boundaries.** Loops (`u=v`) are always skipped (same root); parallel edges: only one of them can be taken; negative weights; `n=0`; no edges (`components = n`); disconnected graph (forest, not tree).

**Complexity.** Time O(m log m + m α(n)) = O(m log m); memory O(n + m).

### 3.3 prim

**Steps.** Build an adjacency list (loops are skipped). For each unvisited vertex `s` (restart for every component, so a forest is produced and `components` is incremented): mark `s` visited, push its edges `(w, to, id)` into a binary heap, then repeatedly pop the lightest edge; if `to` is already visited, discard it (lazy deletion); otherwise visit `to`, add `w` to the cost, record `id`, and push the edges of `to` that lead to unvisited vertices.

**Invariants.** (1) Visited vertices of the current component form a tree whose edges are in some MSF. (2) The heap contains every edge that leaves the visited set (plus possibly stale edges that go inside it). Therefore the minimum non-stale heap edge is the lightest edge crossing the cut (visited, unvisited).

**Correctness.** By the cut property, the lightest edge crossing the cut (visited set, rest of the component) belongs to some MSF containing the current tree. The loop ends when no edge leaves the visited set, i.e. when the whole component is spanned. Running it from every unvisited vertex yields an MSF of the whole graph.

**Boundaries.** Same as Kruskal; isolated vertices form their own component with no edges; negative weights are fine because the heap order is by weight only.

**Complexity.** Each edge is pushed at most twice (once per endpoint), so time O(m log m) = O((n + m) log n) and memory O(n + m). Unlike Kruskal there is no sorting, but there are many heap operations on tuples.

### 3.4 scc (Kosaraju)

**Steps.** (1) Build `G` and its transpose `Gᵀ`. (2) First pass: iterative DFS on `G` over all vertices, recording the finish order. (3) Second pass: process vertices in reverse finish order; for every vertex without a label, run an iterative DFS/stack traversal on `Gᵀ` and assign a new label to everything reached. (4) Condensation: the set of distinct pairs `(component[u], component[v])` over edges with different labels, sorted and de-duplicated.

**Invariants.** When the second pass starts a traversal from vertex `s`, `s` has the latest finish time among unlabeled vertices; all vertices reached in `Gᵀ` that are still unlabeled form exactly the SCC of `s`.

**Correctness.** The component whose vertex finishes last in `G` is a source component of the condensation DAG, so in `Gᵀ` it is a sink: traversal from it cannot leave its own component. Removing it and repeating the argument on the remaining vertices gives the SCCs one by one. Labels are numbered by discovery order, which is accepted as "any valid labeling".

**Boundaries.** Self-loops (do not create cross-component pairs), duplicate edges (collapsed by the set), `n=0`, isolated vertices (singleton components), a 100000-vertex chain and a 100000-vertex cycle (tested).

**Complexity.** Time O(n + m) for the traversals plus O(c log c) for sorting the `c` distinct condensation pairs (`c ≤ m`); memory O(n + m).

### 3.5 topo (three-state DFS)

**Steps.** States: 0 white, 1 gray (on the stack), 2 black (finished). Run iterative DFS from every white vertex. If an edge leads to a gray vertex, a directed cycle exists: return `acyclic=false`, `order=[]`. A vertex becomes black when all its edges are processed and is appended to `post`. At the end the order is `post` reversed.

**Invariants.** Gray vertices are exactly the vertices on the current DFS path (stack); black vertices have all descendants finished.

**Correctness.** A directed graph has a cycle iff DFS meets a back edge (an edge to a gray vertex). If there is none, for every edge `u→v` the vertex `v` finishes before `u` (white: finished as a descendant; black: already finished; gray is excluded), so reverse finish order is a topological order. The loop covers every start vertex, so cycles in components that are unreachable from other vertices are also found.

**Boundaries.** Self-loop (edge to itself is to a gray vertex, cycle), parallel edges (not a cycle), isolated vertices, disconnected cycles, empty graph, deep chain/cycle with 100000 vertices.

**Complexity.** Time O(n + m); memory O(n + m).

### 3.6 dag (shortest paths in a DAG)

**Steps.** (1) Run `topo` on the whole graph, not only on the part reachable from `source`; if a cycle exists anywhere, return `{"acyclic": false, "distance": [], "parent_edge": []}`. (2) `distance[source]=0`, all others `null`, `parent_edge=-1`. (3) Process vertices in topological order; skip vertices with `null` distance; for each outgoing edge `(u→v, w, id)` relax: if `distance[v]` is `null` or `distance[u]+w < distance[v]`, set `distance[v]` and `parent_edge[v]=id`.

**Invariants.** When vertex `u` is processed, `distance[u]` is final (all its predecessors were processed earlier and relaxed their edges into `u`). `parent_edge[v]` is the original index of an edge `p→v` such that `distance[p] + w = distance[v]`.

**Correctness.** In topological order every path to `v` goes through vertices processed before `v`, so by induction `distance[v]` is the minimum over all incoming edges of `distance[p]+w`, i.e. the shortest path length (negative weights are fine because no vertex is revisited). Unreachable vertices never get relaxed and keep `null` / `-1`. The `source` has `distance 0` and `parent_edge -1`. Cycles not reachable from `source` are still reported because the cycle check covers the whole graph.

**Boundaries.** `n=1`; unreachable cycle (tested: `dag cycle unreachable from source`); self-loop; parallel edges and ties (strict `<` keeps the first edge found); weights ±10⁹ with large sums; 100000-vertex chain.

**Complexity.** Time O(n + m); memory O(n + m).

### 3.7 Route helper `route(edges, source, target, distance, parent_edge)`

Returns `None` if `distance[target]` is `null`; otherwise follows `parent_edge` from `target` back to `source`, using `edges[id][0]` as the previous vertex, and returns `{"vertices": [...], "edge_ids": [...]}` from source to target. Time O(length of the route), memory O(length).

Calls on the DAG `D = [[0,1,2],[0,1,1],[1,2,-3],[0,2,5],[3,4,1]]`, `source=0`, with result `distance=[0,1,-2,null,null]`, `parent_edge=[-1,1,2,-1,-1]`:

| Call | Result | Why |
|---|---|---|
| `route(D,0,2,...)` reachable target | `{"vertices":[0,1,2],"edge_ids":[1,2]}` | cost 1 + (-3) = -2 = `distance[2]` (edge 1 is the cheaper parallel edge; edge 3 would cost 5) |
| `route(D,0,0,...)` source | `{"vertices":[0],"edge_ids":[]}` | loop stops immediately |
| `route(D,0,3,...)` unreachable target | `None` | `distance[3]` is `null` |

Tied/parallel edges: `Tt = [[0,1,1],[0,1,1],[1,2,1],[0,2,2]]`, `source=0`. Both parallel edges 0 and 1 give `distance[1]=1`, and both `0→1→2` and `0→2` give `distance[2]=2`. With strict `<` relaxation the first edge found is kept, so the result is `parent_edge=[-1,0,3]` and `route(Tt,0,2,...)` returns `{"vertices":[0,2],"edge_ids":[3]}`. Any tied alternative would also be valid; the test `dag + route tied/parallel` checks validity (exact distances, edge endpoints, route cost equals `distance[target]`), not one specific route.

## 4. Testing

`tests/test_my_cases.py` (41 checks, all passed; output in `tests/test_results.txt`). Expected answers are justified in comments next to each case. Non-unique answers (MSF edge sets, topological orders, SCC labels, shortest-path witnesses) are checked by validators, not by equality:

- MSF: no repeated or out-of-range edge ids, no cycle, total weight equals the expected optimum, `components` is correct.
- Topological order: contains every vertex once and respects every edge.
- SCC: the partition equals the expected partition regardless of label numbers; condensation pairs are distinct and match the labels.
- DAG: exact distances, each `parent_edge` ends at its vertex and is tight (`distance[u]+w = distance[v]`), and no edge can still be relaxed.
- Negative tests show the validators reject an invalid witness (repeated edge in MSF, reversed topological order, wrong DAG parent edge). Alternative valid answers (tied optima) are accepted.

Coverage: empty graphs, isolates, loops, parallel edges, negative weights, ±10⁹ weights, tied optima, `n=100000` chains and cycles, full limits (`m=250000` for Kruskal/Prim/DAG, 250000 DSU operations), a cycle unreachable from the source, and repeated mixed requests through `main.py` (`tests/my_cases.jsonl`, actual output in `tests/my_cases_actual.txt`).

## 5. Benchmark: Kruskal vs Prim

**Setup.** Random connected graphs: a random spanning tree (vertex `i` is connected to a random earlier vertex) plus random extra edges (loops and parallel edges possible); weights uniform in [-10⁹, 10⁹]. The generator uses `random.Random(2026)`, and one graph is generated per size; Kruskal and Prim run on exactly the same graph. Both methods returned the same cost on every graph (the script asserts it).

- Command: `python3 tests/benchmark.py | tee tests/benchmark_results.txt`
- Environment: macOS 14.6 (arm64, Apple Silicon; `platform.processor()` reports `arm`), Python 3.14.0 (CPython). Add your exact Mac model/chip and RAM here: `<MacBook Air 13, chip m3, RAM 8>`.
- Timer: `time.perf_counter()`; `gc.collect()` before each timed run.
- Warm-up: 1 untimed run per method per size.
- Timed runs: 5 per method per size (requirement: at least 3); the median is reported.
- Timing boundary: only the call `algorithms.kruskal(request)` / `algorithms.prim(request)`. Graph generation, JSON parsing, process start-up and result printing are excluded. There is no compilation step in Python.

**Raw timings (seconds).**

| n | m | Kruskal runs | Prim runs |
|---|---|---|---|
| 1000 | 5000 | 0.0023, 0.0023, 0.0023, 0.0023, 0.0022 | 0.0046, 0.0046, 0.0045, 0.0045, 0.0045 |
| 10000 | 50000 | 0.033, 0.0271, 0.027, 0.0264, 0.0263 | 0.0618, 0.0624, 0.0616, 0.0613, 0.0617 |
| 100000 | 250000 | 0.3374, 0.3292, 0.3422, 0.3404, 0.3475 | 0.9996, 1.0162, 1.0084, 1.0702, 1.0499 |

**Medians.**

| n | m | Kruskal median (s) | Prim median (s) | Prim / Kruskal |
|---|---|---|---|---|
| 1000 | 5000 | 0.0023 | 0.0045 | about 2.0x |
| 10000 | 50000 | 0.0270 | 0.0617 | about 2.3x |
| 100000 | 250000 | 0.3404 | 1.0162 | about 3.0x |

**Discussion.** Both methods are O(m log m) in theory, and the measured times grow roughly in line with `m` (with a log factor and cache effects at the largest size). In this Python implementation Kruskal is faster at all three sizes. A plausible explanation (not separately profiled here) is that Kruskal's heavy step is one C-level `sorted` call, while Prim performs many Python-level heap pushes/pops of tuples and builds an adjacency structure with two entries per edge; Prim also uses more memory (O(n+m) adjacency lists plus the heap). The gap widens with size (about 2.0x → 3.0x). The result applies to this implementation, this input family (sparse random graphs, `m ≈ 2.5n–5n`) and this machine; on dense graphs or in another language the ranking could differ. The first Kruskal run at `n=10000` (0.033 s) is slower than the others, which is a typical remaining warm-up/cache effect even after one warm-up run; medians reduce its influence.

## 6. Sources and AI assistance

Sources: course lectures and the assignment specification; the standard textbook algorithms (Kruskal, Prim, Kosaraju, DFS-based topological sort, DAG shortest paths, union-find with path compression and union by size) as described in *Introduction to Algorithms* (Cormen et al.). The JSON Lines adapter (`main.py`), `tools/run.py` and the public tests were supplied by the course template.

AI assistance: Claude (Anthropic) was used as an assistant for drafting the algorithm code, the own-test script, the benchmark script and this document. All code was run locally; the public checks (36 cases + state reset), the 41 own checks and the benchmark were executed by the student, and the numbers above are from the student's actual runs. `<Nurdaulet:I worked on it together with Claude.>`
