"""Backend opcional baseado no OR-Tools CP-SAT."""

from itertools import combinations, product
from time import monotonic

from solver.backtracking import materialize_edges
from solver.canonical import canonical_heavy_key
from solver.hydrogen import distributions


def solve_distribution(
    heavy,
    residual,
    hydrogen_distribution,
    request,
    deadline,
    keys,
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

    capacity = count - 1
    flows = {}
    for a, b in pairs:
        forward = model.new_int_var(0, capacity, f"f_{a}_{b}")
        backward = model.new_int_var(0, capacity, f"f_{b}_{a}")
        model.add(forward <= capacity * edges[(a, b)])
        model.add(backward <= capacity * edges[(a, b)])
        flows[(a, b)] = forward
        flows[(b, a)] = backward
    for atom in range(count):
        outgoing = [flows[(atom, other)] for other in range(count) if other != atom]
        incoming = [flows[(other, atom)] for other in range(count) if other != atom]
        if atom == 0:
            model.add(sum(outgoing) - sum(incoming) == capacity)
        else:
            model.add(sum(incoming) - sum(outgoing) == 1)

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
            key = canonical_heavy_key(
                heavy_edges, heavy, hydrogen_distribution
            )
            if key in keys:
                return
            keys.add(key)
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
        if len(hydrogens) == 2:
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
    keys = set()
    candidates_found = []
    for targets in product(*candidates):
        for hydrogen_distribution in distributions(
            heavy, targets, len(hydrogens)
        ):
            if request.cancel_check is not None and request.cancel_check():
                return [], False, "cancelled"
            residual = tuple(
                target - hydrogen
                for target, hydrogen in zip(targets, hydrogen_distribution)
            )
            reason, single = solve_distribution(
                heavy,
                residual,
                hydrogen_distribution,
                request,
                deadline,
                keys,
                candidates_found,
                limit,
            )
            if reason == "candidate":
                key = canonical_heavy_key(
                    single, heavy, hydrogen_distribution
                )
                if key not in keys:
                    keys.add(key)
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
