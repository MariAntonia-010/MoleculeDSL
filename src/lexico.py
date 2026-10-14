import os
import sys

from antlr4 import FileStream, CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener


# Localiza a pasta raiz do projeto
PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adiciona a pasta com o código gerado pelo ANTLR
PASTA_GERADO = os.path.join(PASTA_RAIZ, "gerado")
sys.path.insert(0, PASTA_GERADO)

from MoleculeDSL import MoleculeDSL


class ErroLexico(ErrorListener):
    def __init__(self):
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.erros.append((line, column, msg))
        print(f"Erro léxico na linha {line}, coluna {column}: {msg}")


def analisar(caminho):
    entrada = FileStream(caminho, encoding="utf-8")

    lexer = MoleculeDSL(entrada)

    # Substitui a mensagem padrão de erro do ANTLR
    lexer.removeErrorListeners()
    erros = ErroLexico()
    lexer.addErrorListener(erros)

    fluxo = CommonTokenStream(lexer)
    fluxo.fill()

    quantidade = 0

    for token in fluxo.tokens:
        if token.type == Token.EOF:
            continue

        nome_token = lexer.symbolicNames[token.type]

        print(
            f"{nome_token} {repr(token.text)} "
            f"linha {token.line}"
        )

        quantidade += 1

    print(f"\n{quantidade} tokens reconhecidos")

    if erros.erros:
        return False

    return True


def main():
    if len(sys.argv) != 2:
        print("Uso: python src/lexico.py <arquivo>")
        sys.exit(1)

    caminho = sys.argv[1]

    if not os.path.isfile(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        sys.exit(1)

    sucesso = analisar(caminho)

    if not sucesso:
        sys.exit(1)


if __name__ == "__main__":
    main()