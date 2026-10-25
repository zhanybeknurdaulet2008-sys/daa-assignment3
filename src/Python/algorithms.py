"""Graph algorithms for Assignment 3 (iterative, no recursion)."""

import heapq


def _find(parent, x):
    root = x
    while parent[root] != root:
        root = parent[root]
    while parent[x] != root:
        parent[x], x = root, parent[x]
    return root


def _union(parent, size, a, b):
    """Returns the new root if merged, else None."""
    a, b = _find(parent, a), _find(parent, b)
    if a == b:
        return None
    if size[a] < size[b]:
        a, b = b, a
    parent[b] = a
    size[a] += size[b]
    return a


def dsu(request):
    n = request["n"]
    operations = request["operations"]
    parent = list(range(n))
    size = [1] * n
    components = n
    largest = 1 if n else 0
    states = []
    for u, v in operations:
        root = _union(parent, size, u, v)
        if root is not None:
            components -= 1
            if size[root] > largest:
                largest = size[root]
        states.append([components, largest])
    return {"states": states}


def kruskal(request):
    n = request["n"]
    edges = request["edges"]
    parent = list(range(n))
    size = [1] * n
    cost = 0
    edge_ids = []
    for i in sorted(range(len(edges)), key=lambda k: edges[k][2]):
        u, v, w = edges[i]
        if _union(parent, size, u, v) is not None:
            cost += w
            edge_ids.append(i)
    return {"cost": cost, "edge_ids": edge_ids, "components": n - len(edge_ids)}


def prim(request):
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        if u != v:
            adj[u].append((w, v, i))
            adj[v].append((w, u, i))
    seen = [False] * n
    cost = 0
    edge_ids = []
    components = 0
    for s in range(n):
        if seen[s]:
            continue
        components += 1
        seen[s] = True
        heap = list(adj[s])
        heapq.heapify(heap)
        while heap:
            w, v, i = heapq.heappop(heap)
            if seen[v]:
                continue
            seen[v] = True
            cost += w
            edge_ids.append(i)
            for item in adj[v]:
                if not seen[item[1]]:
                    heapq.heappush(heap, item)
    return {"cost": cost, "edge_ids": edge_ids, "components": components}


def _finish_order(n, adj):
    """Iterative DFS over all vertices; returns vertices in finish order."""
    seen = [False] * n
    it = [0] * n
    order = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [s]
        while stack:
            u = stack[-1]
            if it[u] < len(adj[u]):
                v = adj[u][it[u]]
                it[u] += 1
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
            else:
                order.append(u)
                stack.pop()
    return order


def scc(request):
    n = request["n"]
    edges = request["edges"]
    g = [[] for _ in range(n)]
    gt = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v)
        gt[v].append(u)
    order = _finish_order(n, g)
    component = [-1] * n
    c = 0
    for s in reversed(order):
        if component[s] != -1:
            continue
        component[s] = c
        stack = [s]
        while stack:
            u = stack.pop()
            for v in gt[u]:
                if component[v] == -1:
                    component[v] = c
                    stack.append(v)
        c += 1
    pairs = {(component[u], component[v]) for u, v in edges if component[u] != component[v]}
    return {"component": component, "condensation": [list(p) for p in sorted(pairs)]}


def _topo(n, edges):
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e[0]].append(e[1])
    state = [0] * n  # 0 white, 1 gray, 2 black
    it = [0] * n
    post = []
    for s in range(n):
        if state[s]:
            continue
        state[s] = 1
        stack = [s]
        while stack:
            u = stack[-1]
            if it[u] < len(adj[u]):
                v = adj[u][it[u]]
                it[u] += 1
                if state[v] == 0:
                    state[v] = 1
                    stack.append(v)
                elif state[v] == 1:
                    return False, []
            else:
                state[u] = 2
                post.append(u)
                stack.pop()
    post.reverse()
    return True, post


def topo(request):
    acyclic, order = _topo(request["n"], request["edges"])
    return {"acyclic": acyclic, "order": order}


def dag(request):
    n = request["n"]
    edges = request["edges"]
    source = request["source"]
    acyclic, order = _topo(n, edges)
    if not acyclic:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    out = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        out[u].append((v, w, i))
    distance = [None] * n
    parent_edge = [-1] * n
    distance[source] = 0
    for u in order:
        if distance[u] is None:
            continue
        for v, w, i in out[u]:
            nd = distance[u] + w
            if distance[v] is None or nd < distance[v]:
                distance[v] = nd
                parent_edge[v] = i
    return {"acyclic": True, "distance": distance, "parent_edge": parent_edge}


def route(edges, source, target, distance, parent_edge):
    """Route helper. Returns {"vertices": [...], "edge_ids": [...]} or None."""
    if distance[target] is None:
        return None
    vertices = [target]
    edge_ids = []
    v = target
    while v != source:
        i = parent_edge[v]
        edge_ids.append(i)
        v = edges[i][0]
        vertices.append(v)
    vertices.reverse()
    edge_ids.reverse()
    return {"vertices": vertices, "edge_ids": edge_ids}