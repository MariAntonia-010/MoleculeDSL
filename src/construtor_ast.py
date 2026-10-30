import os
import sys

# sintatico.py (via lexico.py) adiciona a pasta "gerado" ao caminho
from sintatico import analisar
from MoleculeDSLParser import MoleculeDSLParser
from MoleculeDSLVisitor import MoleculeDSLVisitor

from ast_nos import (
    AnelDecl,
    AtomoDecl,
    EstereoDecl,
    LigacaoDecl,
    Molecula,
    Operador,
    Referencia,
    TipoEspecie,
    TipoReferencia,
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
        cabecalho = ctx.cabecalho()
        # Tira as aspas do TEXTO
        nome = cabecalho.TEXTO().getText()[1:-1]
        tipo, carga_total, legacy = self.visit(cabecalho)
        eletrons_desemparelhados = None
        if ctx.desemparelhados() is not None:
            eletrons_desemparelhados = int(
                ctx.desemparelhados().INTEIRO().getText()
            )
        comandos = [self.visit(c) for c in ctx.comando()]
        return Molecula(
            nome=nome,
            linha=ctx.start.line,
            coluna=ctx.start.column,
            comandos=comandos,
            tipo=tipo,
            carga_total=carga_total,
            eletrons_desemparelhados=eletrons_desemparelhados,
            declaracao_legacy=legacy,
        )

    def visitCabecalho(self, ctx):
        if ctx.SPECIES() is None:
            return TipoEspecie.MOLECULA, None, True
        if ctx.MOLECULAR_ION() is not None:
            return (
                TipoEspecie.ION_MOLECULAR,
                self.visit(ctx.cargaEspecie()),
                False,
            )
        if ctx.IONIC_SOLID() is not None:
            return TipoEspecie.SOLIDO_IONICO, 0, False
        if ctx.COVALENT_NETWORK() is not None:
            return TipoEspecie.REDE_COVALENTE, 0, False
        if ctx.METALLIC_SOLID() is not None:
            return TipoEspecie.SOLIDO_METALICO, 0, False
        return TipoEspecie.MOLECULA, 0, False

    def visitCargaEspecie(self, ctx):
        valor = int(ctx.INTEIRO().getText())
        return valor if ctx.sinal().MAIS() is not None else -valor

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
        tipo = (
            TipoReferencia.ELEMENTO
            if token.type == P.IDENT
            else TipoReferencia.NOME
        )
        return Referencia(token.text, tipo, token.line, token.column)

    def visitAnel(self, ctx):
        nomes = [
            Referencia(
                n.getText(),
                TipoReferencia.NOME,
                n.symbol.line,
                n.symbol.column,
            )
            for n in ctx.NOME()
        ]
        return AnelDecl(nomes, ctx.start.line, ctx.start.column)

    def visitEstereo(self, ctx):
        operador = None
        if ctx.operador() is not None:
            operador = OPERADORES[ctx.operador().start.type]
        descritor = ctx.descritor().start
        return EstereoDecl(
            [self.visit(r) for r in ctx.referencia()],
            operador,
            descritor.text,
            ctx.start.line,
            ctx.start.column,
            descritor.column,
        )


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
