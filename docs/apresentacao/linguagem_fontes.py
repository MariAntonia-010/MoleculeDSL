"""Partes da página tiradas das fontes da linguagem.

A gramática (gramatica/MoleculeDSL.g4) dá as palavras reservadas, os tipos
de espécie e os operadores; a tabela "Regras semânticas" do README dá as
regras. Um tipo ou operador novo sem descrição aqui interrompe a geração,
para que nenhuma mudança da linguagem fique de fora da página.
"""

import html
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DESCRICAO_TIPOS = {
    "atom": ("átomo isolado, neutro, sem ligações", 'species atom "Argon" { atom Ar }'),
    "monatomic_ion": ("íon de um átomo só", 'species monatomic_ion "Chloride" charge -1 { atom Cl(-1) }'),
    "molecule": ("molécula: entidade neutra com mais de um átomo", 'species molecule "Water" { … }'),
    "molecular_ion": ("íon com mais de um átomo", 'species molecular_ion "Ammonium" charge +1 { … }'),
    "ionic_solid": ("motivo de um sólido iônico", 'species ionic_solid "Sodium chloride" { … }'),
    "covalent_network": ("motivo de uma rede covalente", 'species covalent_network "Diamond" { … }'),
    "metallic_solid": ("motivo de um sólido metálico, com ~", 'species metallic_solid "Sodium" { … }'),
}

DESCRICAO_OPERADORES = {
    "-": "simples: 1 par compartilhado",
    "=": "dupla: 2 pares",
    "#": "tripla: 3 pares",
    "->": "coordenada: o par vem do doador",
    "~": "metálica: elétrons deslocalizados",
}


def ler(caminho):
    with open(os.path.join(RAIZ, caminho), encoding="utf-8") as arquivo:
        return arquivo.read()


def gramatica():
    texto = ler("gramatica/MoleculeDSL.g4")
    literais = dict(re.findall(r"^([A-Z_]+)\s*:\s*'([^']+)'\s*;", texto, re.M))
    palavras = [v for v in literais.values() if re.fullmatch(r"[a-z_]+", v)]
    tipos = []
    for token, carga in re.findall(r"SPECIES\s+([A-Z_]+)\s+TEXTO(\s+cargaEspecie)?", texto):
        tipos.append({"tipo": literais[token], "exige_carga": bool(carga)})
    regra_operador = re.search(r"^operador\s*\n((?:\s+[:|].*\n)+)", texto, re.M).group(1)
    operadores = [literais[t] for t in re.findall(r"[:|]\s*([A-Z_]+)", regra_operador)]
    sem_descricao = [t["tipo"] for t in tipos if t["tipo"] not in DESCRICAO_TIPOS]
    sem_descricao += [o for o in operadores if o not in DESCRICAO_OPERADORES]
    if sem_descricao:
        raise SystemExit(f"linguagem_fontes.py: falta descrição para {sem_descricao}")
    return {"texto": texto.strip(), "palavras": palavras, "tipos": tipos, "operadores": operadores}


def regras():
    readme = ler("README.md")
    tabela = readme.split("## Regras semânticas", 1)[1].split("\n\n", 2)[1]
    linhas = []
    for linha in tabela.splitlines()[2:]:
        partes = [p.strip() for p in linha.strip("|").split("|")]
        if len(partes) != 3:
            continue
        codigos = re.findall(r"`([A-Z]+-\d{3})`", partes[0])
        rotulo = codigos[0] + (f"…{codigos[-1].split('-')[1]}" if len(codigos) > 1 else "")
        linhas.append({"codigos": codigos, "rotulo": rotulo, "regra": partes[1].replace("`", ""), "severidade": partes[2]})
    return linhas


def tabela_regras_html(lista):
    return "\n".join(
        f'<tr><td>{html.escape(r["rotulo"])}</td><td>{html.escape(r["regra"])}</td>'
        f'<td class="{"erro-sev" if r["severidade"] == "erro" else "aviso-sev"}">{html.escape(r["severidade"])}</td></tr>'
        for r in lista
    )


def tabela_tipos_html(tipos):
    return "\n".join(
        f'<tr><td>{t["tipo"]}</td><td>{html.escape(DESCRICAO_TIPOS[t["tipo"]][0])}{" · exige charge" if t["exige_carga"] else ""}</td>'
        f'<td><code>{html.escape(DESCRICAO_TIPOS[t["tipo"]][1])}</code></td></tr>'
        for t in tipos
    )


def tabela_operadores_html(operadores):
    return "\n".join(
        f"<tr><td>{html.escape(o)}</td><td>{html.escape(DESCRICAO_OPERADORES[o])}</td></tr>" for o in operadores
    )
