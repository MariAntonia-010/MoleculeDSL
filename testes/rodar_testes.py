"""Suíte integrada: corpus principal, AST, processar() e CLI.

Uso: python testes/rodar_testes.py
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
sys.path.insert(0, SRC)

# 1. Corpus e diagnósticos esperados do projeto Main.
base = subprocess.run([sys.executable, os.path.join(RAIZ, "testar.py")], cwd=RAIZ)
if base.returncode:
    sys.exit(base.returncode)

# 2. Testes da API em memória e da AST.
from main import processar  # noqa: E402
from ast_nos import AtomoDecl, LigacaoDecl, Operador  # noqa: E402

def confere(nome, cond):
    if not cond:
        print(f"FALHOU {nome}")
        sys.exit(1)
    print(f"ok     {nome}")

with open(os.path.join(RAIZ, "exemplos", "amonio.mol"), encoding="utf-8-sig") as f:
    r = processar(f.read())
confere("processar(): amônio sem erros", r.ok)
confere("AST: molécula construída", r.ast is not None and r.ast.nome == "Ammonium")
confere("AST: multiplicador 4x preservado", any(isinstance(c, AtomoDecl) and c.multiplicador == 4 for c in r.ast.comandos))
confere("AST: repetição de ligação x4", any(isinstance(c, LigacaoDecl) and c.repeticoes == 4 for c in r.ast.comandos))
confere("AST: coluna base 0", r.ast.coluna == 0)

r = processar('molecule "Quebrada" {\n atom C\n')
confere("processar(): erro sintático devolvido", not r.ok and bool(r.erros))

# 3. CLI: --arvore deve imprimir a parse tree do ANTLR e terminar com sucesso.
p = subprocess.run([sys.executable, os.path.join(SRC, "main.py"), "--arvore", os.path.join(RAIZ, "exemplos", "agua.mol")], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
confere("CLI: --arvore", p.returncode == 0 and "programa" in p.stdout)
print("\nTestes adicionais concluídos.")
