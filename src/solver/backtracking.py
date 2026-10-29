"""Backend exaustivo de referência para grafos pequenos."""

from itertools import combinations, product

from solver.canonical import hydrogens_sorted, is_canonical_heavy
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


def feasible(residual):
    # Podas seguras, válidas para qualquer perfil: cada ligação consome a
    # mesma ordem nas duas pontas, então a soma residual é par; um grafo
    # conectado com n átomos pesados precisa de n - 1 arestas, e nenhum
    # átomo pesado pode ficar sem ligação entre os pesados.
    total = sum(residual)
    if total % 2:
        return False
    count = len(residual)
    if count >= 2:
        if any(value == 0 for value in residual):
            return False
        if total // 2 < count - 1:
            return False
    return True


def search_heavy(residual, on_solution, should_stop):
    count = len(residual)
    if count < 2:
        if all(value == 0 for value in residual):
            on_solution({})
        return
    pairs = list(combinations(range(count), 2))
    remaining = list(residual)
    stopped = False
    stop_reason = None

    def future_capacity(start, atom):
        return sum(
            min(3, remaining[other])
            for a, b in pairs[start:]
            if atom in (a, b)
            for other in ((b if a == atom else a),)
        )

    def visit(index, edges):
        nonlocal stopped, stop_reason
        stop_reason = should_stop()
        if stop_reason is not None:
            stopped = True
            return
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
    return stop_reason


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


def enumerate_edges(
    problem,
    profile,
    limit,
    should_stop=lambda: None,
    filters=None,
    emit=None,
):
    # Sem emit, as soluções voltam numa lista. Com emit(edges), cada uma
    # é entregue ao ser encontrada e a lista devolvida fica vazia.
    heavy = problem.heavy_atoms
    hydrogens = problem.hydrogens

    if not heavy:
        if len(hydrogens) == 2:
            if filters is not None and not filters.accepts_bonds(
                [("H", 1, "H")], 0
            ):
                return [], False, None
            edges = {(hydrogens[0].index, hydrogens[1].index): 1}
            if emit is not None:
                emit(edges)
                return [], False, None
            return [edges], False, None
        return [], False, None

    candidates = []
    for atom in heavy:
        allowed = profile.allowed_valences(atom)
        if not allowed:
            return None, atom, None
        candidates.append(allowed)

    # Fase 5: cada classe é emitida só na sua rotulação canônica, testada
    # na hora em que a estrutura fica completa. Não há conjunto de chaves
    # crescendo com a enumeração.
    solutions = []
    found = 0
    search_limit = limit + 1
    for targets in product(*candidates):
        stop_reason = should_stop()
        if stop_reason is not None:
            return solutions, False, stop_reason
        for hydrogen_distribution in distributions(
            heavy, targets, len(hydrogens)
        ):
            if not hydrogens_sorted(heavy, hydrogen_distribution):
                continue
            residual = tuple(
                target - hydrogen
                for target, hydrogen in zip(
                    targets, hydrogen_distribution
                )
            )
            if not feasible(residual):
                continue

            def accept(heavy_edges):
                nonlocal found
                if filters is not None and not filters.accepts(
                    heavy, heavy_edges, hydrogen_distribution
                ):
                    return False
                if not is_canonical_heavy(
                    heavy_edges, heavy, hydrogen_distribution
                ):
                    return False
                found += 1
                edges = materialize_edges(
                    problem, heavy_edges, hydrogen_distribution
                )
                if emit is not None:
                    emit(edges)
                else:
                    solutions.append(edges)
                return found >= search_limit

            stop_reason = search_heavy(
                residual, accept, should_stop
            )
            if stop_reason is not None:
                return solutions, False, stop_reason
            if found >= search_limit:
                return solutions[:limit], True, None
    return solutions, False, None
