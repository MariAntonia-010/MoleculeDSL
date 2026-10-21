import os
import sys

from antlr4 import InputStream, CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener


# Localiza a pasta raiz do projeto
PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adiciona a pasta com o código gerado pelo ANTLR
PASTA_GERADO = os.path.join(PASTA_RAIZ, "gerado")
sys.path.insert(0, PASTA_GERADO)

try:
    from MoleculeDSLLexer import MoleculeDSLLexer
except ModuleNotFoundError:
    print("Código do ANTLR não encontrado em gerado/. Gere com: sh gerar.sh")
    sys.exit(1)


class ErroLexico(ErrorListener):
    def __init__(self):
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # Substitui a mensagem do ANTLR ("token recognition error") por
        # uma em português, a partir do primeiro caractere não reconhecido
        caractere = recognizer._input.getText(e.startIndex, e.startIndex)
        mensagem = traduzir_erro_lexico(caractere)
        if caractere == ".":
            anterior = recognizer._input.getText(e.startIndex - 1, e.startIndex - 1) if e.startIndex > 0 else ""
            if anterior.isdigit():
                mensagem = "número malformado: faltam dígitos depois do ponto"
        self.erros.append((line, column, mensagem))
        print(f"Erro léxico na linha {line}, coluna {column}: {mensagem}")


def traduzir_erro_lexico(caractere):
    if not caractere:
        return "fim do arquivo inesperado"
    if caractere == '"':
        return "texto sem aspas de fechamento: o texto precisa terminar na mesma linha"
    if caractere == ".":
        return "'.' fora de um número real (um número real é escrito como 3.5)"
    if caractere.isprintable() and not caractere.isspace():
        return f"caractere inválido '{caractere}'"
    return f"caractere invisível inválido (U+{ord(caractere):04X})"


def ler_arquivo(caminho):
    # Devolve o conteúdo pronto para o lexer, ou None se o arquivo não
    # estiver em UTF-8. O BOM que alguns editores do Windows colocam no
    # início do arquivo é ignorado.
    with open(caminho, "rb") as arquivo:
        dados = arquivo.read()

    try:
        return InputStream(dados.decode("utf-8-sig"))
    except UnicodeDecodeError as e:
        # Coluna em caracteres, como nos outros erros, e não em bytes
        linha = dados.count(b"\n", 0, e.start) + 1
        inicio_linha = dados.rfind(b"\n", 0, e.start) + 1
        coluna = len(dados[inicio_linha:e.start].decode("utf-8-sig"))
        print(
            f"Erro léxico na linha {linha}, coluna {coluna}: o arquivo precisa "
            "estar salvo em UTF-8"
        )
        return None



def criar_lexer(entrada):
    """Tokeniza um InputStream já carregado e devolve (lexer, fluxo, erros)."""
    lexer = MoleculeDSLLexer(entrada)
    lexer.removeErrorListeners()
    coletor = ErroLexico()
    lexer.addErrorListener(coletor)
    fluxo = CommonTokenStream(lexer)
    fluxo.fill()
    return lexer, fluxo, coletor.erros


def analisar(caminho):
    entrada = ler_arquivo(caminho)

    if entrada is None:
        return False

    lexer = MoleculeDSLLexer(entrada)

    # Substitui a mensagem padrão de erro do ANTLR
    lexer.removeErrorListeners()
    erros = ErroLexico()
    lexer.addErrorListener(erros)

    fluxo = CommonTokenStream(lexer)
    fluxo.fill()

    imprimir_tokens(lexer, fluxo)

    if erros.erros:
        return False

    return True


def imprimir_tokens(lexer, fluxo):
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