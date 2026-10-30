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
from nomes_pt import ELEMENTOS as NOMES_ELEMENTOS, ESPECIES as NOMES_ESPECIES  # noqa: E402
import linguagem_fontes  # noqa: E402

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(PASTA))
MAIN = os.path.join(RAIZ, "src", "main.py")

# Exemplos do playground, na ordem do seletor
# Exemplos da página, por grupo: o playground mostra cada grupo num
# <optgroup>, e o laboratório e as demonstrações escolhem entre eles
GRUPOS_EXEMPLOS = [
    ("Átomos isolados", ["atomo_de_hidrogenio", "helio", "neonio", "argonio", "carbono_13", "sodio_configuracao_completa",
                         "cromo", "cobre", "ferro_56", "uranio_235"]),
    ("Íons monoatômicos", ["proton", "sodio_1mais", "cloreto", "cloreto_37", "oxido", "ferro_2mais"]),
    ("Substâncias simples", ["hidrogenio", "oxigenio", "nitrogenio", "cloro", "ozonio"]),
    ("Moléculas", ["agua", "metano", "amonia", "etanol", "metanol", "acetona", "acido_acetico", "ureia",
                   "dioxido_carbono", "monoxido_de_carbono", "cloreto_de_hidrogenio", "peroxido_de_hidrogenio",
                   "berilio", "glicina_zwitterion", "acido_sulfuroso", "tiofosgenio", "germano", "etanimina", "piridin_2_ona"]),
    ("Anéis e aromáticos", ["benzeno", "naftaleno", "pirrol", "imidazol", "ciclohexano", "ciclobutadieno", "ciclopropenila", "ciclopentadienila", "tropilio"]),
    ("Íons moleculares", ["amonio_por_ligacao_coordenada", "hidronio", "hidroxido", "nitrato", "sulfato",
                          "carbonato", "cianato", "azida", "nitronio", "hexafluorofosfato", "tetracloroaluminato", "cation_alila", "enolato"]),
    ("Isótopos em moléculas", ["agua_pesada", "metano_deuterado", "etano_13c2", "etanol_1_deuterado", "propan_2_ol_d3"]),
    ("Estereoquímica", ["acido_tartarico_meso", "e_1_2_dicloroeteno", "e_pent_2_eno", "r_2_clorobutano",
                        "penta_2_3_dieno", "hexa_2_3_dieno", "cis_1_3_dimetilciclohexano", "e_diazeno", "e_acetaldoxima"]),
    ("Radicais e ligação coordenada", ["radical_metila", "oxido_nitrico", "dioxigenio_tripleto", "metileno_tripleto", "dioxido_de_nitrogenio", "hidroperoxila", "agua_trifluoreto_de_boro"]),
    ("Complexos de metais", ["diaminoprata", "tetraaminocobre", "hexaaminocobalto", "ferrocianeto"]),
    ("Sólidos", ["cloreto_de_sodio", "oxido_de_magnesio", "cloreto_de_magnesio", "dioxido_de_silicio", "sodio_metalico", "cobre_metalico"]),
]
EXEMPLOS = [nome for _, nomes in GRUPOS_EXEMPLOS for nome in nomes]
GRUPO_DO_EXEMPLO = {nome: grupo for grupo, nomes in GRUPOS_EXEMPLOS for nome in nomes}


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
        # Nome em português; sem tradução, o nome do cabeçalho do arquivo
        titulo = NOMES_ESPECIES.get(nome) or re.search(r'(?:molecule|species\s+\w+)\s+"([^"]*)"', texto).group(1)
        lista_exemplos.append(
            {
                "titulo": titulo,
                "grupo": GRUPO_DO_EXEMPLO[nome],
                "arquivo": arquivo,
                "codigo": texto,
                "saida": rodar("--modelo", arquivo).strip(),
            }
        )
    with open(os.path.join(RAIZ, "regras", "elementos.json"), encoding="utf-8") as entrada:
        elementos = {
            simbolo: {
                "nome": NOMES_ELEMENTOS[dados["numero_atomico"] - 1],
                "nome_fonte": dados["nome"],
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

    fontes = linguagem_fontes.gramatica()
    regras_semanticas = linguagem_fontes.regras()
    dados = {
        "palavras": fontes["palavras"],
        "tipos_especie": fontes["tipos"],
        "guia": guia,
        "exemplos": lista_exemplos,
        "elementos": elementos,
        "isotopos": json.load(open(os.path.join(RAIZ, "regras", "isotopos.json"), encoding="utf-8"))["isotopos_naturais"],
        "mais_abundante": json.load(open(os.path.join(RAIZ, "regras", "isotopos.json"), encoding="utf-8"))["mais_abundante"],
        "classificacao": json.load(open(os.path.join(RAIZ, "regras", "classificacao_ligacoes.json"), encoding="utf-8")),
        "valencias": {
            chave: regras[chave]
            for chave in ("valencias", "valencias_expandidas", "valencias_com_carga")
        },
    }
    gramatica = fontes["texto"]

    valores = {
        "DADOS_JSON": json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"),
        "USO": rodar().strip(),
        "GRAMATICA": gramatica,
        "PALAVRAS": " ".join(fontes["palavras"]),
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
    # Tabelas já em HTML, geradas das fontes da linguagem
    valores["TABELA_REGRAS"] = linguagem_fontes.tabela_regras_html(regras_semanticas)
    valores["TABELA_TIPOS"] = linguagem_fontes.tabela_tipos_html(fontes["tipos"])
    valores["TABELA_OPERADORES"] = linguagem_fontes.tabela_operadores_html(fontes["operadores"])
    for chave, valor in valores.items():
        cru = chave in ("AST_IMG", "DADOS_JSON", "TABELA_REGRAS", "TABELA_TIPOS", "TABELA_OPERADORES")
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
