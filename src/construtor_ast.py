import os
import sys

# sintatico.py (via lexico.py) adiciona a pasta "gerado" ao caminho
from sintatico import analisar
from MoleculeDSLParser import MoleculeDSLParser
from MoleculeDSLVisitor import MoleculeDSLVisitor

from ast_nos import (
    AnelDecl,
    AtomoDecl,
    LigacaoDecl,
    Molecula,
    Operador,
    Referencia,
    formatar,
)


P = MoleculeDSLParser

OPERADORES = {
    P.LIGACAO: Operador.SIMPLES,
    P.DUPLA: Operador.DUPLA,
    P.TRIPLA: Operador.TRIPLA,
    P.COORDENADA: Operador.COORDENADA,
    P.METALICA: Operador.METALICA,
}


class ConstrutorAST(MoleculeDSLVisitor):
    # Só deve receber árvores sem erros léxicos ou sintáticos

    def visitPrograma(self, ctx):
        return self.visit(ctx.molecula())

    def visitMolecula(self, ctx):
        # Tira as aspas do TEXTO
        nome = ctx.TEXTO().getText()[1:-1]
        comandos = [self.visit(c) for c in ctx.comando()]
        return Molecula(nome, ctx.start.line, ctx.start.column, comandos)

    def visitComando(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitAtomo(self, ctx):
        # "4x" vira 4; sem multiplicador vale 1
        multiplicador = 1
        if ctx.MULTIPLICADOR_ATOMO() is not None:
            multiplicador = int(ctx.MULTIPLICADOR_ATOMO().getText()[:-1])

        carga = 0
        if ctx.carga() is not None:
            carga = self.visit(ctx.carga())

        nome = ctx.NOME().getText() if ctx.NOME() is not None else None

        return AtomoDecl(
            multiplicador,
            ctx.IDENT().getText(),
            carga,
            nome,
            ctx.start.line,
            ctx.start.column,
        )

    def visitCarga(self, ctx):
        # "(+1)" vira 1 e "(-1)" vira -1
        valor = int(ctx.INTEIRO().getText())
        if ctx.sinal().MAIS() is None:
            valor = -valor
        return valor

    def visitLigacao(self, ctx):
        # "x4" vira 4; sem repetição vale 1
        repeticoes = 1
        if ctx.REPETICAO_LIGACAO() is not None:
            repeticoes = int(ctx.REPETICAO_LIGACAO().getText()[1:])

        return LigacaoDecl(
            self.visit(ctx.referencia(0)),
            OPERADORES[ctx.operador().start.type],
            self.visit(ctx.referencia(1)),
            repeticoes,
            ctx.start.line,
            ctx.start.column,
        )

    def visitReferencia(self, ctx):
        token = ctx.start
        tipo = "elemento" if token.type == P.IDENT else "nome"
        return Referencia(token.text, tipo, token.line, token.column)

    def visitAnel(self, ctx):
        nomes = [
            Referencia(n.getText(), "nome", n.symbol.line, n.symbol.column)
            for n in ctx.NOME()
        ]
        return AnelDecl(nomes, ctx.start.line, ctx.start.column)


def construir(arvore):
    return ConstrutorAST().visit(arvore)


def main():
    if len(sys.argv) != 2:
        print("Uso: python src/construtor_ast.py <arquivo>")
        sys.exit(1)

    caminho = sys.argv[1]

    if not os.path.isfile(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        sys.exit(1)

    arvore = analisar(caminho)

    if arvore is None:
        sys.exit(1)

    print(formatar(construir(arvore)))


if __name__ == "__main__":
    main()
