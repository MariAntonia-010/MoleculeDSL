"""Backend opcional baseado no OR-Tools CP-SAT."""

from itertools import combinations, product
from time import monotonic

from solver.backtracking import connected, feasible, materialize_edges
from solver.canonical import column_pairs, hydrogens_sorted, is_canonical_heavy
from solver.hydrogen import distributions


def solve_distribution(
    heavy,
    residual,
    hydrogen_distribution,
    request,
    deadline,
    solutions,
    limit,
):
    from ortools.sat.python import cp_model

    count = len(heavy)
    if count < 2:
        if all(value == 0 for value in residual):
            return "candidate", {}
        return None, None

    model = cp_model.CpModel()
    pairs = list(combinations(range(count), 2))
    bonds = {}
    edges = {}
    incident = {index: [] for index in range(count)}
    for a, b in pairs:
        bond = model.new_int_var(0, min(3, residual[a], residual[b]), f"b_{a}_{b}")
        edge = model.new_bool_var(f"e_{a}_{b}")
        model.add(bond >= 1).only_enforce_if(edge)
        model.add(bond == 0).only_enforce_if(edge.Not())
        bonds[(a, b)] = bond
        edges[(a, b)] = edge
        incident[a].append(bond)
        incident[b].append(bond)
    for index, target in enumerate(residual):
        model.add(sum(incident[index]) == target)

    # Quebra de simetria por líder lexicográfico: a rotulação canônica
    # (menor vetor coluna a coluna) nunca diminui ao trocar dois átomos
    # gêmeos, de mesmo elemento, carga e quantidade de H. Só as posições
    # que tocam um dos dois mudam, então a comparação vira uma soma
    # ponderada em base 4 sobre essas posições.
    rank = {pair: index for index, pair in enumerate(column_pairs(count))}
    signatures = [
        (atom.element, atom.charge, hydrogens)
        for atom, hydrogens in zip(heavy, hydrogen_distribution)
    ]
    for i, j in pairs:
        if signatures[i] != signatures[j]:
            continue

        def swap(vertex):
            return j if vertex == i else i if vertex == j else vertex

        touched = sorted(
            (pair for pair in pairs if (i in pair or j in pair) and pair != (i, j)),
            key=rank.get,
        )
        weights = {
            pair: 4 ** (len(touched) - 1 - position)
            for position, pair in enumerate(touched)
        }
        model.add(
            sum(weights[pair] * bonds[pair] for pair in touched)
            <= sum(
                weights[pair] * bonds[tuple(sorted(map(swap, pair)))]
                for pair in touched
            )
        )

    # Conexão: o modelo só exige as n - 1 arestas necessárias, e o
    # callback descarta os grafos desconexos. Variáveis de fluxo fariam
    # o CP-SAT repetir a mesma estrutura para cada fluxo possível.
    model.add(sum(edges.values()) >= count - 1)

    stopped_for_limit = False
    stopped_for_cancel = False

    class Collector(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            nonlocal stopped_for_limit, stopped_for_cancel
            if request.cancel_check is not None and request.cancel_check():
                stopped_for_cancel = True
                self.stop_search()
                return
            heavy_edges = {
                pair: self.value(variable)
                for pair, variable in bonds.items()
                if self.value(variable)
            }
            if not connected(count, heavy_edges):
                return
            if request.filters is not None and not request.filters.accepts(
                heavy, heavy_edges, hydrogen_distribution
            ):
                return
            if not is_canonical_heavy(
                heavy_edges, heavy, hydrogen_distribution
            ):
                return
            solutions.append((heavy_edges, hydrogen_distribution))
            if len(solutions) >= limit + 1:
                stopped_for_limit = True
                self.stop_search()

    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.num_search_workers = 1
    if deadline is not None:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return "timeout", None
        solver.parameters.max_time_in_seconds = remaining
    status = solver.solve(model, Collector())
    if stopped_for_cancel:
        return "cancelled", None
    if stopped_for_limit:
        return "limit", None
    if status == cp_model.UNKNOWN:
        return "timeout", None
    return None, None


def enumerate_edges(problem, profile, limit, request):
    try:
        import ortools  # noqa: F401
    except ImportError as error:
        raise RuntimeError(
            "backend CP-SAT indisponível; instale requirements-solver.txt"
        ) from error

    heavy = problem.heavy_atoms
    hydrogens = problem.hydrogens
    if not heavy:
        if len(hydrogens) == 2 and (
            request.filters is None
            or request.filters.accepts_graph(
                ["H", "H"], [[(1, 1)], [(0, 1)]], 0
            )
        ):
            return [
                {(hydrogens[0].index, hydrogens[1].index): 1}
            ], False, None
        return [], False, None

    candidates = []
    for atom in heavy:
        allowed = profile.allowed_valences(atom)
        if not allowed:
            return None, atom, None
        candidates.append(allowed)

    deadline = (
        monotonic() + request.time_limit_seconds
        if request.time_limit_seconds is not None
        else None
    )
    candidates_found = []
    for targets in product(*candidates):
        for hydrogen_distribution in distributions(
            heavy, targets, len(hydrogens)
        ):
            if request.cancel_check is not None and request.cancel_check():
                return [], False, "cancelled"
            # Quebra de simetria: toda classe tem uma rotulação com os H
            # em ordem crescente dentro de cada grupo de mesmo elemento e
            # carga, então as outras distribuições são redundantes
            if not hydrogens_sorted(heavy, hydrogen_distribution):
                continue
            residual = tuple(
                target - hydrogen
                for target, hydrogen in zip(targets, hydrogen_distribution)
            )
            if not feasible(residual):
                continue
            reason, single = solve_distribution(
                heavy,
                residual,
                hydrogen_distribution,
                request,
                deadline,
                candidates_found,
                limit,
            )
            if reason == "candidate" and (
                request.filters is None
                or request.filters.accepts(
                    heavy, single, hydrogen_distribution
                )
            ):
                candidates_found.append((single, hydrogen_distribution))
            if reason == "limit":
                break
            if reason in ("timeout", "cancelled"):
                solutions = [
                    materialize_edges(problem, edges, h_distribution)
                    for edges, h_distribution in candidates_found[:limit]
                ]
                return solutions, False, reason
        if len(candidates_found) >= limit + 1:
            break

    solutions = [
        materialize_edges(problem, edges, h_distribution)
        for edges, h_distribution in candidates_found[:limit]
    ]
    truncated = len(candidates_found) > limit
    return solutions, truncated, None
