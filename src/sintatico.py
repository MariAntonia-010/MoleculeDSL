import os
import sys

from antlr4 import CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.ErrorStrategy import DefaultErrorStrategy

# lexico.py adiciona a pasta "gerado" ao caminho de importação
from lexico import ErroLexico, ler_arquivo
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


def fim_de_ligacao(fluxo, indice):
    # Diz se o token na posição indice é a segunda referência de um bond,
    # como o 'H' de "bond C-H", onde a repetição (como 'x4') pode entrar
    if indice < 1:
        return False
    return fluxo.get(indice).type in REFERENCIAS and fluxo.get(indice - 1).type in OPERADORES


def explicar_quantificador(fluxo, token):
    # Mensagens para os erros de espaço mais comuns em "4x" e "x4", que
    # sem isso apareceriam como "comando inválido". Devolve None se o
    # token não for um desses casos.
    i = token.tokenIndex
    anterior = fluxo.get(i - 1) if i > 0 else None
    seguinte = fluxo.get(i + 1)
    depois_de_ligacao = fim_de_ligacao(fluxo, i - 1)

    if token.type == P.INTEIRO:
        n = token.text
        if seguinte.type == P.NOME and seguinte.text == "x":
            return f"multiplicador com espaço: escreva '{n}x', sem espaço entre o número e o x"
        if seguinte.type == P.IDENT and seguinte.text == "X":
            return f"multiplicador com X maiúsculo: escreva '{n}x'"
        if seguinte.type == P.ATOM:
            return f"multiplicador sem x: escreva '{n}x atom'"
        if depois_de_ligacao and anterior.type == P.IDENT and anterior.text.endswith("x"):
            elemento = anterior.text[:-1]
            return (
                f"repetição sem espaço: escreva '{elemento} x{n}' em vez de "
                f"'{anterior.text}{n}' ('{anterior.text}' seria lido como elemento)"
            )
        if depois_de_ligacao:
            return f"repetição sem x: escreva 'x{n}'"

    if token.type == P.NOME and token.text == "x":
        if seguinte.type == P.INTEIRO:
            return f"repetição com espaço: escreva 'x{seguinte.text}', sem espaço entre o x e o número"
        if depois_de_ligacao:
            return "repetição sem número: escreva o x junto do número, como 'x4'"

    if token.type == P.IDENT and token.text == "X" and seguinte.type == P.INTEIRO and depois_de_ligacao:
        return f"repetição com X maiúsculo: escreva 'x{seguinte.text}'"

    if token.type == P.REPETICAO_LIGACAO:
        n = token.text[1:]
        return (
            f"a repetição '{token.text}' só pode vir no fim de um 'bond'; "
            f"para vários átomos iguais use '{n}x atom'"
        )

    return None


class RecuperacaoPorComando(DefaultErrorStrategy):
    # Na recuperação, o ANTLR pode apagar um token para "consertar" o
    # comando com erro. Se esse token começa outro comando (como o 'bond'
    # da linha seguinte), apagá-lo estraga também o comando seguinte, e
    # o erro dele sai com uma mensagem errada. Por isso esses tokens
    # nunca são apagados.

    INICIO_DE_COMANDO = {P.ATOM, P.BOND, P.RING, P.MULTIPLICADOR_ATOMO, P.FECHA_CHAVE}

    def singleTokenDeletion(self, recognizer):
        if recognizer.getCurrentToken().type in self.INICIO_DE_COMANDO:
            return None
        return super().singleTokenDeletion(recognizer)


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
                dica = explicar_quantificador(recognizer.getTokenStream(), token)
                if dica is not None:
                    return dica, False
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


def tokenizar(caminho):
    # Devolve o lexer, o fluxo de tokens já lido e se não houve erro léxico.
    # Se o arquivo não puder ser lido, o lexer e o fluxo são None.
    entrada = ler_arquivo(caminho)

    if entrada is None:
        return None, None, False

    lexer = MoleculeDSLLexer(entrada)
    lexer.removeErrorListeners()
    erros_lexicos = ErroLexico()
    lexer.addErrorListener(erros_lexicos)

    fluxo = CommonTokenStream(lexer)
    fluxo.fill()

    return lexer, fluxo, not erros_lexicos.erros


def analisar(caminho):
    # Devolve a árvore sintática, ou None se houver erro léxico ou sintático
    lexer, fluxo, sem_erro_lexico = tokenizar(caminho)

    # Com erro léxico, a análise sintática só geraria erros em cascata
    if not sem_erro_lexico:
        return None

    return analisar_fluxo(fluxo)


def analisar_fluxo(fluxo):
    # Devolve a árvore sintática, ou None se houver erro sintático
    parser = MoleculeDSLParser(fluxo)
    parser._errHandler = RecuperacaoPorComando()
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
