import os
import sys

# sintatico.py (via lexico.py) adiciona a pasta "gerado" ao caminho
from lexico import imprimir_tokens
from sintatico import tokenizar, analisar_fluxo
from construtor_ast import construir
from ast_nos import formatar
import modelo
import semantico
import solver


# Códigos de saída
SUCESSO = 0
ERRO_LEXICO_OU_SINTATICO = 1
ERRO_SEMANTICO = 2

USO = (
    "Uso: python src/main.py [--tokens] [--ast] [--modelo] [--resolver] <arquivo>\n"
    "  --tokens  mostra os tokens reconhecidos\n"
    "  --ast     mostra a AST construída\n"
    "  --modelo  mostra o modelo da molécula (átomos e ligações)"
    "\n  --resolver infere ligações quando a entrada contém somente átomos"
)

OPCOES = {"--tokens", "--ast", "--modelo", "--resolver"}


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
    lexer, fluxo, erros_lexicos = tokenizar(caminho)

    if "--tokens" in opcoes and lexer is not None:
        imprimir_tokens(lexer, fluxo)

    if erros_lexicos.erros:
        erros_lexicos.imprimir()
        return ERRO_LEXICO_OU_SINTATICO

    arvore, erros_sintaticos = analisar_fluxo(fluxo)

    if erros_sintaticos.erros:
        erros_sintaticos.imprimir()
        return ERRO_LEXICO_OU_SINTATICO

    molecula = construir(arvore)

    if "--resolver" in opcoes:
        molecula, mensagens_solver = solver.resolver(
            molecula, semantico.carregar_valencias()
        )
        for mensagem in mensagens_solver:
            print(mensagem)
        if mensagens_solver:
            return ERRO_SEMANTICO

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

    print(f"Espécie {molecula.nome!r}: análise concluída sem erros")
    return SUCESSO


def main():
    lidos = ler_argumentos(sys.argv[1:])

    if lidos is None:
        print(USO)
        sys.exit(ERRO_LEXICO_OU_SINTATICO)

    caminho, opcoes = lidos

    if not os.path.isfile(caminho):
        print(f"Erro de entrada [ENT-001]: arquivo não encontrado: {caminho}")
        sys.exit(ERRO_LEXICO_OU_SINTATICO)

    sys.exit(compilar(caminho, opcoes))


if __name__ == "__main__":
    main()
