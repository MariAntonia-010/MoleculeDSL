"""Execução da busca num processo separado.

O processo filho roda a mesma busca e manda cada solução pelo canal
assim que ela aparece. O pai repassa as soluções e, no tempo limite,
encerra o filho mesmo que ele esteja preso numa chamada nativa (como o
CP-SAT). Assim um pedido grande não trava quem chamou o solver.
"""

import multiprocessing
from dataclasses import replace
from time import monotonic

# Folga para o filho terminar sozinho depois do próprio tempo limite
GRACE_SECONDS = 2.0


def child(connection, molecule, rules, request):
    import solver

    def forward(solution, index):
        connection.send(("solution", solution, index))

    result = solver.solve(
        molecule,
        rules,
        replace(request, isolate=False, on_solution=forward, cancel_check=None),
    )
    connection.send(("result", result.messages, result.summary))
    connection.close()


def solve_isolated(molecule, rules, request):
    from solver.result import SolveResult, SolveStatus, SolveSummary, Uniqueness

    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=child,
        args=(sender, molecule, rules, replace(request, on_solution=None, cancel_check=None)),
        daemon=True,
    )
    started = monotonic()
    process.start()
    sender.close()
    deadline = (
        started + request.time_limit_seconds + GRACE_SECONDS
        if request.time_limit_seconds is not None
        else None
    )

    solutions = []
    final = None
    stop = None
    while final is None:
        if request.cancel_check is not None and request.cancel_check():
            stop = SolveStatus.CANCELLED
            break
        wait = 0.1
        if deadline is not None:
            wait = min(wait, max(0.0, deadline - monotonic()))
        if receiver.poll(wait):
            try:
                message = receiver.recv()
            except EOFError:
                break
            if message[0] == "solution":
                _, solution, index = message
                if request.on_solution is not None:
                    request.on_solution(solution, index)
                else:
                    solutions.append(solution)
            else:
                final = message
        elif deadline is not None and monotonic() >= deadline:
            stop = SolveStatus.TIMEOUT
            break
        elif not process.is_alive() and not receiver.poll():
            break

    if process.is_alive():
        process.terminate()
    process.join()

    if final is not None:
        _, messages, summary = final
        summary.details["isolated"] = True
        return SolveResult(solutions, messages, summary)

    delivered = len(solutions)
    summary = SolveSummary(
        status=stop or SolveStatus.ERROR,
        unique=Uniqueness.FALSE if delivered > 1 else Uniqueness.UNKNOWN,
        complete=False,
        solutions_emitted=delivered,
        classes_seen=delivered,
        elapsed_ms=int((monotonic() - started) * 1000),
        backend=request.backend,
        details={
            "isolated": True,
            "exit_code": process.exitcode,
        },
    )
    return SolveResult(solutions, [], summary)
