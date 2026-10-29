"""Backend exaustivo de referência para grafos pequenos."""

from itertools import combinations, product

from solver.canonical import canonical_heavy_key
from solver.hydrogen import distributions


def connected(vertex_count, edges):
    if vertex_count < 2:
        return True
    adjacency = {i: set() for i in range(vertex_count)}
    for (a, b), order in edges.items():
        if order:
            adjacency[a].add(b)
            adjacency[b].add(a)
    visited = set()
    stack = [0]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        stack.extend(adjacency[current] - visited)
    return len(visited) == vertex_count


def search_heavy(residual, on_solution):
    count = len(residual)
    if count < 2:
        if all(value == 0 for value in residual):
            on_solution({})
        return
    pairs = list(combinations(range(count), 2))
    remaining = list(residual)
    stopped = False

    def future_capacity(start, atom):
        return sum(
            min(3, remaining[other])
            for a, b in pairs[start:]
            if atom in (a, b)
            for other in ((b if a == atom else a),)
        )

    def visit(index, edges):
        nonlocal stopped
        if stopped:
            return
        if index == len(pairs):
            if all(value == 0 for value in remaining) and connected(
                count, edges
            ):
                stopped = on_solution(dict(edges))
            return

        a, b = pairs[index]
        maximum = min(3, remaining[a], remaining[b])
        for order in range(maximum, -1, -1):
            remaining[a] -= order
            remaining[b] -= order
            if (
                remaining[a] <= future_capacity(index + 1, a)
                and remaining[b] <= future_capacity(index + 1, b)
            ):
                edges[(a, b)] = order
                visit(index + 1, edges)
                edges.pop((a, b), None)
            remaining[a] += order
            remaining[b] += order

    visit(0, {})


def materialize_edges(problem, heavy_edges, hydrogen_distribution):
    heavy = problem.heavy_atoms
    hydrogens = problem.hydrogens
    edges = {}
    for (a, b), order in heavy_edges.items():
        if order:
            edges[tuple(sorted((heavy[a].index, heavy[b].index)))] = order

    hydrogen_index = 0
    for heavy_index, count in enumerate(hydrogen_distribution):
        for _ in range(count):
            hydrogen = hydrogens[hydrogen_index]
            hydrogen_index += 1
            edges[
                tuple(sorted((heavy[heavy_index].index, hydrogen.index)))
            ] = 1
    return edges


def enumerate_edges(problem, profile, limit):
    heavy = problem.heavy_atoms
    hydrogens = problem.hydrogens

    if not heavy:
        if len(hydrogens) == 2:
            return [{(hydrogens[0].index, hydrogens[1].index): 1}], False
        return [], False

    candidates = []
    for atom in heavy:
        allowed = profile.allowed_valences(atom)
        if not allowed:
            return None, atom
        candidates.append(allowed)

    solutions = []
    keys = set()
    search_limit = limit + 1
    for targets in product(*candidates):
        for hydrogen_distribution in distributions(
            heavy, targets, len(hydrogens)
        ):
            residual = tuple(
                target - hydrogen
                for target, hydrogen in zip(
                    targets, hydrogen_distribution
                )
            )
            def accept(heavy_edges):
                key = canonical_heavy_key(
                    heavy_edges, heavy, hydrogen_distribution
                )
                if key in keys:
                    return False
                keys.add(key)
                edges = materialize_edges(
                    problem, heavy_edges, hydrogen_distribution
                )
                solutions.append(edges)
                if len(solutions) >= search_limit:
                    return True
                return False

            search_heavy(residual, accept)
            if len(solutions) >= search_limit:
                return solutions[:limit], True
    return solutions, False
