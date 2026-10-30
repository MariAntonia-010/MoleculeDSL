"""Fachada compatível e API estruturada do solver."""

from dataclasses import replace
from time import monotonic

from ast_nos import (
    AtomoDecl,
    LigacaoDecl,
    Operador,
    Referencia,
    TipoReferencia,
)
from solver.backtracking import enumerate_edges as enumerate_reference
from solver.chemical_profile import from_rules
from solver.filters import Fragment, SolveFilters, parse_fragment
from solver.messages import SolverMessage
from solver.problem import normalize
from solver.result import (
    SolveRequest,
    SolveResult,
    SolveStatus,
    SolveSummary,
    Uniqueness,
)
from solver.serialization import (
    result_dict,
    result_json,
    result_jsonl,
    solution_jsonl,
    summary_dict,
    summary_json,
    summary_jsonl,
)


OPERATOR_BY_ORDER = {
    1: Operador.SIMPLES,
    2: Operador.DUPLA,
    3: Operador.TRIPLA,
}


def build_molecule(problem, edges):
    molecule = problem.molecule
    atoms = [
        AtomoDecl(
            multiplicador=1,
            elemento=atom.element,
            carga=atom.charge,
            nome=atom.name,
            linha=atom.line,
            coluna=atom.column,
            massa=atom.mass,
        )
        for atom in problem.atoms
    ]
    bonds = []
    for (a, b), order in sorted(edges.items()):
        if not order:
            continue
        bonds.append(
            LigacaoDecl(
                origem=Referencia(
                    problem.atoms[a].name,
                    TipoReferencia.NOME,
                    molecule.linha,
                    molecule.coluna,
                ),
                operador=OPERATOR_BY_ORDER[order],
                destino=Referencia(
                    problem.atoms[b].name,
                    TipoReferencia.NOME,
                    molecule.linha,
                    molecule.coluna,
                ),
                repeticoes=1,
                linha=molecule.linha,
                coluna=molecule.coluna,
            )
        )
    return replace(molecule, comandos=[*atoms, *bonds])


def error_result(message, status=SolveStatus.ERROR):
    return SolveResult(
        [],
        [message],
        SolveSummary(
            status=status,
            unique=Uniqueness.UNKNOWN,
            complete=True,
            solutions_emitted=0,
            classes_seen=0,
        ),
    )


def solve(molecule, rules, request=None):
    started = monotonic()
    request = request or SolveRequest()
    if request.isolate:
        from solver.isolation import solve_isolated

        result = solve_isolated(molecule, rules, request)
        if result.summary.status is SolveStatus.ERROR and not result.messages:
            result.messages.append(
                SolverMessage(
                    "SOLVER-006",
                    molecule.linha,
                    molecule.coluna,
                    "o processo isolado da busca terminou sem resultado",
                )
            )
        return result
    problem, invalid_command = normalize(molecule)
    if invalid_command is not None:
        return error_result(
            SolverMessage(
                "SOLVER-001",
                invalid_command.linha,
                invalid_command.coluna,
                "--resolver aceita somente declarações de átomos",
            )
        )
    if not problem.atoms:
        return error_result(
            SolverMessage(
                "SOLVER-001",
                molecule.linha,
                molecule.coluna,
                "não há átomos para resolver",
            )
        )
    if (
        len(problem.atoms) > request.max_atoms
        or len(problem.heavy_atoms) > request.max_heavy_atoms
    ):
        return error_result(
            SolverMessage(
                "SOLVER-001",
                molecule.linha,
                molecule.coluna,
                f"o solver aceita no máximo {request.max_atoms} átomos e "
                f"{request.max_heavy_atoms} átomos pesados",
            )
        )

    profile = from_rules(rules)
    limit = 2 if request.require_unique else request.max_solutions
    deadline = (
        started + request.time_limit_seconds
        if request.time_limit_seconds is not None
        else None
    )

    def should_stop():
        if request.cancel_check is not None and request.cancel_check():
            return "cancelled"
        if deadline is not None and monotonic() >= deadline:
            return "timeout"
        return None

    # Toda solução passa por aqui. A busca procura limit + 1 classes para
    # saber se houve truncamento, mas a excedente nunca é entregue.
    solutions = []
    emitted = 0

    def emit(edge_set):
        nonlocal emitted
        if emitted >= limit:
            emitted += 1
            return
        emitted += 1
        solution = build_molecule(problem, edge_set)
        if request.on_solution is not None:
            request.on_solution(solution, emitted)
        else:
            solutions.append(solution)

    backend_name = request.backend
    backend_version = "1"
    try:
        if request.backend == "reference":
            edges, extra, stop_reason = enumerate_reference(
                problem,
                profile,
                limit,
                should_stop,
                filters=request.filters,
                emit=emit,
            )
            backend_name = "reference-backtracking"
        elif request.backend == "cpsat":
            import ortools
            from solver.cpsat import enumerate_edges as enumerate_cpsat

            backend_version = ortools.__version__
            edges, extra, stop_reason = enumerate_cpsat(
                problem, profile, limit, request
            )
            # O CP-SAT devolve a lista ao final; a entrega por solução
            # acontece depois da busca.
            if edges is not None:
                for edge_set in edges:
                    emit(edge_set)
                if extra:
                    emitted += 1
            backend_name = "ortools-cpsat"
        else:
            return error_result(
                SolverMessage(
                    "SOLVER-006",
                    molecule.linha,
                    molecule.coluna,
                    f"backend desconhecido '{request.backend}'",
                )
            )
    except RuntimeError as error:
        return error_result(
            SolverMessage(
                "SOLVER-006",
                molecule.linha,
                molecule.coluna,
                str(error),
            )
        )
    if edges is None:
        atom = extra
        return error_result(
            SolverMessage(
                "SOLVER-002",
                atom.line,
                atom.column,
                f"não há valência confirmada para resolver {atom.element} "
                f"com carga {atom.charge:+d}",
            )
        )
    truncated = bool(extra) or emitted > limit
    delivered = min(emitted, limit)
    if not delivered and stop_reason is None:
        return error_result(
            SolverMessage(
                "SOLVER-003",
                molecule.linha,
                molecule.coluna,
                "nenhuma estrutura conectada satisfaz as valências conhecidas"
                + (
                    " e os filtros pedidos"
                    if request.filters is not None and request.filters.active
                    else ""
                ),
            ),
            SolveStatus.UNSAT,
        )

    complete = not truncated and stop_reason is None
    if delivered == 1 and complete:
        unique = Uniqueness.TRUE
    elif delivered > 1:
        unique = Uniqueness.FALSE
    else:
        unique = Uniqueness.UNKNOWN
    if stop_reason == "timeout":
        status = SolveStatus.TIMEOUT
    elif stop_reason == "cancelled":
        status = SolveStatus.CANCELLED
    else:
        status = (
            SolveStatus.COMPLETE
            if complete
            else SolveStatus.LIMIT_REACHED
        )
    summary = SolveSummary(
        status=status,
        unique=unique,
        complete=complete,
        solutions_emitted=delivered,
        classes_seen=delivered + (1 if truncated else 0),
        truncated=truncated,
        elapsed_ms=int((monotonic() - started) * 1000),
        backend=backend_name,
        backend_version=backend_version,
        details={
            "chemical_profile": profile.name,
            "chemical_profile_version": profile.version,
            "chemical_profile_digest": profile.digest,
            "filters": (
                request.filters.describe()
                if request.filters is not None
                else []
            ),
        },
    )
    return SolveResult(solutions, [], summary)


def resolver(molecule, rules):
    result = solve(
        molecule,
        rules,
        SolveRequest(max_solutions=2, require_unique=True),
    )
    if result.messages:
        return None, result.messages
    if result.summary.status in (
        SolveStatus.TIMEOUT,
        SolveStatus.CANCELLED,
    ):
        return None, [
            SolverMessage(
                "SOLVER-005",
                molecule.linha,
                molecule.coluna,
                "a busca foi interrompida antes de provar a unicidade",
            )
        ]
    if result.summary.unique is not Uniqueness.TRUE:
        return None, [
            SolverMessage(
                "SOLVER-004",
                molecule.linha,
                molecule.coluna,
                "a fórmula admite múltiplas estruturas; declare as ligações",
            )
        ]
    return result.solutions[0], []


def enumerar(molecule, rules, limite=10):
    result = solve(
        molecule,
        rules,
        SolveRequest(max_solutions=limite, require_unique=False),
    )
    return result.solutions, result.messages, result.summary.truncated


__all__ = [
    "Fragment",
    "SolveFilters",
    "SolveRequest",
    "SolveResult",
    "SolveStatus",
    "SolveSummary",
    "Uniqueness",
    "enumerar",
    "parse_fragment",
    "resolver",
    "result_dict",
    "result_json",
    "result_jsonl",
    "solution_jsonl",
    "solve",
    "summary_dict",
    "summary_json",
    "summary_jsonl",
]
