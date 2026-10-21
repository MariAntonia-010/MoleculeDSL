import os
import sys
from dataclasses import dataclass, field
from antlr4 import InputStream, CommonTokenStream

# sintatico.py (via lexico.py) adiciona a pasta "gerado" ao caminho
from lexico import imprimir_tokens
from sintatico import tokenizar, analisar_fluxo, analisar_fluxo_detalhado
from construtor_ast import construir
from ast_nos import formatar
import modelo
import semantico


# Códigos de saída
SUCESSO = 0
ERRO_LEXICO_OU_SINTATICO = 1
ERRO_SEMANTICO = 2

USO = (
    "Uso: python src/main.py [--tokens] [--ast] [--arvore] [--modelo] <arquivo>\n"
    "  --tokens  mostra os tokens reconhecidos\n"
    "  --ast     mostra a AST construída\n"
    "  --arvore  mostra a árvore sintática concreta do ANTLR\n"
    "  --modelo  mostra o modelo da molécula (átomos e ligações)"
)

OPCOES = {"--tokens", "--ast", "--arvore", "--modelo"}


def ler_argumentos(argumentos):
    # Devolve o caminho do arquivo e o conjunto de opções, ou None se
    # os argumentos forem inválidos
    opcoes = set()
    arquivos = []

    for arg in argumentos:
        if arg.startswith("--"):
            if arg not in OPCOES:
                print(f"Opção desconhecida: {arg}")
                return None
            opcoes.add(arg)
        else:
            arquivos.append(arg)

    if len(arquivos) != 1:
        return None

    return arquivos[0], opcoes


@dataclass
class Resultado:
    """Resultado programático do pipeline, útil para testes e ferramentas."""
    erros: list = field(default_factory=list)
    ast: object = None
    lexer: object = None
    fluxo: object = None
    arvore: object = None
    parser: object = None
    modelo: object = None
    mensagens_semanticas: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.erros and not any(m.severidade == semantico.ERRO for m in self.mensagens_semanticas)


def processar(texto):
    """Executa léxico, sintático, AST e semântica sobre texto em memória.

    As posições continuam na convenção do Main: colunas base 0.
    Interrompe a cadeia na primeira fase com erros, evitando cascatas.
    """
    r = Resultado()
    entrada = InputStream(texto)
    from lexico import criar_lexer
    r.lexer, r.fluxo, erros = criar_lexer(entrada)
    if erros:
        r.erros.extend(erros)
        return r
    r.arvore, r.parser, erros = analisar_fluxo_detalhado(r.fluxo)
    if erros:
        r.erros.extend(erros)
        return r
    r.ast = construir(r.arvore)
    r.modelo, r.mensagens_semanticas = semantico.analisar(r.ast)
    r.erros.extend(m for m in r.mensagens_semanticas if m.severidade == semantico.ERRO)
    return r


def compilar(caminho, opcoes):
    # Etapas encadeadas: cada uma só roda se a anterior não teve erro
    lexer, fluxo, sem_erro_lexico = tokenizar(caminho)

    if "--tokens" in opcoes and lexer is not None:
        imprimir_tokens(lexer, fluxo)

    if not sem_erro_lexico:
        return ERRO_LEXICO_OU_SINTATICO

    if "--arvore" in opcoes:
        arvore, parser, erros = analisar_fluxo_detalhado(fluxo)
        if erros:
            return ERRO_LEXICO_OU_SINTATICO
        print(arvore.toStringTree(recog=parser))
    else:
        arvore = analisar_fluxo(fluxo)
        if arvore is None:
            return ERRO_LEXICO_OU_SINTATICO

    molecula = construir(arvore)

    if "--ast" in opcoes:
        print(formatar(molecula))

    modelo_molecula, mensagens = semantico.analisar(molecula)

    # Avisos são mostrados, mas não impedem a compilação
    for mensagem in mensagens:
        print(mensagem)

    if any(m.severidade == semantico.ERRO for m in mensagens):
        return ERRO_SEMANTICO

    if "--modelo" in opcoes:
        print(modelo.formatar(modelo_molecula))

    print(f"Molécula {molecula.nome!r}: análise concluída sem erros")
    return SUCESSO


def main():
    lidos = ler_argumentos(sys.argv[1:])

    if lidos is None:
        print(USO)
        sys.exit(ERRO_LEXICO_OU_SINTATICO)

    caminho, opcoes = lidos

    if not os.path.isfile(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        sys.exit(ERRO_LEXICO_OU_SINTATICO)

    sys.exit(compilar(caminho, opcoes))


if __name__ == "__main__":
    main()
