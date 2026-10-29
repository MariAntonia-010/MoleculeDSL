"""Estruturas comuns para erros produzidos durante a compilação.

Os listeners do ANTLR coletam os erros; quem chama o lexer ou o parser
decide quando exibi-los. Assim, a saída da linha de comando e os testes
usam exatamente a mesma representação.
"""

from dataclasses import dataclass

from antlr4.error.ErrorListener import ErrorListener


LIMITE_ERROS = 10


@dataclass(frozen=True)
class ErroCompilacao:
    fase: str
    codigo: str
    linha: int
    coluna: int
    mensagem: str

    def __str__(self) -> str:
        return (
            f"Erro {self.fase} [{self.codigo}] na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}"
        )


class ColetorErrosANTLR(ErrorListener):
    """Listener-base que limita e acumula erros sem imprimir no callback."""

    def __init__(self, fase: str, limite: int = LIMITE_ERROS):
        super().__init__()
        self.fase = fase
        self.limite = limite
        self.erros: list[ErroCompilacao] = []
        self.quantidade_omitida = 0

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        codigo, mensagem = self.traduzir(
            recognizer, offendingSymbol, line, column, msg, e
        )
        linha, coluna = self.ajustar_posicao(
            recognizer, offendingSymbol, line, column, e
        )
        self.adicionar(codigo, linha, coluna, mensagem)

    def traduzir(self, recognizer, offendingSymbol, line, column, msg, e):
        raise NotImplementedError

    def ajustar_posicao(self, recognizer, offendingSymbol, line, column, e):
        return line, column

    def adicionar(self, codigo: str, linha: int, coluna: int, mensagem: str):
        if len(self.erros) >= self.limite:
            self.quantidade_omitida += 1
            return
        self.erros.append(
            ErroCompilacao(self.fase, codigo, linha, coluna, mensagem)
        )

    def imprimir(self):
        for erro in self.erros:
            print(erro)
        if self.quantidade_omitida:
            plural = (
                "erro foi omitido"
                if self.quantidade_omitida == 1
                else "erros foram omitidos"
            )
            print(
                f"Aviso de compilação [LIM-001]: limite de {self.limite} erros atingido; "
                f"{self.quantidade_omitida} {plural}"
            )
