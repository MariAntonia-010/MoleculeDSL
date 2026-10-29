from dataclasses import dataclass


@dataclass
class SolverMessage:
    id: str
    line: int
    column: int
    message: str

    def __str__(self):
        return (
            f"Erro de resolução [{self.id}] na linha {self.line}, "
            f"coluna {self.column}: {self.message}"
        )
