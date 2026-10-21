import os
import sys

from antlr4 import FileStream, CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener

# lexico.py adiciona a pasta "gerado" ao caminho de importação
from lexico import ErroLexico
from MoleculeDSLLexer import MoleculeDSLLexer
from MoleculeDSLParser import MoleculeDSLParser


P = MoleculeDSLParser

OPERADORES = {P.LIGACAO, P.DUPLA, P.TRIPLA, P.COORDENADA, P.METALICA}
REFERENCIAS = {P.IDENT, P.NOME}
SINAIS = {P.MAIS, P.LIGACAO}

# Descrição dos tokens nas mensagens genéricas
DESCRICAO_TOKEN = {
    Token.EOF: "fim do arquivo",
    P.TEXTO: "texto entre aspas",
    P.IDENT: "símbolo de elemento",
    P.NOME: "nome de átomo",
    P.INTEIRO: "número inteiro",
    P.MULTIPLICADOR_ATOMO: "multiplicador (como '4x')",
    P.REPETICAO_LIGACAO: "repetição (como 'x4')",
}


def descrever_esperado(tipo):
    if tipo in DESCRICAO_TOKEN:
        return DESCRICAO_TOKEN[tipo]
    return P.literalNames[tipo]


def descrever_encontrado(token):
    if token.type == Token.EOF:
        return "fim do arquivo"
    return f"'{token.text}'"


class ErroSintatico(ErrorListener):
    def __init__(self):
        super().__init__()
        self.erros = []
        self.linhas_com_erro = set()

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        mensagem, falta_algo = self.traduzir(recognizer, offendingSymbol, e)

        # Se falta algo no fim de uma linha, o erro fica logo depois do
        # token anterior, e não no primeiro token da linha seguinte
        anterior = recognizer.getTokenStream().LT(-1)
        if falta_algo and anterior is not None and anterior.line < line:
            line = anterior.line
            column = anterior.column + len(anterior.text)

        # Um erro por linha: os seguintes costumam ser cascata da recuperação
        if line in self.linhas_com_erro:
            return
        self.linhas_com_erro.add(line)

        self.erros.append((line, column, mensagem))
        print(f"Erro sintático na linha {line}, coluna {column}: {mensagem}")

    def traduzir(self, recognizer, token, e):
        # Devolve a mensagem e se o erro é algo que falta (True) ou um
        # token que sobra (False)
        ctx = e.ctx if e is not None and e.ctx is not None else recognizer._ctx
        regra = ctx.getRuleIndex()
        esperados = set(recognizer.getExpectedTokens())
        encontrado = descrever_encontrado(token)

        if regra == P.RULE_programa and esperados == {Token.EOF}:
            return f"conteúdo depois do fim da molécula: {encontrado}", False

        if regra == P.RULE_molecula:
            if P.MOLECULE in esperados:
                return f"o programa deve começar com 'molecule', encontrado {encontrado}", False
            if P.TEXTO in esperados:
                return f"esperado nome da molécula entre aspas depois de 'molecule', encontrado {encontrado}", True
            if P.ABRE_CHAVE in esperados:
                return f"esperado '{{' depois do nome da molécula, encontrado {encontrado}", True
            if P.FECHA_CHAVE in esperados:
                if token.type == Token.EOF:
                    return "esperado '}' para fechar a molécula", True
                return f"comando inválido {encontrado}: esperado 'atom', 'bond', 'ring' ou '}}'", False

        if regra == P.RULE_atomo:
            if P.ATOM in esperados:
                return f"o multiplicador (como '4x') só pode vir antes de 'atom', encontrado {encontrado}", False
            if P.IDENT in esperados:
                return f"esperado símbolo de elemento depois de 'atom', encontrado {encontrado}", True
            if P.NOME in esperados:
                return (
                    f"esperado nome de átomo depois de 'as', encontrado {encontrado} "
                    "(palavras-chave e nomes como 'x4' são reservados)"
                ), True

        if regra in (P.RULE_carga, P.RULE_sinal):
            if esperados & SINAIS:
                return f"a carga precisa de sinal, como (+1) ou (-1), encontrado {encontrado}", True
            if P.INTEIRO in esperados:
                return f"esperado número inteiro na carga, encontrado {encontrado}", True
            if P.FECHA_PAREN in esperados:
                return f"esperado ')' para fechar a carga, encontrado {encontrado}", True

        if regra in (P.RULE_ligacao, P.RULE_operador) and esperados & OPERADORES:
            return f"esperado operador de ligação (-, =, #, -> ou ~), encontrado {encontrado}", True

        if regra in (P.RULE_ligacao, P.RULE_referencia) and esperados & REFERENCIAS:
            return f"esperado elemento ou nome de átomo na ligação, encontrado {encontrado}", True

        if regra == P.RULE_anel and P.NOME in esperados:
            return f"um anel precisa de pelo menos três nomes de átomos, encontrado {encontrado}", True

        lista = ", ".join(sorted(descrever_esperado(t) for t in esperados))
        return f"esperado {lista}, encontrado {encontrado}", True


def analisar(caminho):
    # Devolve a árvore sintática, ou None se houver erro léxico ou sintático
    entrada = FileStream(caminho, encoding="utf-8")

    lexer = MoleculeDSLLexer(entrada)
    lexer.removeErrorListeners()
    erros_lexicos = ErroLexico()
    lexer.addErrorListener(erros_lexicos)

    fluxo = CommonTokenStream(lexer)
    fluxo.fill()

    # Com erro léxico, a análise sintática só geraria erros em cascata
    if erros_lexicos.erros:
        return None

    parser = MoleculeDSLParser(fluxo)
    parser.removeErrorListeners()
    erros_sintaticos = ErroSintatico()
    parser.addErrorListener(erros_sintaticos)

    arvore = parser.programa()

    if erros_sintaticos.erros:
        return None

    return arvore


def main():
    if len(sys.argv) != 2:
        print("Uso: python src/sintatico.py <arquivo>")
        sys.exit(1)

    caminho = sys.argv[1]

    if not os.path.isfile(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        sys.exit(1)

    arvore = analisar(caminho)

    if arvore is None:
        sys.exit(1)

    print(arvore.toStringTree(recog=arvore.parser))
    print("\nAnálise sintática concluída sem erros")


if __name__ == "__main__":
    main()
