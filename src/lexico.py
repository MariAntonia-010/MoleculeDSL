import os
import sys

from antlr4 import InputStream, CommonTokenStream, Token

from erros import ColetorErrosANTLR, ErroCompilacao


# Localiza a pasta raiz do projeto
PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adiciona a pasta com o código gerado pelo ANTLR
PASTA_GERADO = os.environ.get(
    "MOLECULEDSL_GERADO", os.path.join(PASTA_RAIZ, "gerado")
)
sys.path.insert(0, PASTA_GERADO)

try:
    from MoleculeDSLLexer import MoleculeDSLLexer
except ModuleNotFoundError:
    print(
        f"Erro de configuração [CFG-001]: código do ANTLR não encontrado em "
        f"{PASTA_GERADO!r}. Gere com: sh gerar.sh"
    )
    sys.exit(1)


class ErroLexico(ColetorErrosANTLR):
    def __init__(self):
        super().__init__("léxico")

    def traduzir(self, recognizer, offendingSymbol, line, column, msg, e):
        # Substitui a mensagem do ANTLR ("token recognition error") por
        # uma em português, a partir do primeiro caractere não reconhecido
        caractere = ""
        if e is not None and hasattr(e, "startIndex"):
            caractere = recognizer._input.getText(e.startIndex, e.startIndex)
        return traduzir_erro_lexico(caractere)


def traduzir_erro_lexico(caractere):
    if not caractere:
        return "LEX-001", "fim do arquivo inesperado"
    if caractere == '"':
        return (
            "LEX-002",
            "texto sem aspas de fechamento: o texto precisa terminar na mesma linha",
        )
    if caractere == ".":
        return (
            "LEX-003",
            "'.' fora de um número real (um número real é escrito como 3.5)",
        )
    if caractere.isprintable() and not caractere.isspace():
        return "LEX-001", f"caractere inválido '{caractere}'"
    return "LEX-004", f"caractere invisível inválido (U+{ord(caractere):04X})"


def ler_arquivo(caminho):
    # Devolve o conteúdo pronto para o lexer e os erros de leitura.
    # O BOM que alguns editores do Windows colocam no início é ignorado.
    with open(caminho, "rb") as arquivo:
        dados = arquivo.read()

    try:
        return InputStream(dados.decode("utf-8-sig")), []
    except UnicodeDecodeError as e:
        # Coluna em caracteres, como nos outros erros, e não em bytes
        linha = dados.count(b"\n", 0, e.start) + 1
        inicio_linha = dados.rfind(b"\n", 0, e.start) + 1
        coluna = len(dados[inicio_linha:e.start].decode("utf-8-sig"))
        erro = ErroCompilacao(
            "léxico",
            "LEX-005",
            linha,
            coluna,
            "o arquivo precisa estar salvo em UTF-8",
        )
        return None, [erro]


def analisar(caminho):
    entrada, erros_leitura = ler_arquivo(caminho)

    if entrada is None:
        for erro in erros_leitura:
            print(erro)
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
        erros.imprimir()
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