import os
import sys

# sintatico.py (via lexico.py) adiciona a pasta "gerado" ao caminho
from sintatico import analisar
from MoleculeDSLParser import MoleculeDSLParser
from MoleculeDSLVisitor import MoleculeDSLVisitor

from ast_nos import (
    AnelDecl,
    AtomoDecl,
    ConfiguracaoDecl,
    EstereoDecl,
    LigacaoDecl,
    Especie,
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
        # Os nomes de todos os blocos, para distinguir um bloco inexistente
        # de um declarado depois de quem o usa
        self.todos_os_nomes = [m.cabecalho().TEXTO().getText()[1:-1] for m in ctx.molecula()]
        self.blocos = []
        for molecula in ctx.molecula():
            self.blocos.append(self.visit(molecula))
        return self.blocos

    def resolver_bloco(self, decl, nome_proprio):
        # atom "Nome": copia elemento, carga e massa do bloco anterior
        if decl.bloco == nome_proprio:
            decl.situacao_bloco = "proprio"
            return
        anterior = next((b for b in getattr(self, "blocos", []) if b.nome == decl.bloco), None)
        if anterior is None:
            todos = getattr(self, "todos_os_nomes", [])
            decl.situacao_bloco = "depois" if decl.bloco in todos else "inexistente"
            return
        atomos = [c for c in anterior.comandos if isinstance(c, AtomoDecl)]
        if anterior.tipo not in (TipoEspecie.ATOMO, TipoEspecie.ION_MONOATOMICO) or len(atomos) != 1:
            decl.situacao_bloco = "tipo"
            return
        origem = atomos[0]
        decl.elemento, decl.carga, decl.massa = origem.elemento, origem.carga, origem.massa
        decl.situacao_bloco = "ok"

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
        for comando in comandos:
            if isinstance(comando, AtomoDecl) and comando.bloco is not None:
                self.resolver_bloco(comando, nome)
        # Nome automático: o mesmo índice por elemento que o modelo usa
        contagem = {}
        for comando in comandos:
            if isinstance(comando, AtomoDecl) and comando.multiplicador >= 1:
                primeiro = contagem.get(comando.elemento, 0) + 1
                contagem[comando.elemento] = primeiro + comando.multiplicador - 1
                ultimo = contagem[comando.elemento]
                comando.nome_automatico = (
                    f"{comando.elemento}#{primeiro}"
                    if primeiro == ultimo
                    else f"{comando.elemento}#{primeiro}…{comando.elemento}#{ultimo}"
                )
        return Especie(
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
        if ctx.MONATOMIC_ION() is not None:
            return (
                TipoEspecie.ION_MONOATOMICO,
                self.visit(ctx.cargaEspecie()),
                False,
            )
        if ctx.ATOM() is not None:
            return TipoEspecie.ATOMO, 0, False
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
        massa = int(ctx.INTEIRO().getText()) if ctx.INTEIRO() is not None else None

        if ctx.TEXTO() is not None:
            # atom "Carbono-13": o elemento vem do bloco (resolver_bloco);
            # até lá, '?' marca que ainda não se sabe
            return AtomoDecl(
                multiplicador, "?", 0, nome, ctx.start.line, ctx.start.column,
                bloco=ctx.TEXTO().getText()[1:-1],
            )

        return AtomoDecl(
            multiplicador,
            ctx.IDENT().getText(),
            carga,
            nome,
            ctx.start.line,
            ctx.start.column,
            massa=massa,
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

    def visitConfiguracao(self, ctx):
        nucleo = ctx.nucleo().IDENT().getText() if ctx.nucleo() is not None else None
        return ConfiguracaoDecl(
            self.visit(ctx.referencia()),
            nucleo,
            [s.getText() for s in ctx.SUBCAMADA()],
            ctx.start.line,
            ctx.start.column,
        )

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


def construir_programa(arvore):
    """Lista de Especie, uma por bloco, na ordem do arquivo."""
    return ConstrutorAST().visit(arvore)


def construir(arvore):
    # Primeiro bloco: o formato de antes, para quem trata um bloco só
    return construir_programa(arvore)[0]


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
