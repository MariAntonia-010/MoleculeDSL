import os
import sys

# sintatico.py (via lexico.py) adiciona a pasta "gerado" ao caminho
from lexico import imprimir_tokens
from sintatico import tokenizar, analisar_fluxo
from construtor_ast import construir
from ast_nos import formatar


# Códigos de saída
SUCESSO = 0
ERRO_LEXICO_OU_SINTATICO = 1
ERRO_SEMANTICO = 2  # reservado para a análise semântica

USO = (
    "Uso: python src/main.py [--tokens] [--ast] <arquivo>\n"
    "  --tokens  mostra os tokens reconhecidos\n"
    "  --ast     mostra a AST construída"
)

OPCOES = {"--tokens", "--ast"}


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


def compilar(caminho, opcoes):
    # Etapas encadeadas: cada uma só roda se a anterior não teve erro
    lexer, fluxo, sem_erro_lexico = tokenizar(caminho)

    if "--tokens" in opcoes:
        imprimir_tokens(lexer, fluxo)

    if not sem_erro_lexico:
        return ERRO_LEXICO_OU_SINTATICO

    arvore = analisar_fluxo(fluxo)

    if arvore is None:
        return ERRO_LEXICO_OU_SINTATICO

    molecula = construir(arvore)

    if "--ast" in opcoes:
        print(formatar(molecula))

    # A análise semântica entra aqui e devolve ERRO_SEMANTICO se falhar

    print(f"Molécula {molecula.nome!r}: análise léxica e sintática concluída sem erros")
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
