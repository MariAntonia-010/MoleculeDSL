"""Gera docs/apresentacao/index.html a partir de modelo.html.

Todo trecho de saída da página vem de uma execução real do projeto feita
por este script, para a apresentação não ficar defasada em relação ao
compilador. Uso, a partir da raiz do repositório:

    python3 docs/apresentacao/gerar_apresentacao.py
"""

import base64
import glob
import html
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conteudo_guia import LICOES  # noqa: E402

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(PASTA))
MAIN = os.path.join(RAIZ, "src", "main.py")

# Exemplos do playground, na ordem do seletor
EXEMPLOS = [
    "agua",
    "metano",
    "amonia",
    "etanol",
    "acetona",
    "acido_acetico",
    "ureia",
    "dioxido_carbono",
    "benzeno",
    "naftaleno",
    "pirrol",
    "ciclohexano",
    "acido_tartarico_meso",
    "e_1_2_dicloroeteno",
    "penta_2_3_dieno",
    "amonio_por_ligacao_coordenada",
    "hidrogenio",
    "oxigenio",
    "nitrogenio",
    "cloro",
    "cloreto_de_hidrogenio",
    "peroxido_de_hidrogenio",
    "monoxido_de_carbono",
    "metanol",
]


def rodar(*argumentos, script=MAIN):
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    resultado = subprocess.run(
        [sys.executable, script, *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=RAIZ,
        env=ambiente,
    )
    return resultado.stdout


def sem_conclusao(saida):
    # Tira a linha "Espécie ...: análise concluída sem erros"
    linhas = [l for l in saida.splitlines() if not l.startswith("Espécie ")]
    return "\n".join(linhas).strip()


def esperado(caminho):
    with open(os.path.join(RAIZ, caminho), encoding="utf-8") as arquivo:
        primeira = arquivo.readline()
    return primeira.removeprefix("// esperado:").strip()


def main():
    with open(os.path.join(PASTA, "modelo.html"), encoding="utf-8") as arquivo:
        pagina = arquivo.read()
    # Estilo e script ficam em arquivos próprios e entram inline na página
    def ler(nome):
        with open(os.path.join(PASTA, nome), encoding="utf-8") as arquivo:
            return arquivo.read()

    modulos = "".join(ler(nome) for nome in ("traducao.js", "guia.js", "laboratorio.js", "tabela.js"))
    pagina = pagina.replace("{{ESTILO}}", ler("estilo.css"))
    pagina = pagina.replace("{{APP_JS}}", ler("app.js").replace("  /* @modulos */\n", modulos))

    with tempfile.TemporaryDirectory() as pasta:
        svg = os.path.join(pasta, "agua.svg")
        rodar(
            "exemplos/agua.mol",
            "--tipo",
            "ast",
            "-o",
            svg,
            script=os.path.join(RAIZ, "src", "desenhar_arvore.py"),
        )
        with open(svg, "rb") as arquivo:
            imagem = "data:image/svg+xml;base64," + base64.b64encode(
                arquivo.read()
            ).decode("ascii")

    testes = rodar(script=os.path.join(RAIZ, "testar.py"))
    resumo = testes.strip().splitlines()[-1]
    total = re.match(r"(\d+) testes", resumo).group(1)
    exemplos = len(glob.glob(os.path.join(RAIZ, "exemplos", "*.mol")))
    snapshots = len(glob.glob(os.path.join(RAIZ, "exemplos", "*.ast.txt"))) + len(
        glob.glob(os.path.join(RAIZ, "exemplos", "*.modelo.txt"))
    )
    bench = next(
        l.strip()
        for l in rodar(script=os.path.join(RAIZ, "tests", "benchmark_solver.py")).splitlines()
        if l.strip().startswith("C6H6")
    )
    estereo = sem_conclusao(rodar("--estereo", "exemplos/acido_tartarico_meso.mol"))
    estereo = "\n".join(l.strip() for l in estereo.splitlines()[-2:])

    lista_exemplos = []
    for nome in EXEMPLOS:
        arquivo = f"exemplos/{nome}.mol"
        with open(os.path.join(RAIZ, arquivo), encoding="utf-8") as entrada:
            texto = entrada.read()
        # O nome vem do cabeçalho, não de aspas em comentários
        titulo = re.search(r'(?:molecule|species\s+\w+)\s+"([^"]*)"', texto).group(1)
        lista_exemplos.append(
            {
                "titulo": titulo,
                "arquivo": arquivo,
                "codigo": texto,
                "saida": rodar("--modelo", arquivo).strip(),
            }
        )
    with open(os.path.join(RAIZ, "regras", "elementos.json"), encoding="utf-8") as entrada:
        elementos = {
            simbolo: {
                "nome": dados["nome"],
                "numero": dados["numero_atomico"],
                "bloco": dados["bloco"],
                "config": dados.get("configuracao_eletronica"),
                "valencia": dados.get("eletrons_valencia"),
                "eletronegatividade": dados.get("eletronegatividade"),
                "estados": dados.get("estados_oxidacao") or [],
            }
            for simbolo, dados in json.load(entrada)["elementos"].items()
        }
    with open(os.path.join(RAIZ, "regras", "valencias.json"), encoding="utf-8") as entrada:
        regras = json.load(entrada)
    # Guia: cada exemplo passa pelo compilador real; código de saída
    # diferente do esperado interrompe a geração
    guia = []
    with tempfile.TemporaryDirectory() as pasta_guia:
        for licao in LICOES:
            exemplos_licao = []
            for indice, exemplo in enumerate(licao["exemplos"], start=1):
                caminho = os.path.join(pasta_guia, f"{licao['id']}_{indice}.mol")
                with open(caminho, "w", encoding="utf-8") as saida_mol:
                    saida_mol.write(exemplo["codigo"])
                processo = subprocess.run(
                    [sys.executable, MAIN, *exemplo["opcoes"], caminho],
                    capture_output=True, text=True, encoding="utf-8", cwd=RAIZ,
                    env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                )
                if processo.returncode != exemplo["saida"]:
                    sys.exit(
                        f"guia: '{exemplo['titulo']}' saiu com {processo.returncode}, "
                        f"esperado {exemplo['saida']}\n{processo.stdout}"
                    )
                exemplos_licao.append({
                    **exemplo,
                    "saida_real": processo.stdout.strip(),
                    "comando": " ".join(["python3 src/main.py", *exemplo["opcoes"], f"{licao['id']}.mol"]),
                })
            guia.append({**licao, "exemplos": exemplos_licao})

    dados = {
        "guia": guia,
        "exemplos": lista_exemplos,
        "elementos": elementos,
        "valencias": {
            chave: regras[chave]
            for chave in ("valencias", "valencias_expandidas", "valencias_com_carga")
        },
    }
    with open(os.path.join(RAIZ, "gramatica", "MoleculeDSL.g4"), encoding="utf-8") as entrada:
        gramatica = entrada.read().strip()

    valores = {
        "DADOS_JSON": json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"),
        "USO": rodar().strip(),
        "GRAMATICA": gramatica,
        "AGUA": open(os.path.join(RAIZ, "exemplos", "agua.mol"), encoding="utf-8").read().strip(),
        "AST_IMG": imagem,
        "TOKENS": sem_conclusao(rodar("--tokens", "exemplos/agua.mol")),
        "AST": sem_conclusao(rodar("--ast", "exemplos/agua.mol")),
        "MODELO": rodar("--modelo", "exemplos/agua.mol").strip(),
        "ERRO_STEREO": esperado("invalidos_semanticos/estereo_descritor_errado.mol"),
        "BENCH": bench,
        "ESTEREO": estereo,
        "TAUTOMEROS": sem_conclusao(rodar("--tautomeros", "exemplos/acetona.mol")),
        "AROMATICIDADE": sem_conclusao(rodar("--aromaticidade", "exemplos/pirrol.mol")),
        "TOTAL": total,
        "EXEMPLOS": str(exemplos),
        "SNAPSHOTS": str(snapshots),
        "SVGS": str(2 * exemplos),
        "RESUMO": resumo,
    }
    for chave, valor in valores.items():
        cru = chave in ("AST_IMG", "DADOS_JSON")
        texto = valor if cru else html.escape(valor, quote=False)
        pagina = pagina.replace("{{" + chave + "}}", texto)
    restantes = re.findall(r"\{\{[A-Z_]+\}\}", pagina)
    if restantes:
        sys.exit(f"marcadores sem valor: {restantes}")

    destino = os.path.join(PASTA, "index.html")
    with open(destino, "w", encoding="utf-8") as arquivo:
        arquivo.write(pagina)
    print(f"Página gerada: {os.path.relpath(destino, RAIZ)} ({resumo})")


if __name__ == "__main__":
    main()
