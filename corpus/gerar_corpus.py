"""Gera o corpus de 1000 exemplos (válidos e inválidos) da MoleculeDSL.

Uso: python3 corpus/gerar_corpus.py

- Válidos: átomos de Z = 1 a 36 com a configuração eletrônica de
  referência, isótopos naturais, íons monoatômicos e moléculas descritas
  em SMILES (sem aromaticidade em minúsculas), convertidas para a DSL com
  os hidrogênios completados pela valência.
- Inválidos e avisos: mutações com um erro planejado cada (elétrons a
  menos, Pauli, massa menor que Z, isótopo não natural, estado excitado,
  unpaired contra Hund, valência, nome inexistente, ligação repetida,
  átomo solto, erros sintáticos e léxicos).

Cada arquivo é conferido com o compilador real: um válido precisa sair sem
nenhuma mensagem, e um inválido precisa conter o código planejado. As
linhas '// esperado:' vêm da saída do compilador e servem de regressão em
testar.py.
"""

import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

import atomo  # noqa: E402
import semantico  # noqa: E402

PASTA = os.path.join(RAIZ, "corpus")
MAIN = os.path.join(RAIZ, "src", "main.py")
DADOS = semantico.carregar_elementos()
ISOTOPOS = semantico.carregar_isotopos()

# Quantos arquivos de cada grupo entram no corpus (total 1000)
QUANTIDADES = {
    "atomos": 86,
    "isotopos": 80,
    "ions": 40,
    "moleculas": 360,
    "atom-003": 40,
    "atom-002": 30,
    "atom-001": 30,
    "atom-005": 40,
    "atom-004": 30,
    "atom-007": 30,
    "atom-008": 20,
    "val-001": 40,
    "nome-inexistente": 40,
    "ligacao-repetida": 40,
    "atomo-solto": 40,
    "sintaxe": 40,
    "lexico": 14,
}

VALENCIA_PADRAO = {"C": 4, "N": 3, "O": 2, "S": 2, "F": 1, "Cl": 1, "Br": 1, "I": 1, "H": 1, "B": 3, "P": 3}
GASES_NOBRES = ["He", "Ne", "Ar", "Kr", "Xe", "Rn"]


# ---------- SMILES simples -> grafo ----------

TOKEN_SMILES = re.compile(r"\[(\d*)([A-Z][a-z]?)(H\d*)?\]|Cl|Br|[BCNOSPFI]|[=#]|\(|\)|\d")


def ler_smiles(smiles):
    """Átomos [(elemento, massa)] e ligações {(i, j): ordem} de um SMILES.

    Aceita átomos orgânicos, colchetes com número de massa ([13C], [2H]),
    ramos, ligações = e # e fechamentos de anel com um dígito.
    """
    atomos, ligacoes, aneis = [], {}, []
    pilha, anterior, ordem = [], None, 1
    abertos = {}
    posicao = 0
    while posicao < len(smiles):
        m = TOKEN_SMILES.match(smiles, posicao)
        if not m:
            raise ValueError(f"SMILES não suportado: {smiles} em {posicao}")
        texto = m.group(0)
        posicao = m.end()
        if texto == "(":
            pilha.append(anterior)
        elif texto == ")":
            anterior = pilha.pop()
        elif texto in "=#":
            ordem = 2 if texto == "=" else 3
        elif texto.isdigit():
            if texto in abertos:
                outro, ordem_aberta = abertos.pop(texto)
                ligacoes[(outro, anterior)] = max(ordem, ordem_aberta)
                aneis.append((outro, anterior))
            else:
                abertos[texto] = (anterior, ordem)
            ordem = 1
        else:
            if m.group(2):
                elemento, massa = m.group(2), int(m.group(1)) if m.group(1) else None
            else:
                elemento, massa = texto, None
            atomos.append((elemento, massa))
            atual = len(atomos) - 1
            if anterior is not None:
                ligacoes[(anterior, atual)] = ordem
            anterior, ordem = atual, 1
    return atomos, ligacoes, aneis


def caminho_do_anel(n, ligacoes, a, b):
    # Menor caminho de a até b sem usar a ligação a-b: os átomos do anel
    vizinhos = {i: set() for i in range(n)}
    for (x, y) in ligacoes:
        if {x, y} != {a, b}:
            vizinhos[x].add(y)
            vizinhos[y].add(x)
    origem = {a: None}
    fila = [a]
    while fila:
        atual = fila.pop(0)
        for v in sorted(vizinhos[atual]):
            if v not in origem:
                origem[v] = atual
                fila.append(v)
    caminho = [b]
    while caminho[-1] != a:
        caminho.append(origem[caminho[-1]])
    return caminho[::-1]


def molecula_para_dsl(nome, smiles):
    atomos, ligacoes, aneis = ler_smiles(smiles)
    soma = [0] * len(atomos)
    for (a, b), o in ligacoes.items():
        soma[a] += o
        soma[b] += o
    nomes, contagem = [], {}
    for elemento, massa in atomos:
        if elemento == "H":
            prefixo = {2: "d", 3: "t"}.get(massa, "hx")
        else:
            prefixo = elemento.lower()
        contagem[prefixo] = contagem.get(prefixo, 0) + 1
        nomes.append(f"{prefixo}{contagem[prefixo]}")
    linhas = [f'species molecule "{nome}" {{']
    for (elemento, massa), rotulo in zip(atomos, nomes):
        linhas.append(f"    atom {massa or ''}{elemento} as {rotulo}")
    hidrogenios = []
    for i, (elemento, _) in enumerate(atomos):
        faltam = VALENCIA_PADRAO[elemento] - soma[i]
        if faltam < 0:
            raise ValueError(f"{nome}: valência passou em {nomes[i]}")
        hidrogenios += [i] * faltam
    if len(hidrogenios) == 1:
        linhas.append("    atom H as h1")
    elif hidrogenios:
        linhas.append(f"    {len(hidrogenios)}x atom H as h")
    linhas.append("")
    simbolo = {1: "-", 2: "=", 3: "#"}
    for (a, b), o in ligacoes.items():
        linhas.append(f"    bond {nomes[a]}{simbolo[o]}{nomes[b]}")
    for k, dono in enumerate(hidrogenios, start=1):
        linhas.append(f"    bond {nomes[dono]}-h{k}")
    for a, b in aneis:
        linhas.append("")
        linhas.append("    ring " + " ".join(nomes[i] for i in caminho_do_anel(len(atomos), ligacoes, a, b)))
    linhas.append("}")
    return "\n".join(linhas) + "\n"


# ---------- átomos e íons ----------


def nome_ingles(simbolo):
    return DADOS[simbolo]["nome"]


def com_nucleo(config):
    """Texto da configuração com o maior núcleo de gás nobre possível."""
    for gas in reversed(GASES_NOBRES):
        nucleo = atomo.normalizar(atomo.ler_subcamadas(f"[{gas}]"))
        if all(config.get(c) == e for c, e in nucleo.items()) and len(config) > len(nucleo):
            resto = {c: e for c, e in config.items() if c not in nucleo}
            return f"[{gas}] {atomo.texto_configuracao(resto)}"
    return atomo.texto_configuracao(config)


def simbolos_ate(z):
    return sorted((s for s in DADOS if DADOS[s]["numero_atomico"] <= z), key=lambda s: DADOS[s]["numero_atomico"])


def especie_atomo(simbolo, config_texto=None, massa=None, unpaired=None, titulo=None, comentario=""):
    config = atomo.configuracao_fundamental(simbolo, 0, DADOS)
    if config_texto is None:
        config_texto = com_nucleo(config)
    if unpaired is None:
        unpaired = atomo.desemparelhados(config)
    rotulo = f"{simbolo.lower()}1"
    cabecalho = f'species atom "{titulo or nome_ingles(simbolo)}"' + (f" unpaired {unpaired}" if unpaired else "")
    linhas = [f"// {comentario}" if comentario else None, cabecalho + " {", f"    atom {massa or ''}{simbolo} as {rotulo}"]
    if config_texto:
        linhas.append(f"    configuration {rotulo} {config_texto}")
    linhas.append("}")
    return "\n".join(l for l in linhas if l is not None) + "\n"


IONS = [
    ("H", -1, "Hydride"), ("Li", 1, None), ("Na", 1, None), ("K", 1, None), ("Rb", 1, None),
    ("Be", 2, None), ("Mg", 2, None), ("Ca", 2, None), ("Sr", 2, None), ("Al", 3, None),
    ("Sc", 3, None), ("Ti", 4, None), ("Cr", 3, None), ("Mn", 2, None), ("Fe", 3, None),
    ("Co", 2, None), ("Ni", 2, None), ("Cu", 1, None), ("Cu", 2, None), ("Zn", 2, None),
    ("F", -1, "Fluoride"), ("Cl", -1, "Chloride"), ("Br", -1, "Bromide"), ("O", -2, "Oxide"),
    ("S", -2, "Sulfide"), ("N", -3, "Nitride"), ("I", -1, "Iodide"), ("Ag", 1, None),
    ("Cs", 1, None), ("Ba", 2, None), ("Ti", 2, None), ("V", 2, None), ("V", 3, None),
    ("Cr", 2, None), ("Mn", 3, None), ("Fe", 2, None), ("Co", 3, None), ("Ga", 3, None),
    ("Cd", 2, None), ("Sn", 2, None), ("Sn", 4, None), ("Pb", 2, None), ("Hg", 2, None),
    ("Au", 1, None), ("Au", 3, None), ("Se", -2, "Selenide"), ("Te", -2, "Telluride"),
    ("P", -3, "Phosphide"),
]

# Moléculas R–X por nomenclatura de classe funcional (IUPAC): um grupo
# alquila ou arila R com um grupo funcional X. O SMILES de R começa no
# átomo que se liga a X; o de X termina no átomo que se liga a R.
RADICAIS = [
    ("methyl", "C"), ("ethyl", "CC"), ("propyl", "CCC"), ("isopropyl", "C(C)C"),
    ("butyl", "CCCC"), ("sec-butyl", "C(C)CC"), ("isobutyl", "CC(C)C"), ("tert-butyl", "C(C)(C)C"),
    ("pentyl", "CCCCC"), ("hexyl", "CCCCCC"), ("cyclopropyl", "C1CC1"), ("cyclobutyl", "C1CCC1"),
    ("cyclopentyl", "C1CCCC1"), ("cyclohexyl", "C1CCCCC1"), ("phenyl", "C1=CC=CC=C1"),
    ("benzyl", "CC1=CC=CC=C1"), ("vinyl", "C=C"), ("allyl", "CC=C"),
]
# (SMILES de X, molde do nome); {r} é o radical, e {par} a dupla em ordem
# alfabética com methyl (éteres, sulfetos e cetonas)
GRUPOS = [
    ("F", "{r} fluoride"), ("Cl", "{r} chloride"), ("Br", "{r} bromide"), ("I", "{r} iodide"),
    ("N#C", "{r} cyanide"), ("O", "{r} alcohol"), ("N", "{r}amine"), ("CO", "{par} ether"),
    ("CS", "{par} sulfide"), ("CC(=O)", "{par} ketone"), ("CC(=O)O", "{r} acetate"),
    ("O=CO", "{r} formate"), ("OO", "{r} hydroperoxide"), ("O=C=N", "{r} isocyanate"),
    ("S=C=N", "{r} isothiocyanate"),
]


def chave_ordem(radical):
    # Prefixos em itálico (sec-, tert-) não contam na ordem alfabética
    return radical.split("-", 1)[1] if radical.startswith(("sec-", "tert-")) else radical


def maiuscula(nome):
    # 'tert-butyl chloride' -> 'tert-Butyl chloride'
    if nome.startswith(("sec-", "tert-")):
        prefixo, resto = nome.split("-", 1)
        return f"{prefixo}-{resto[0].upper()}{resto[1:]}"
    return nome[0].upper() + nome[1:]


def nome_classe_funcional(radical, molde):
    if radical == "phenyl" and molde == "{r} alcohol":
        return "Phenol"  # o fenol não é um álcool
    if "{par}" in molde:
        par = "dimethyl" if radical == "methyl" else " ".join(sorted([radical, "methyl"], key=chave_ordem))
        return maiuscula(molde.format(par=par))
    return maiuscula(molde.format(r=radical))


MOLECULAS_RX = [
    (nome_classe_funcional(radical, molde), grupo + smiles_r)
    for radical, smiles_r in RADICAIS
    for grupo, molde in GRUPOS
]


def especie_ion(simbolo, carga, nome):
    config = atomo.configuracao_fundamental(simbolo, carga, DADOS)
    unpaired = atomo.desemparelhados(config)
    nome = nome or f"{nome_ingles(simbolo)}({carga}+)"
    sinal = f"{carga:+d}"
    rotulo = f"{simbolo.lower()}1"
    linhas = [
        f"// {nome}: {atomo.texto_configuracao(config)}, {unpaired} desemparelhado(s) pela regra de Hund",
        f'species monatomic_ion "{nome}" charge {sinal}' + (f" unpaired {unpaired}" if unpaired else "") + " {",
        f"    atom {simbolo}({sinal}) as {rotulo}",
    ]
    if config:
        linhas.append(f"    configuration {rotulo} {com_nucleo(config)}")
    linhas.append("}")
    return "\n".join(linhas) + "\n"


# ---------- moléculas ----------

MOLECULAS = [
    # alcanos
    ("Pentane", "CCCCC"), ("Hexane", "CCCCCC"), ("Heptane", "CCCCCCC"), ("Octane", "CCCCCCCC"),
    ("Nonane", "CCCCCCCCC"), ("Decane", "CCCCCCCCCC"), ("2-Methylbutane", "CC(C)CC"),
    ("2,2-Dimethylpropane", "CC(C)(C)C"), ("2-Methylpentane", "CC(C)CCC"), ("3-Methylpentane", "CCC(C)CC"),
    ("2,2-Dimethylbutane", "CC(C)(C)CC"), ("2,3-Dimethylbutane", "CC(C)C(C)C"),
    # alcenos e alcinos
    ("But-1-ene", "C=CCC"), ("Pent-1-ene", "C=CCCC"), ("Hex-1-ene", "C=CCCCC"), ("2-Methylprop-1-ene", "C=C(C)C"),
    ("Penta-1,3-diene", "C=CC=CC"), ("2-Methylbuta-1,3-diene", "CC(=C)C=C"), ("But-1-yne", "C#CCC"),
    ("But-2-yne", "CC#CC"), ("Pent-1-yne", "C#CCCC"), ("Pent-2-yne", "CC#CCC"),
    # anéis
    ("Cycloheptane", "C1CCCCCC1"), ("Cyclooctane", "C1CCCCCCC1"), ("Methylcyclopentane", "CC1CCCC1"),
    ("Methylcyclohexane", "CC1CCCCC1"), ("Ethylcyclohexane", "CCC1CCCCC1"), ("Cyclohexanol", "OC1CCCCC1"),
    ("Chlorocyclohexane", "ClC1CCCCC1"), ("Cyclohexanone", "O=C1CCCCC1"), ("Cyclopentanone", "O=C1CCCC1"),
    ("Cyclopentene", "C1=CCCC1"), ("Cyclohexanamine", "NC1CCCCC1"), ("Oxane", "C1CCOCC1"),
    ("1,4-Dioxane", "C1COCCO1"), ("Pyrrolidine", "C1CCNC1"), ("Piperidine", "C1CCNCC1"),
    ("Morpholine", "C1COCCN1"), ("Thiolane", "C1CCSC1"),
    # álcoois e éteres
    ("Butan-1-ol", "CCCCO"), ("Pentan-1-ol", "CCCCCO"), ("Hexan-1-ol", "CCCCCCO"),
    ("2-Methylpropan-1-ol", "CC(C)CO"), ("2-Methylpropan-2-ol", "CC(C)(C)O"), ("2-Methylbutan-2-ol", "CCC(C)(C)O"),
    ("Pentan-3-ol", "CCC(O)CC"), ("Propane-1,3-diol", "OCCCO"), ("Butane-1,4-diol", "OCCCCO"),
    ("Prop-2-en-1-ol", "C=CCO"), ("Prop-2-yn-1-ol", "C#CCO"), ("Methoxyethane", "CCOC"),
    ("Ethoxyethane", "CCOCC"), ("1-Methoxypropane", "CCCOC"), ("1,2-Dimethoxyethane", "COCCOC"),
    # carbonilas
    ("Butanal", "CCCC=O"), ("Pentanal", "CCCCC=O"), ("Hexanal", "CCCCCC=O"), ("2-Methylpropanal", "CC(C)C=O"),
    ("Prop-2-enal", "C=CC=O"), ("Butan-2-one", "CCC(C)=O"), ("Pentan-2-one", "CCCC(C)=O"),
    ("Pentan-3-one", "CCC(=O)CC"), ("Hexan-2-one", "CCCCC(C)=O"), ("Butane-2,3-dione", "CC(=O)C(C)=O"),
    ("Ethanedial", "O=CC=O"),
    # ácidos, ésteres e amidas
    ("Butanoic acid", "CCCC(=O)O"), ("Pentanoic acid", "CCCCC(=O)O"), ("Hexanoic acid", "CCCCCC(=O)O"),
    ("2-Methylpropanoic acid", "CC(C)C(=O)O"), ("Propanedioic acid", "OC(=O)CC(=O)O"),
    ("Chloroacetic acid", "ClCC(=O)O"), ("Methyl formate", "COC=O"), ("Ethyl formate", "CCOC=O"),
    ("Ethyl acetate", "CCOC(C)=O"), ("Propyl acetate", "CCCOC(C)=O"), ("Methyl propanoate", "CCC(=O)OC"),
    ("Propanamide", "CCC(N)=O"), ("N,N-Dimethylformamide", "CN(C)C=O"), ("N-Methylacetamide", "CNC(C)=O"),
    ("Acetic anhydride", "CC(=O)OC(C)=O"),
    # nitrogênio e enxofre
    ("Ethanamine", "CCN"), ("Propan-1-amine", "CCCN"), ("Butan-1-amine", "CCCCN"), ("Propan-2-amine", "CC(C)N"),
    ("N-Ethylethanamine", "CCNCC"), ("Triethylamine", "CCN(CC)CC"), ("Ethane-1,2-diamine", "NCCN"),
    ("2-Aminoethanol", "NCCO"), ("Propanenitrile", "CCC#N"), ("Butanenitrile", "CCCC#N"),
    ("Prop-2-enenitrile", "C=CC#N"), ("Ethanedinitrile", "N#CC#N"), ("Ethanethiol", "CCS"),
    ("Propane-1-thiol", "CCCS"), ("Diethyl sulfide", "CCSCC"), ("Dimethyl disulfide", "CSSC"),
    ("2-Sulfanylethanol", "OCCS"),
    # halogênios
    ("Chloroethane", "CCCl"), ("Bromoethane", "CCBr"), ("Iodoethane", "CCI"), ("Fluoroethane", "CCF"),
    ("1-Chloropropane", "CCCCl"), ("2-Chloropropane", "CC(C)Cl"), ("2-Bromopropane", "CC(C)Br"),
    ("1,2-Dichloroethane", "ClCCCl"), ("1,2-Dibromoethane", "BrCCBr"), ("Trifluoromethane", "FC(F)F"),
    ("Tetrachloroethene", "ClC(Cl)=C(Cl)Cl"), ("Chloroethene", "ClC=C"), ("Hexafluoroethane", "FC(F)(F)C(F)(F)F"),
    ("Chlorotrifluoromethane", "ClC(F)(F)F"), ("Tribromomethane", "BrC(Br)Br"), ("Diiodomethane", "ICI"),
    # aromáticos (forma de Kekulé)
    ("Chlorobenzene", "ClC1=CC=CC=C1"), ("Bromobenzene", "BrC1=CC=CC=C1"), ("Benzaldehyde", "O=CC1=CC=CC=C1"),
    ("Benzoic acid", "OC(=O)C1=CC=CC=C1"), ("1,2-Dimethylbenzene", "CC1=CC=CC=C1C"),
    ("1,4-Dimethylbenzene", "CC1=CC=C(C)C=C1"), ("Ethylbenzene", "CCC1=CC=CC=C1"),
    ("Ethenylbenzene", "C=CC1=CC=CC=C1"), ("Benzonitrile", "N#CC1=CC=CC=C1"), ("Methoxybenzene", "COC1=CC=CC=C1"),
    ("Pyrimidine", "C1=CN=CN=C1"), ("Pyrazine", "C1=CN=CC=N1"),
    # isotopólogos
    ("(2H1)Methane", "C[2H]"), ("(2H2)Methane", "[2H]C[2H]"), ("(2H3)Methane", "[2H]C([2H])[2H]"),
    ("(13C)Carbon dioxide", "O=[13C]=O"), ("(18O)Water", "[18O]"), ("(15N)Ammonia", "[15N]"),
    ("(2H1)Water", "[2H]O"), ("(3H1)Water", "[3H]O"), ("(1-13C)Ethane", "C[13C]"),
    ("(2H2)Ethyne", "[2H]C#C[2H]"),
]


# ---------- verificação ----------


def compilar(caminho):
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, MAIN, caminho], capture_output=True, env=ambiente)
    saida = (r.stdout + r.stderr).decode("utf-8")
    return r.returncode, [l for l in saida.splitlines() if l.startswith(("Erro ", "Aviso "))]


def nome_de_arquivo(texto):
    texto = texto.lower()
    for de, para in (("áàãâ", "a"), ("éê", "e"), ("í", "i"), ("óôõ", "o"), ("ú", "u"), ("ç", "c")):
        for letra in de:
            texto = texto.replace(letra, para)
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


class Corpus:
    def __init__(self):
        self.contagem = {}
        self.descartados = []

    def valido(self, grupo, nome, codigo):
        if self.contagem.get(grupo, 0) >= QUANTIDADES[grupo]:
            return
        caminho = os.path.join(PASTA, "exemplos", f"{nome_de_arquivo(nome)}.mol")
        if os.path.exists(caminho):
            caminho = caminho[:-4] + f"_{grupo}.mol"
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(codigo)
        saida, mensagens = compilar(caminho)
        if saida != 0 or mensagens:
            os.remove(caminho)
            self.descartados.append((grupo, nome, mensagens[:2]))
            return
        self.contagem[grupo] = self.contagem.get(grupo, 0) + 1

    def invalido(self, grupo, pasta, nome, codigo, regra, saida_esperada):
        """Grava com as linhas '// esperado:' se o compilador acusa a regra."""
        if self.contagem.get(grupo, 0) >= QUANTIDADES[grupo]:
            return
        caminho = os.path.join(PASTA, pasta, f"{nome_de_arquivo(nome)}.mol")
        mensagens = []
        # As linhas esperadas deslocam o código: repete até estabilizar
        for _ in range(4):
            cabeca = "".join(f"// esperado: {m}\n" for m in mensagens) or "// esperado: ?\n"
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(cabeca + codigo)
            saida, novas = compilar(caminho)
            if novas == mensagens:
                break
            mensagens = novas
        if saida != saida_esperada or not any(f"[{regra}]" in m for m in mensagens):
            os.remove(caminho)
            self.descartados.append((grupo, nome, mensagens[:2]))
            return
        self.contagem[grupo] = self.contagem.get(grupo, 0) + 1


def chave_canonica(codigo):
    # Chave do grafo (elementos, ordens, cargas e H por átomo) para não
    # repetir a mesma molécula com outro nome
    import tempfile

    import construtor_ast
    import sintatico
    import tautomeros

    with tempfile.NamedTemporaryFile("w", suffix=".mol", delete=False, encoding="utf-8") as arquivo:
        arquivo.write(codigo)
    try:
        modelo, _ = semantico.analisar(construtor_ast.construir(sintatico.analisar(arquivo.name)))
        return tautomeros.chave(modelo, semantico.carregar_valencias())
    except Exception:
        return codigo
    finally:
        os.remove(arquivo.name)


def ultima_subcamada(config):
    return max(config, key=lambda c: (c[0] + c[1], c[0]))


def main():
    for pasta in ("exemplos", "invalidos", "invalidos_sintaticos", "invalidos_semanticos", "avisos_semanticos"):
        shutil.rmtree(os.path.join(PASTA, pasta), ignore_errors=True)
        os.makedirs(os.path.join(PASTA, pasta))
    corpus = Corpus()

    # Átomos isolados no estado fundamental de referência
    for s in simbolos_ate(86):
        config = atomo.configuracao_fundamental(s, 0, DADOS)
        termo = atomo.texto_termo(atomo.termo_fundamental(config))
        corpus.valido("atomos", f"atomo_{nome_ingles(s)}", especie_atomo(
            s, comentario=f"{nome_ingles(s)} (Z={DADOS[s]['numero_atomico']}): {atomo.texto_configuracao(config)}, termo {termo}"))

    # Isótopos naturais (CIAAW) dos elementos com mais de um, até o Kr
    for s in simbolos_ate(36):
        naturais = ISOTOPOS.get(s) or []
        if len(naturais) < 2:
            continue
        z = DADOS[s]["numero_atomico"]
        for a in naturais:
            corpus.valido("isotopos", f"isotopo_{nome_ingles(s)}_{a}", especie_atomo(
                s, config_texto="", massa=a, titulo=f"{nome_ingles(s)}-{a}",
                comentario=f"{a}{s}: {z} prótons e {a - z} nêutrons, isótopo natural (CIAAW)"))

    for s, carga, nome in IONS:
        nome_final = nome or f"{nome_ingles(s)}({carga}+)"
        corpus.valido("ions", f"ion_{nome_final}", especie_ion(s, carga, nome))

    # Moléculas; a mesma estrutura escrita com outro SMILES (cloroetano e
    # ethyl chloride) entra uma vez só, pela chave canônica do grafo
    vistas = set()
    moleculas_aceitas = []
    for nome, smiles in MOLECULAS + MOLECULAS_RX:
        codigo = f"// {nome} ({smiles})\n" + molecula_para_dsl(nome, smiles)
        chave = chave_canonica(codigo)
        if chave in vistas:
            continue
        vistas.add(chave)
        antes = corpus.contagem.get("moleculas", 0)
        corpus.valido("moleculas", nome, codigo)
        if corpus.contagem.get("moleculas", 0) > antes:
            moleculas_aceitas.append((nome, smiles))

    # ---------- avisos e erros de estrutura atômica ----------
    candidatos = [s for s in simbolos_ate(86) if s not in GASES_NOBRES]
    for s in candidatos[2:]:
        config = atomo.configuracao_fundamental(s, 0, DADOS)
        ultima = ultima_subcamada(config)
        n, l = ultima
        letra = atomo.LETRA_DO_L[l]
        z = DADOS[s]["numero_atomico"]
        menos = dict(config)
        menos[ultima] -= 1
        if not menos[ultima]:
            del menos[ultima]
        corpus.invalido("atom-003", "invalidos_semanticos", f"eletrons_a_menos_{nome_ingles(s)}", especie_atomo(
            s, config_texto=com_nucleo(menos),
            comentario=f"Erro: a configuração soma {z - 1} elétrons, mas {s} tem {z}"), "ATOM-003", 2)

        acima = dict(config)
        acima[ultima] = atomo.capacidade(l) + 1
        if l > 0:
            corpus.invalido("atom-002", "invalidos_semanticos", f"pauli_{nome_ingles(s)}", especie_atomo(
                s, config_texto=com_nucleo(acima),
                comentario=f"Erro: {n}{letra}{atomo.capacidade(l) + 1} passa da capacidade {atomo.capacidade(l)} da subcamada {letra} (Pauli)"),
                "ATOM-002", 2)

        corpus.invalido("atom-001", "invalidos_semanticos", f"massa_menor_que_z_{nome_ingles(s)}", especie_atomo(
            s, config_texto="", massa=z - 1, titulo=f"{nome_ingles(s)}-{z - 1}",
            comentario=f"Erro: A = {z - 1} é menor que Z = {z}, o que daria nêutrons negativos"), "ATOM-001", 2)

        naturais = ISOTOPOS.get(s) or []
        if naturais:
            a = naturais[-1] + 2
            corpus.invalido("atom-005", "avisos_semanticos", f"isotopo_artificial_{nome_ingles(s)}_{a}", especie_atomo(
                s, config_texto="", massa=a, titulo=f"{nome_ingles(s)}-{a}",
                comentario=f"Aviso: {a}{s} não é isótopo natural (CIAAW: {', '.join(map(str, naturais))})"), "ATOM-005", 0)

        # Estado excitado: um elétron da última subcamada sobe para a próxima vazia
        ordem = atomo.ordem_madelung()
        proxima = next(c for c in ordem[ordem.index(ultima) + 1:] if c not in config)
        excitado = dict(menos)
        excitado[proxima] = 1
        corpus.invalido("atom-004", "avisos_semanticos", f"estado_excitado_{nome_ingles(s)}", especie_atomo(
            s, config_texto=com_nucleo(excitado), unpaired=atomo.desemparelhados(excitado),
            comentario=f"Aviso: um elétron de {n}{letra} subiu para {proxima[0]}{atomo.LETRA_DO_L[proxima[1]]}: estado excitado"),
            "ATOM-004", 0)

        hund = atomo.desemparelhados(config)
        corpus.invalido("atom-007", "avisos_semanticos", f"unpaired_contra_hund_{nome_ingles(s)}", especie_atomo(
            s, unpaired=hund + 2,
            comentario=f"Aviso: pela regra de Hund {s} tem {hund} desemparelhado(s), não {hund + 2}"), "ATOM-007", 0)

    # Carga maior que Z: o átomo não tem tantos elétrons para perder
    for s in simbolos_ate(20):
        z = DADOS[s]["numero_atomico"]
        corpus.invalido("atom-008", "invalidos_semanticos", f"carga_maior_que_z_{nome_ingles(s)}", (
            f"// Erro: {s} tem {z} elétron(s); a carga +{z + 1} deixaria -1\n"
            f'species monatomic_ion "{nome_ingles(s)}({z + 1}+)" charge +{z + 1} {{\n'
            f"    atom {s}(+{z + 1})\n}}\n"), "ATOM-008", 2)

    # ---------- erros em moléculas ----------
    for nome, smiles in moleculas_aceitas:
        if "[" in smiles:
            continue
        base = molecula_para_dsl(nome, smiles)
        linhas = base.splitlines()
        primeira = next(i for i, l in enumerate(linhas) if l.strip().startswith("bond "))
        fim = len(linhas) - 1

        mais_h = linhas[:primeira] + ["    atom H as hz", *linhas[primeira:fim], "    bond c1-hz", "}"]
        corpus.invalido("val-001", "invalidos_semanticos", f"valencia_excedida_{nome}",
                        f"// Erro: c1 já tem quatro ligações; a ligação com hz é a quinta\n" + "\n".join(mais_h) + "\n",
                        "VAL-001", 2)

        inexistente = linhas[:fim] + ["    bond c1-q9", "}"]
        corpus.invalido("nome-inexistente", "invalidos_semanticos", f"nome_inexistente_{nome}",
                        "// Erro: q9 não foi declarado com 'as'\n" + "\n".join(inexistente) + "\n", "STRUCT-001", 2)

        repetida = linhas[:fim] + [linhas[primeira], "}"]
        corpus.invalido("ligacao-repetida", "invalidos_semanticos", f"ligacao_repetida_{nome}",
                        f"// Erro: '{linhas[primeira].strip()}' aparece duas vezes\n" + "\n".join(repetida) + "\n",
                        "STRUCT-006", 2)

        solto = linhas[:primeira] + ["    atom Ne as ne1", *linhas[primeira:]]
        corpus.invalido("atomo-solto", "invalidos_semanticos", f"atomo_solto_{nome}",
                        "// Erro: o neônio ne1 foi declarado mas não está ligado ao resto da molécula\n" + "\n".join(solto) + "\n",
                        "STRUCT-003", 2)

        # Sintaxe: um defeito por arquivo, alternando entre quatro tipos
        k = corpus.contagem.get("sintaxe", 0) % 4
        if k == 0:
            texto, regra, nota = "\n".join(linhas[:fim]) + "\n", "SIN-004", "falta o '}' que fecha a espécie"
        elif k == 1:
            alvo = linhas[primeira]
            texto = "\n".join(linhas[:primeira] + [re.sub(r"[-=#]", " ", alvo, count=1)] + linhas[primeira + 1:]) + "\n"
            regra, nota = "SIN-001", "ligação sem operador entre os dois átomos"
        elif k == 2:
            texto = "\n".join(linhas[:primeira] + [linhas[primeira].replace("bond", "bnd", 1)] + linhas[primeira + 1:]) + "\n"
            regra, nota = "SIN-002", "'bnd' não é palavra-chave da linguagem"
        else:
            texto = "\n".join([linhas[0].replace(f'"{nome}"', nome.split()[0].replace(",", "").replace("-", ""))] + linhas[1:]) + "\n"
            regra, nota = "SIN-001", "o nome da espécie precisa estar entre aspas"
        corpus.invalido("sintaxe", "invalidos_sintaticos", f"sintaxe_{nome}", f"// Erro: {nota}\n" + texto, regra, 1)

        # Léxico: caractere fora do alfabeto da linguagem
        caractere = "@$%&?!;|^`"[corpus.contagem.get("lexico", 0) % 10]
        texto = "\n".join(linhas[:primeira] + [linhas[primeira] + f" {caractere}"] + linhas[primeira + 1:]) + "\n"
        corpus.invalido("lexico", "invalidos", f"caractere_{nome}",
                        f"// Erro: '{caractere}' não pertence ao alfabeto da linguagem\n" + texto, "LEX-001", 1)

    total = sum(corpus.contagem.values())
    for grupo, quantidade in QUANTIDADES.items():
        obtido = corpus.contagem.get(grupo, 0)
        marca = "" if obtido == quantidade else "  <-- faltam"
        print(f"{grupo:18} {obtido:3}/{quantidade}{marca}")
    print(f"total: {total}")
    if corpus.descartados:
        print(f"descartados: {len(corpus.descartados)}")
        for grupo, nome, mensagens in corpus.descartados:
            print(f"  {grupo}: {nome}: {mensagens}")
    return 0 if total == sum(QUANTIDADES.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
