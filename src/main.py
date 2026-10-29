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
    "Uso: python src/main.py [--tokens] [--ast] [--modelo] "
    "[--resolver|--resolver-todas] <arquivo>\n"
    "  --tokens  mostra os tokens reconhecidos\n"
    "  --ast     mostra a AST construída\n"
    "  --modelo  mostra o modelo da molécula (átomos e ligações)"
    "\n  --resolver infere ligações quando a entrada contém somente átomos"
    "\n  --resolver-todas enumera até 10 estruturas não equivalentes"
    "\n  --max-solucoes=N define o limite da enumeração"
    "\n  --tempo-limite=S interrompe a busca após S segundos"
    "\n  --formato=texto|json|jsonl escolhe a saída do solver"
    "\n  --backend=reference|cpsat escolhe o backend"
)

OPCOES = {
    "--tokens",
    "--ast",
    "--modelo",
    "--resolver",
    "--resolver-todas",
}


def ler_argumentos(argumentos):
    # Devolve o caminho do arquivo e o conjunto de opções, ou None se
    # os argumentos forem inválidos
    opcoes = set()
    arquivos = []
    configuracao = {
        "max_solucoes": 10,
        "tempo_limite": None,
        "formato": "texto",
        "backend": "reference",
    }

    for arg in argumentos:
        if arg.startswith("--"):
            if arg.startswith("--max-solucoes="):
                try:
                    valor = int(arg.split("=", 1)[1])
                except ValueError:
                    return None
                if valor < 1:
                    return None
                configuracao["max_solucoes"] = valor
                continue
            if arg.startswith("--tempo-limite="):
                try:
                    valor = float(arg.split("=", 1)[1])
                except ValueError:
                    return None
                if valor <= 0:
                    return None
                configuracao["tempo_limite"] = valor
                continue
            if arg.startswith("--formato="):
                valor = arg.split("=", 1)[1]
                if valor not in {"texto", "json", "jsonl"}:
                    return None
                configuracao["formato"] = valor
                continue
            if arg.startswith("--backend="):
                valor = arg.split("=", 1)[1]
                if valor not in {"reference", "cpsat"}:
                    return None
                configuracao["backend"] = valor
                continue
            if arg not in OPCOES:
                print(f"Opção desconhecida: {arg}")
                return None
            opcoes.add(arg)
        else:
            arquivos.append(arg)

    if len(arquivos) != 1:
        return None

    return arquivos[0], opcoes, configuracao


def compilar(caminho, opcoes, configuracao=None):
    configuracao = configuracao or {
        "max_solucoes": 10,
        "tempo_limite": None,
        "formato": "texto",
        "backend": "reference",
    }
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

    if "--resolver" in opcoes and "--resolver-todas" in opcoes:
        print("As opções --resolver e --resolver-todas são mutuamente exclusivas")
        return ERRO_LEXICO_OU_SINTATICO
    formato = configuracao["formato"]
    if formato != "texto" and not (
        "--resolver" in opcoes or "--resolver-todas" in opcoes
    ):
        print("--formato=json|jsonl exige uma opção de resolução")
        return ERRO_LEXICO_OU_SINTATICO
    if formato != "texto" and opcoes & {"--tokens", "--ast", "--modelo"}:
        print("Saída estruturada não pode ser combinada com tokens, AST ou modelo")
        return ERRO_LEXICO_OU_SINTATICO

    if "--resolver-todas" in opcoes:
        resultado = solver.solve(
            molecula,
            semantico.carregar_valencias(),
            solver.SolveRequest(
                max_solutions=configuracao["max_solucoes"],
                require_unique=False,
                time_limit_seconds=configuracao["tempo_limite"],
                backend=configuracao["backend"],
            ),
        )
        if formato != "texto":
            for estrutura in resultado.solutions:
                _, mensagens = semantico.analisar(estrutura)
                resultado.messages.extend(mensagens)
        if formato == "json":
            print(solver.result_json(resultado))
            tem_erro = any(
                getattr(mensagem, "severidade", None) == semantico.ERRO
                for mensagem in resultado.messages
            )
            return (
                SUCESSO
                if resultado.solutions
                and not tem_erro
                and resultado.summary.status
                not in (solver.SolveStatus.TIMEOUT, solver.SolveStatus.CANCELLED)
                else ERRO_SEMANTICO
            )
        if formato == "jsonl":
            print(solver.result_jsonl(resultado))
            tem_erro = any(
                getattr(mensagem, "severidade", None) == semantico.ERRO
                for mensagem in resultado.messages
            )
            return (
                SUCESSO
                if resultado.solutions
                and not tem_erro
                and resultado.summary.status
                not in (solver.SolveStatus.TIMEOUT, solver.SolveStatus.CANCELLED)
                else ERRO_SEMANTICO
            )
        for mensagem in resultado.messages:
            print(mensagem)
        if resultado.messages:
            return ERRO_SEMANTICO

        for indice, estrutura in enumerate(resultado.solutions, start=1):
            modelo_molecula, mensagens = semantico.analisar(estrutura)
            print(f"Solução {indice}/{len(resultado.solutions)}")
            if "--ast" in opcoes:
                print(formatar(estrutura))
            for mensagem in mensagens:
                print(mensagem)
            if any(m.severidade == semantico.ERRO for m in mensagens):
                return ERRO_SEMANTICO
            print(modelo.formatar(modelo_molecula))
        if resultado.summary.status is solver.SolveStatus.LIMIT_REACHED:
            print(
                "Mais soluções existem; exibidas somente as "
                f"{len(resultado.solutions)} primeiras"
            )
        elif resultado.summary.status is solver.SolveStatus.TIMEOUT:
            print("Tempo limite atingido; o resultado é parcial")
            return ERRO_SEMANTICO
        return SUCESSO if resultado.solutions else ERRO_SEMANTICO

    if "--resolver" in opcoes:
        resultado = solver.solve(
            molecula,
            semantico.carregar_valencias(),
            solver.SolveRequest(
                max_solutions=2,
                require_unique=True,
                time_limit_seconds=configuracao["tempo_limite"],
                backend=configuracao["backend"],
            ),
        )
        if formato != "texto":
            for estrutura in resultado.solutions:
                _, mensagens = semantico.analisar(estrutura)
                resultado.messages.extend(mensagens)
        if formato == "json":
            print(solver.result_json(resultado))
        elif formato == "jsonl":
            print(solver.result_jsonl(resultado))
        if formato != "texto":
            tem_erro = any(
                getattr(mensagem, "severidade", None) == semantico.ERRO
                for mensagem in resultado.messages
            )
            return (
                SUCESSO
                if resultado.solutions
                and not tem_erro
                and resultado.summary.unique is solver.Uniqueness.TRUE
                and resultado.summary.status is solver.SolveStatus.COMPLETE
                else ERRO_SEMANTICO
            )
        for mensagem in resultado.messages:
            print(mensagem)
        if resultado.messages:
            return ERRO_SEMANTICO
        if resultado.summary.status in (
            solver.SolveStatus.TIMEOUT,
            solver.SolveStatus.CANCELLED,
        ):
            if formato == "texto":
                print(
                    "Erro de resolução [SOLVER-005] na linha "
                    f"{molecula.linha}, coluna {molecula.coluna}: "
                    "a busca foi interrompida antes de provar a unicidade"
                )
            return ERRO_SEMANTICO
        if resultado.summary.unique is not solver.Uniqueness.TRUE:
            if formato == "texto":
                print(
                    "Erro de resolução [SOLVER-004] na linha "
                    f"{molecula.linha}, coluna {molecula.coluna}: "
                    "a fórmula admite múltiplas estruturas; declare as ligações"
                )
            return ERRO_SEMANTICO
        if formato != "texto":
            return SUCESSO
        molecula = resultado.solutions[0]

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

    caminho, opcoes, configuracao = lidos

    if not os.path.isfile(caminho):
        print(f"Erro de entrada [ENT-001]: arquivo não encontrado: {caminho}")
        sys.exit(ERRO_LEXICO_OU_SINTATICO)

    sys.exit(compilar(caminho, opcoes, configuracao))


if __name__ == "__main__":
    main()
