"""Mede os backends do solver numa lista fixa de fórmulas.

Uso: python tests/benchmark_solver.py [--backend=reference|cpsat|ambos]

Cada linha mostra a fórmula, a quantidade de classes encontradas, a
esperada (isômeros constitucionais conhecidos) e o tempo. Uma contagem
diferente da esperada marca a linha com DIVERGE e o código de saída é 1.
"""

import os
import re
import sys
from time import monotonic

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

import semantico  # noqa: E402
import solver  # noqa: E402
from ast_nos import AtomoDecl, Molecula  # noqa: E402

# Contagens da literatura (isômeros constitucionais, sem estereoisômeros)
FORMULAS = [
    ("C4H10", 2),
    ("C5H12", 3),
    ("C6H14", 5),
    ("C7H16", 9),
    ("C8H18", 18),
    ("C4H8", 5),
    ("C5H10", 10),
    ("C6H12", 25),
    ("C4H6", 9),
    ("C6H6", 217),
    ("C3H6O", 9),
    ("C3H9N", 4),
]


def molecula(formula):
    comandos = []
    for elemento, quantidade in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        for indice in range(int(quantidade or 1)):
            comandos.append(
                AtomoDecl(1, elemento, 0, f"{elemento.lower()}{indice + 1}", 1, 0)
            )
    return Molecula(formula, 1, 0, comandos)


def medir(formula, backend, regras):
    inicio = monotonic()
    resultado = solver.solve(
        molecula(formula),
        regras,
        solver.SolveRequest(
            max_solutions=100000,
            require_unique=False,
            backend=backend,
            time_limit_seconds=120,
        ),
    )
    return resultado.summary.solutions_emitted, monotonic() - inicio


def main():
    escolha = "reference"
    for argumento in sys.argv[1:]:
        if argumento.startswith("--backend="):
            escolha = argumento.split("=", 1)[1]
    backends = ["reference", "cpsat"] if escolha == "ambos" else [escolha]
    regras = semantico.carregar_valencias()
    diverge = False
    for backend in backends:
        print(f"backend {backend}")
        for formula, esperado in FORMULAS:
            encontrado, segundos = medir(formula, backend, regras)
            marca = ""
            if encontrado != esperado:
                marca = "  DIVERGE"
                diverge = True
            print(f"  {formula:8} {encontrado:5} (esperado {esperado}) "
                  f"{segundos:7.2f}s{marca}")
    sys.exit(1 if diverge else 0)


if __name__ == "__main__":
    main()
