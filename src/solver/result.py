"""Contratos públicos de execução do solver."""

from dataclasses import dataclass, field
from enum import Enum


class SolveStatus(Enum):
    COMPLETE = "complete"
    UNSAT = "unsat"
    LIMIT_REACHED = "limit_reached"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ERROR = "error"


class Uniqueness(Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SolveRequest:
    max_solutions: int = 1
    require_unique: bool = True
    max_atoms: int = 24
    max_heavy_atoms: int = 8
    time_limit_seconds: float | None = None
    cancel_check: object | None = None
    backend: str = "reference"
    filters: object | None = None
    # Com on_solution(molecula, indice), cada solução é entregue assim que
    # aparece e não fica acumulada em SolveResult.solutions.
    on_solution: object | None = None


@dataclass
class SolveSummary:
    status: SolveStatus
    unique: Uniqueness
    complete: bool
    solutions_emitted: int
    classes_seen: int
    backend: str = "reference-backtracking"
    backend_version: str = "1"
    truncated: bool = False
    elapsed_ms: int = 0
    details: dict = field(default_factory=dict)


@dataclass
class SolveResult:
    solutions: list
    messages: list
    summary: SolveSummary
