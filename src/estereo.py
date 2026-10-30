from collections import deque
from dataclasses import dataclass, field

import eletronico


# Estereoquímica sobre a constituição (fase 8 e plano de limites, L8/L9).
#
# Elementos candidatos:
# - centro tetraédrico: quatro vizinhos sem par livre (com ligações
#   simples, ou P, S, As, Se com ligações múltiplas), ou P, S, As, Se com
#   três vizinhos e um par livre, que conta como o substituinte de menor
#   prioridade. O N fica fora: ele inverte rápido;
# - ligação dupla E/Z, inclusive no centro de cumulenos com número ímpar
#   de ligações duplas, fora de anéis com menos de oito átomos;
# - eixo de aleno (cumuleno com número par de ligações duplas), Ra/Sa;
# - eixo de biarila, só quando declarado: a barreira de rotação não é
#   calculada a partir do grafo.
#
# Um candidato com dois substituintes de mesma constituição só continua
# candidato se esses ramos contêm outros candidatos (centro
# pseudoassimétrico, r/s) ou se são os dois sentidos de um mesmo anel.
#
# A contagem de estereoisômeros enumera as configurações dos candidatos e
# as agrupa pelo grupo de automorfismos do grafo (com os H terminais
# recolhidos no átomo dono). Isso dá a quantidade exata, já sem as
# formas meso, os pares de enantiômeros e quais candidatos são de fato
# estereogênicos.
#
# Prioridades CIP: regra 1a (número atômico, esfera a esfera, com
# duplicatas para ligações múltiplas e fechamentos de anel). Empates
# entre ramos de mesma constituição usam as regras 3 (Z > E), 4
# (semelhante antes de diferente) e 5 (R > S) sobre os descritores
# declarados. A regra 2 (número de massa, IUPAC P-92.3) só entra depois
# da regra 1 esgotada: a chave de cada ramo é o par (esferas de números
# atômicos, esferas de massas). Um átomo sem número de massa declarado
# conta com a massa atômica da composição natural, como no exemplo da
# IUPAC '81Br > Br > 79Br'; a duplicata tem a massa do átomo duplicado.

TAMANHO_MINIMO_ANEL_E_Z = 8
PIRAMIDAIS = {"P", "S", "As", "Se"}
LIMITE_AUTOMORFISMOS = 20000
LIMITE_TRABALHO = 2_000_000

DESCRITORES = {
    "centro": {"R", "S"},
    "pseudo": {"r", "s"},
    "dupla": {"E", "Z"},
    "eixo": {"Ra", "Sa"},
    "atropo": {"Ra", "Sa"},
    "relativo": {"cis", "trans"},
}
ESPELHO = {"R": "S", "S": "R", "Ra": "Sa", "Sa": "Ra"}


def par_livre(dono):
    return ("LP", dono)


def ordem_chave(chave):
    # Átomos (int) antes dos pares livres
    return (0, chave) if isinstance(chave, int) else (1, chave[1])


def paridade(sequencia):
    # 0 se a permutação que ordena a sequência é par, 1 se é ímpar
    inversoes = 0
    for i in range(len(sequencia)):
        for j in range(i + 1, len(sequencia)):
            if sequencia[i] > sequencia[j]:
                inversoes += 1
    return inversoes % 2


@dataclass
class Elemento:
    tipo: str  # "centro", "dupla", "eixo" ou "atropo"
    atomos: tuple  # centro: (c,); demais: (a, b) com a < b
    lados: tuple  # centro: (vizinhos,); demais: (substituintes de a, de b)
    internos: tuple = ()
    pseudo: str | None = None  # "ramos" ou "anel" para centros com ramos iguais
    prioridades: list = field(default_factory=list)

    @property
    def chave(self):
        return self.atomos[0] if self.tipo == "centro" else frozenset(self.atomos)

    @property
    def tetraedrico(self):
        return self.tipo != "dupla"

    def tupla(self):
        if self.tipo == "centro":
            return tuple(sorted(self.lados[0], key=ordem_chave))
        a, b = self.lados
        return tuple(sorted(a, key=ordem_chave)) + tuple(sorted(b, key=ordem_chave))


# ---------- grafo e prioridades CIP ----------


def grafo(modelo, valencias):
    ordens = eletronico.ordens_do_modelo(modelo, valencias)
    vizinhos = {a.id: {} for a in modelo.atomos}
    for (a, b), ordem in ordens.items():
        vizinhos[a][b] = ordem
        vizinhos[b][a] = ordem
    return vizinhos


class Arvore:
    """Dígrafo hierárquico de CIP, explorado até uma profundidade."""

    def __init__(self, vizinhos, numero_atomico, massa=None):
        self.vizinhos = vizinhos
        self.z = numero_atomico
        self.massa = massa or {}

    def esferas(self, atomo, pai, ordem_pai, caminho, profundidade, valor=None):
        # Esferas do ramo como tuplas de valores (número atômico na regra
        # 1, massa na regra 2), cada uma em ordem decrescente de prioridade
        valor = valor if valor is not None else self.z
        if isinstance(atomo, tuple):
            return [(0,)]
        resultado = [(valor[atomo],)]
        if profundidade == 0:
            return resultado
        filhos = []
        for vizinho, ordem in self.vizinhos[atomo].items():
            if vizinho == pai:
                continue
            if vizinho in caminho:
                # Fechamento de anel: átomo duplicado, sem filhos
                filhos.append([(valor[vizinho],)])
            else:
                filhos.append(
                    self.esferas(
                        vizinho, atomo, ordem, caminho | {vizinho}, profundidade - 1, valor
                    )
                )
            # Ligação múltipla: duplicatas do vizinho
            for _ in range(ordem - 1):
                filhos.append([(valor[vizinho],)])
        if pai is not None:
            for _ in range(ordem_pai - 1):
                filhos.append([(valor[pai],)])
        filhos.sort(key=chave_esferas, reverse=True)
        maior = max((len(f) for f in filhos), default=0)
        for nivel in range(maior):
            camada = []
            for filho in filhos:
                if nivel < len(filho):
                    camada.extend(filho[nivel])
            resultado.append(tuple(camada))
        return resultado

    def chaves(self, centro, ligados):
        # Chave de cada ramo, aprofundando até separar os ramos ou até as
        # árvores pararem de crescer
        anteriores = None
        for profundidade in range(1, len(self.vizinhos) + 1):
            chaves = {}
            for vizinho in ligados:
                ordem = (
                    self.vizinhos[centro].get(vizinho, 1)
                    if isinstance(vizinho, int)
                    else 1
                )
                chaves[vizinho] = self.chave_ramo(vizinho, centro, ordem, profundidade)
            if len(set(chaves.values())) == len(chaves) or chaves == anteriores:
                return chaves
            anteriores = chaves
        return anteriores or {}

    def chave_ramo(self, vizinho, centro, ordem, profundidade):
        # Regra 1 inteira antes da regra 2: o par compara primeiro os
        # números atômicos e só no empate as massas
        if not isinstance(vizinho, int):
            return (((0,),), ((0,),))
        argumentos = (vizinho, centro, ordem, {centro, vizinho}, profundidade)
        return (
            chave_esferas(self.esferas(*argumentos, self.z)),
            chave_esferas(self.esferas(*argumentos, self.massa or self.z)),
        )


def chave_esferas(esferas):
    # Na comparação de tuplas, a esfera menor perde como prefixo: é o
    # mesmo que completar com átomos fantasmas de número atômico 0
    return tuple(tuple(camada) for camada in esferas)


def ramo(vizinhos, centro, inicio):
    # Átomos alcançados a partir de inicio sem passar pelo centro
    if not isinstance(inicio, int):
        return set()
    visto = {inicio}
    pilha = [inicio]
    while pilha:
        atual = pilha.pop()
        for vizinho in vizinhos[atual]:
            if vizinho != centro and vizinho not in visto:
                visto.add(vizinho)
                pilha.append(vizinho)
    return visto


def tamanho_menor_anel(vizinhos, a, b):
    # Menor ciclo que contém a ligação a-b, ou None se ela não está em anel
    distancia = {a: 0}
    fila = deque([a])
    while fila:
        atual = fila.popleft()
        for vizinho in vizinhos[atual]:
            if {atual, vizinho} == {a, b} or vizinho in distancia:
                continue
            distancia[vizinho] = distancia[atual] + 1
            if vizinho == b:
                return distancia[vizinho] + 1
            fila.append(vizinho)
    return None


# ---------- candidatos ----------


def cadeias_cumuladas(vizinhos):
    # Cadeias a=x=...=b de ligações duplas, com os átomos internos (dois
    # vizinhos, ambos por ligação dupla)
    internos = {
        x
        for x, ligados in vizinhos.items()
        if len(ligados) == 2 and all(o == 2 for o in ligados.values())
    }
    vistas = set()
    cadeias = []
    for a, ligados in vizinhos.items():
        for b, ordem in ligados.items():
            if ordem != 2 or frozenset((a, b)) in vistas or a in internos:
                continue
            cadeia = [a, b]
            vistas.add(frozenset((a, b)))
            while cadeia[-1] in internos:
                seguinte = next(v for v in vizinhos[cadeia[-1]] if v != cadeia[-2])
                vistas.add(frozenset((cadeia[-1], seguinte)))
                cadeia.append(seguinte)
            cadeias.append(cadeia)
    return cadeias


def massas_cip(modelo, dados_elementos):
    # Massa de cada átomo para a regra 2: o número de massa declarado ou,
    # sem ele, a massa atômica da composição natural (ou o número
    # atômico, se a fonte não tem a massa)
    massas = {}
    for atomo in modelo.atomos:
        dados = dados_elementos.get(atomo.elemento, {})
        natural = dados.get("massa_atomica")
        if natural is None:
            natural = dados.get("numero_atomico", 0)
        massas[atomo.id] = atomo.massa if getattr(atomo, "massa", None) is not None else natural
    return massas


def candidatos(modelo, vizinhos, pares_livres, arvore, declarados_atropo):
    brutos = []

    for atomo in modelo.atomos:
        ligados = vizinhos[atomo.id]
        lp = pares_livres.get(atomo.id)
        if len(ligados) == 4 and lp == 0 and (
            all(o == 1 for o in ligados.values()) or atomo.elemento in PIRAMIDAIS
        ):
            brutos.append(Elemento("centro", (atomo.id,), (list(ligados),)))
        elif len(ligados) == 3 and lp == 1 and atomo.elemento in PIRAMIDAIS:
            brutos.append(
                Elemento("centro", (atomo.id,), ([*ligados, par_livre(atomo.id)],))
            )

    for cadeia in cadeias_cumuladas(vizinhos):
        a, b = cadeia[0], cadeia[-1]
        if any(
            (tamanho := tamanho_menor_anel(vizinhos, x, y)) is not None
            and tamanho < TAMANHO_MINIMO_ANEL_E_Z
            for x, y in zip(cadeia, cadeia[1:])
        ):
            continue
        lados = []
        for ponta, proximo in ((a, cadeia[1]), (b, cadeia[-2])):
            outros = [v for v, o in vizinhos[ponta].items() if v != proximo]
            if any(vizinhos[ponta][v] > 1 for v in outros):
                break
            if len(outros) == 2:
                lados.append(outros)
            elif len(outros) == 1 and (pares_livres.get(ponta) or 0) >= 1:
                lados.append([outros[0], par_livre(ponta)])
            else:
                break
        if len(lados) != 2:
            continue
        ligacoes = len(cadeia) - 1
        tipo = "dupla" if ligacoes % 2 else "eixo"
        (pa, la), (pb, lb) = sorted(((a, lados[0]), (b, lados[1])))
        brutos.append(Elemento(tipo, (pa, pb), (la, lb), tuple(cadeia[1:-1])))

    for a, b in declarados_atropo:
        elemento = criar_atropo(vizinhos, a, b)
        if elemento is not None:
            brutos.append(elemento)

    # Ponto fixo: descarta candidatos com dois ramos iguais que não
    # contêm candidatos nem formam um anel com o átomo
    atuais = brutos
    while True:
        atomos_candidatos = {x for e in atuais for x in (*e.atomos, *e.internos)}
        seguintes = []
        for elemento in atuais:
            situacao = ramos_iguais(elemento, vizinhos, arvore, atomos_candidatos)
            if situacao == "trivial":
                continue
            if elemento.tipo == "centro":
                elemento.pseudo = situacao
            seguintes.append(elemento)
        if len(seguintes) == len(atuais):
            break
        atuais = seguintes
    for elemento in atuais:
        elemento.prioridades = prioridades_constitucionais(elemento, arvore)
    return atuais


def criar_atropo(vizinhos, a, b):
    # Eixo de biarila: cada ponta com dois outros vizinhos
    if b not in vizinhos.get(a, {}) or vizinhos[a][b] != 1:
        return None
    lados = []
    for ponta, outra in ((a, b), (b, a)):
        outros = [v for v in vizinhos[ponta] if v != outra]
        if len(outros) != 2:
            return None
        lados.append(outros)
    (pa, la), (pb, lb) = sorted(((a, lados[0]), (b, lados[1])))
    return Elemento("atropo", (pa, pb), (la, lb))


def grupos_de_ramos(elemento):
    # Listas de substituintes comparados entre si (um por ponta)
    if elemento.tipo == "centro":
        return [(elemento.atomos[0], elemento.lados[0])]
    return list(zip(elemento.atomos, elemento.lados))


def ramos_iguais(elemento, vizinhos, arvore, atomos_candidatos):
    # None (ramos distintos), "trivial" (não estereogênico), "ramos" ou
    # "anel" (dois ramos iguais que ainda podem ser estereogênicos)
    situacao = None
    for dono, substituintes in grupos_de_ramos(elemento):
        chaves = arvore.chaves(dono, substituintes)
        valores = list(chaves.values())
        repetidos = [v for v in set(valores) if valores.count(v) > 1]
        if not repetidos:
            continue
        if elemento.tipo != "centro" or len(repetidos) > 1 or valores.count(
            repetidos[0]
        ) > 2:
            # Duas pontas iguais numa dupla, ou mais de um par igual num
            # centro: só um anel comum mantém o candidato (espiranos)
            iguais = [s for s in substituintes if chaves[s] in repetidos]
            if not all(mesmo_anel(vizinhos, dono, s, iguais) for s in iguais):
                return "trivial"
            situacao = "anel"
            continue
        u, v = [s for s in substituintes if chaves[s] == repetidos[0]]
        if mesmo_anel(vizinhos, dono, u, [v]):
            situacao = "anel"
        elif (ramo(vizinhos, dono, u) | ramo(vizinhos, dono, v)) & atomos_candidatos:
            situacao = "ramos"
        else:
            return "trivial"
    return situacao


def mesmo_anel(vizinhos, dono, u, outros):
    alcancados = ramo(vizinhos, dono, u)
    return all(isinstance(o, int) and o in alcancados for o in outros if o != u)


def prioridades_constitucionais(elemento, arvore):
    # Ordem CIP de cada grupo de substituintes; ramos iguais ficam juntos
    # numa sublista, para o desempate pelos descritores declarados
    resultado = []
    for dono, substituintes in grupos_de_ramos(elemento):
        chaves = arvore.chaves(dono, substituintes)
        niveis = {}
        for s in substituintes:
            niveis.setdefault(chaves[s], []).append(s)
        resultado.append(
            [sorted(grupo, key=ordem_chave) for _, grupo in sorted(niveis.items(), reverse=True)]
        )
    return resultado


# ---------- simetria ----------


def massa_do_atomo(atomo):
    # Número de massa declarado; 0 para a composição natural
    return getattr(atomo, "massa", None) or 0


def automorfismos(modelo, vizinhos, limite=LIMITE_AUTOMORFISMOS):
    """Automorfismos do grafo, com os H terminais recolhidos no dono.

    Devolve uma lista de mapas completos (átomo -> átomo), ou None se o
    grupo passa do limite.
    """
    por_id = {a.id: a for a in modelo.atomos}
    terminal = {
        a.id
        for a in modelo.atomos
        if a.elemento == "H" and len(vizinhos[a.id]) == 1
    }
    pesados = [a.id for a in modelo.atomos if a.id not in terminal]
    # H terminais em ordem de massa, para o deutério só trocar com deutério
    hidrogenios = {
        x: sorted(
            (h for h in vizinhos[x] if h in terminal),
            key=lambda h: (massa_do_atomo(por_id[h]), h),
        )
        for x in pesados
    }
    ligacoes = {
        x: {y: o for y, o in vizinhos[x].items() if y not in terminal} for x in pesados
    }
    cor = {
        x: repr(
            (
                por_id[x].elemento,
                por_id[x].carga,
                massa_do_atomo(por_id[x]),
                [massa_do_atomo(por_id[h]) for h in hidrogenios[x]],
            )
        )
        for x in pesados
    }
    while True:
        assinatura = {
            x: repr((cor[x], sorted((cor[y], o) for y, o in ligacoes[x].items())))
            for x in pesados
        }
        rotulos = {valor: i for i, valor in enumerate(sorted(set(assinatura.values())))}
        nova = {x: rotulos[assinatura[x]] for x in pesados}
        estavel = len(set(nova.values())) == len(set(cor.values()))
        cor = nova
        if estavel:
            break

    # Ordem de busca: em largura, começando pelas menores classes de cor
    tamanho = {c: list(cor.values()).count(c) for c in set(cor.values())}
    ordem = []
    vistos = set()
    for inicio in sorted(pesados, key=lambda x: (tamanho[cor[x]], x)):
        if inicio in vistos:
            continue
        fila = deque([inicio])
        vistos.add(inicio)
        while fila:
            atual = fila.popleft()
            ordem.append(atual)
            for y in sorted(ligacoes[atual], key=lambda y: (tamanho[cor[y]], y)):
                if y not in vistos:
                    vistos.add(y)
                    fila.append(y)

    mapas = []
    mapa = {}
    usados = set()
    excedeu = False

    def visitar(indice):
        nonlocal excedeu
        if excedeu:
            return
        if indice == len(ordem):
            if len(mapas) >= limite:
                excedeu = True
                return
            mapas.append(dict(mapa))
            return
        x = ordem[indice]
        for y in pesados:
            if y in usados or cor[y] != cor[x]:
                continue
            if all(
                ligacoes[x].get(u, 0) == ligacoes[y].get(mapa[u], 0) for u in mapa
            ):
                mapa[x] = y
                usados.add(y)
                visitar(indice + 1)
                usados.discard(y)
                del mapa[x]

    visitar(0)
    if excedeu:
        return None
    completos = []
    for mapa in mapas:
        completo = dict(mapa)
        for x in pesados:
            for h, imagem in zip(hidrogenios[x], hidrogenios[mapa[x]]):
                completo[h] = imagem
        completos.append(completo)
    return completos


def aplicar(mapa, chave):
    if isinstance(chave, int):
        return mapa[chave]
    return (chave[0], mapa[chave[1]])


def acoes(elementos, mapas):
    """Para cada automorfismo, a permutação dos elementos e as trocas de bit."""
    indice = {e.chave: i for i, e in enumerate(elementos)}
    tuplas = [e.tupla() for e in elementos]
    resultado = []
    for mapa in mapas:
        destino = []
        troca = []
        for e, tupla in zip(elementos, tuplas):
            imagem = (
                mapa[e.atomos[0]]
                if e.tipo == "centro"
                else frozenset(mapa[x] for x in e.atomos)
            )
            j = indice.get(imagem)
            if j is None:
                break
            nova = tuplas[j]
            mapeada = [aplicar(mapa, k) for k in tupla]
            if e.tetraedrico:
                posicoes = [nova.index(k) for k in mapeada]
                troca.append(paridade(posicoes))
            else:
                troca.append(nova.index(mapeada[0]) % 2 ^ nova.index(mapeada[2]) % 2)
            destino.append(j)
        else:
            resultado.append((destino, troca))
    return resultado


def fechar_sob_simetria(elementos, mapas, vizinhos):
    # Imagens de eixos declarados também entram, para o grupo agir no
    # conjunto de elementos
    chaves = {e.chave for e in elementos}
    novos = list(elementos)
    for e in elementos:
        if e.tipo != "atropo":
            continue
        for mapa in mapas:
            a, b = (mapa[x] for x in e.atomos)
            imagem = frozenset((a, b))
            if imagem not in chaves:
                criado = criar_atropo(vizinhos, a, b)
                if criado is not None:
                    chaves.add(imagem)
                    novos.append(criado)
    return novos


class Classes:
    """Configurações agrupadas pelo grupo de automorfismos."""

    def __init__(self, elementos, mapas):
        self.elementos = elementos
        self.acoes = acoes(elementos, mapas)
        self.tetraedricos = sum(
            1 << i for i, e in enumerate(elementos) if e.tetraedrico
        )

    def transformar(self, bits, acao):
        destino, troca = acao
        novo = 0
        for i, j in enumerate(destino):
            if (bits >> i & 1) ^ troca[i]:
                novo |= 1 << j
        return novo

    def canonica(self, bits):
        return min(self.transformar(bits, acao) for acao in self.acoes)

    def espelho(self, bits):
        return bits ^ self.tetraedricos


# ---------- análise ----------


@dataclass
class Resultado:
    elementos: list
    estereogenicos: list
    classes: dict | None  # canônica -> canônica do espelho
    motivo_contagem: str | None
    declarados: dict  # índice do elemento -> descritor
    relativos: list  # (i, j, "cis"|"trans")
    compativeis: list | None  # classes compatíveis com as declarações


def analisar(modelo, dados_elementos, valencias, declaracoes=None):
    """Devolve (Resultado, motivo, mensagens).

    declaracoes é a lista de modelo.estereo; mensagens são tuplas
    (codigo, severidade, declaracao, texto) para a análise semântica.
    """
    declaracoes = declaracoes if declaracoes is not None else getattr(modelo, "estereo", [])
    vizinhos = grafo(modelo, valencias)
    z = {}
    for atomo in modelo.atomos:
        numero = dados_elementos.get(atomo.elemento, {}).get("numero_atomico")
        if numero is None:
            return None, f"falta o número atômico de {atomo.elemento}", []
        z[atomo.id] = numero
    arvore = Arvore(vizinhos, z, massas_cip(modelo, dados_elementos))
    pares_livres = {
        estado.atomo.id: estado.pares_livres
        for estado in eletronico.estados(modelo, dados_elementos, valencias)
    }
    atropos = [tuple(d.atomos) for d in declaracoes if d.operador == "-"]
    elementos = candidatos(modelo, vizinhos, pares_livres, arvore, atropos)
    mensagens = []

    mapas = automorfismos(modelo, vizinhos) if elementos else [{}]
    if elementos and mapas is not None:
        elementos = fechar_sob_simetria(elementos, mapas, vizinhos)
        for e in elementos:
            if not e.prioridades:
                e.prioridades = prioridades_constitucionais(e, arvore)
    quantidade = len(elementos)
    motivo_contagem = None
    classes = None
    estereogenicos = list(range(quantidade))
    calculo = None
    if mapas is None:
        motivo_contagem = (
            f"o grafo tem mais de {LIMITE_AUTOMORFISMOS} automorfismos"
        )
    elif (1 << quantidade) * len(mapas) * max(quantidade, 1) > LIMITE_TRABALHO:
        motivo_contagem = (
            f"{quantidade} candidatos e {len(mapas)} automorfismos passam do "
            "limite da enumeração"
        )
    else:
        calculo = Classes(elementos, mapas)
        canonicas = {}
        for bits in range(1 << quantidade):
            canonicas[bits] = calculo.canonica(bits)
        estereogenicos = [
            i
            for i in range(quantidade)
            if any(canonicas[b] != canonicas[b ^ (1 << i)] for b in canonicas)
        ]
        classes = {}
        for bits, canonica in canonicas.items():
            classes.setdefault(canonica, canonicas[calculo.espelho(bits)])

    declarados, relativos, compativeis = interpretar(
        modelo, declaracoes, elementos, estereogenicos, arvore, vizinhos, calculo, mensagens
    )
    return (
        Resultado(
            elementos,
            estereogenicos,
            classes,
            motivo_contagem,
            declarados,
            relativos,
            compativeis,
        ),
        None,
        mensagens,
    )


# ---------- declarações ----------


def localizar(declaracao, elementos):
    # Índice do elemento citado pela declaração, ou None
    atomos = tuple(declaracao.atomos)
    for i, e in enumerate(elementos):
        if declaracao.operador is None and len(atomos) == 1:
            if e.tipo == "centro" and e.atomos == atomos:
                return i
            if e.tipo == "eixo" and atomos[0] in e.internos:
                return i
        elif declaracao.operador == "=" and e.tipo == "dupla":
            cadeia = (e.atomos[0], *e.internos, e.atomos[1])
            pares = {frozenset(p) for p in zip(cadeia, cadeia[1:])}
            if frozenset(atomos) in pares:
                return i
        elif declaracao.operador == "-" and e.tipo == "atropo":
            if frozenset(atomos) == frozenset(e.atomos):
                return i
    return None


def tipo_descritor(elemento):
    if elemento.tipo == "centro" and elemento.pseudo == "ramos":
        return "pseudo"
    return elemento.tipo


def desempatar(elemento, grupo, dono, vizinhos, declarados_por_atomo):
    """Ordena ramos de mesma constituição pelas regras 3, 4 e 5.

    Devolve (lista ordenada, None) ou (None, motivo), com motivo
    "faltam" (há ramo sem descritor declarado) ou "empate" (os ramos têm
    os mesmos descritores, e o centro não é estereogênico).
    """
    chaves = {}
    for s in grupo:
        atomos_ramo = ramo(vizinhos, dono, s)
        distancias = distancias_de(vizinhos, s, dono)
        encontrados = sorted(
            (distancias[x], declarados_por_atomo[x])
            for x in atomos_ramo
            if x in declarados_por_atomo
        )
        if not encontrados:
            return None, "faltam"
        referencia = encontrados[0][1]
        regra3 = tuple(1 if d == "Z" else 0 for _, d in encontrados if d in ("E", "Z"))
        regra4 = tuple(
            1 if d == referencia else 0 for _, d in encontrados if d in ("R", "S", "Ra", "Sa")
        )
        regra5 = tuple(1 if d in ("R", "Ra", "r") else 0 for _, d in encontrados)
        chaves[s] = (regra3, regra4, regra5)
    if len(set(chaves.values())) != len(chaves):
        return None, "empate"
    return sorted(grupo, key=lambda s: chaves[s], reverse=True), None


def distancias_de(vizinhos, inicio, proibido):
    distancia = {inicio: 0}
    fila = deque([inicio])
    while fila:
        atual = fila.popleft()
        for vizinho in vizinhos[atual]:
            if vizinho != proibido and vizinho not in distancia:
                distancia[vizinho] = distancia[atual] + 1
                fila.append(vizinho)
    return distancia


def ordem_completa(elemento, vizinhos, declarados_por_atomo):
    # (lista de substituintes por ponta em ordem CIP, None), ou
    # (None, motivo) quando um empate não se resolve
    grupos = []
    for (dono, _), niveis in zip(grupos_de_ramos(elemento), elemento.prioridades):
        ordem = []
        for nivel in niveis:
            if len(nivel) == 1:
                ordem.extend(nivel)
                continue
            desempatado, motivo = desempatar(
                elemento, nivel, dono, vizinhos, declarados_por_atomo
            )
            if desempatado is None:
                return None, motivo
            ordem.extend(desempatado)
        grupos.append(ordem)
    return grupos, None


def bit_do_descritor(elemento, ordem, descritor):
    # Convenção interna: bit 0 quando a tupla canônica do elemento tem
    # a mesma quiralidade da ordem CIP de um descritor R (ou Ra); na
    # dupla, bit 1 quando os primeiros da tupla ficam do mesmo lado
    tupla = elemento.tupla()
    if elemento.tetraedrico:
        prioridade = ordem[0] if elemento.tipo == "centro" else ordem[0] + ordem[1]
        sinal = paridade([prioridade.index(k) for k in tupla])
        direto = 0 if descritor in ("R", "r", "Ra") else 1
        return direto ^ sinal
    topo_a, topo_b = ordem[0][0], ordem[1][0]
    cis = 1 if descritor == "Z" else 0
    return cis ^ (tupla[0] != topo_a) ^ (tupla[2] != topo_b)


def descritor_do_bit(elemento, ordem, bit):
    for descritor in sorted(DESCRITORES[tipo_descritor(elemento)]):
        if bit_do_descritor(elemento, ordem, descritor) == bit:
            return descritor
    return None


def relacao_em_anel(elemento_a, elemento_b, vizinhos, arvore):
    """Diferença de bit que corresponde a cis entre dois centros de anel.

    Percorrendo o anel num sentido, o substituinte de maior prioridade de
    cada átomo fica do mesmo lado do plano quando a quiralidade de
    (anterior, seguinte, maior, menor) é a mesma nos dois átomos.
    Devolve None se os centros não estão num anel comum com dois
    substituintes de fora distintos.
    """
    a, b = elemento_a.atomos[0], elemento_b.atomos[0]
    anel = menor_anel_comum(vizinhos, a, b)
    if anel is None:
        return None
    sinais = []
    for elemento, posicao in ((elemento_a, anel.index(a)), (elemento_b, anel.index(b))):
        x = elemento.atomos[0]
        anterior = anel[posicao - 1]
        seguinte = anel[(posicao + 1) % len(anel)]
        fora = [k for k in elemento.lados[0] if k not in (anterior, seguinte)]
        if len(fora) != 2:
            return None
        chaves = arvore.chaves(x, fora)
        if chaves[fora[0]] == chaves[fora[1]]:
            return None
        maior, menor = sorted(fora, key=lambda k: chaves[k], reverse=True)
        sequencia = [anterior, seguinte, maior, menor]
        tupla = elemento.tupla()
        sinais.append(paridade([sequencia.index(k) for k in tupla]))
    return sinais[0] ^ sinais[1]


def menor_anel_comum(vizinhos, a, b):
    # Menor ciclo que passa por a e b: dois caminhos disjuntos entre eles
    melhor = None
    for primeiro in vizinhos[a]:
        caminho = caminho_minimo(vizinhos, primeiro, b, proibidos={a})
        if caminho is None:
            continue
        internos = set(caminho[:-1])
        for segundo in vizinhos[a]:
            if segundo == primeiro or segundo in internos:
                continue
            volta = caminho_minimo(vizinhos, segundo, b, proibidos={a} | internos)
            if volta is None:
                continue
            anel = [a, *caminho, *reversed(volta[:-1])]
            if melhor is None or len(anel) < len(melhor):
                melhor = anel
    return melhor


def caminho_minimo(vizinhos, inicio, fim, proibidos):
    if inicio in proibidos:
        return None
    anterior = {inicio: None}
    fila = deque([inicio])
    while fila:
        atual = fila.popleft()
        if atual == fim:
            caminho = [fim]
            while anterior[caminho[-1]] is not None:
                caminho.append(anterior[caminho[-1]])
            return caminho[::-1]
        for vizinho in vizinhos[atual]:
            if vizinho not in anterior and vizinho not in proibidos:
                anterior[vizinho] = atual
                fila.append(vizinho)
    return None


def interpretar(modelo, declaracoes, elementos, estereogenicos, arvore, vizinhos, calculo, mensagens):
    por_id = {a.id: a for a in modelo.atomos}
    declarados = {}
    relativos = []
    descritores_por_atomo = {}
    pendentes = []

    def nome(declaracao):
        if declaracao.operador is None and len(declaracao.atomos) == 2:
            return " ".join(por_id[x].rotulo() for x in declaracao.atomos)
        separador = declaracao.operador or ""
        return separador.join(por_id[x].rotulo() for x in declaracao.atomos)

    for declaracao in declaracoes:
        if declaracao.operador == "-":
            mensagens.append(
                (
                    "STEREO-005",
                    "aviso",
                    declaracao,
                    f"eixo {nome(declaracao)} declarado como estereogênico; a "
                    "barreira de rotação não é verificada a partir do grafo",
                )
            )
        if declaracao.descritor in DESCRITORES["relativo"]:
            indices = []
            for atomo in declaracao.atomos:
                encontrado = next(
                    (
                        i
                        for i, e in enumerate(elementos)
                        if e.tipo == "centro" and e.atomos == (atomo,)
                    ),
                    None,
                )
                indices.append(encontrado)
            if (
                len(indices) != 2
                or None in indices
                or any(i not in estereogenicos for i in indices)
            ):
                mensagens.append(
                    (
                        "STEREO-001",
                        "erro",
                        declaracao,
                        f"{nome(declaracao)}: cis/trans exige dois centros "
                        "estereogênicos do mesmo anel",
                    )
                )
                continue
            diferenca = relacao_em_anel(
                elementos[indices[0]], elementos[indices[1]], vizinhos, arvore
            )
            if diferenca is None:
                mensagens.append(
                    (
                        "STEREO-001",
                        "erro",
                        declaracao,
                        f"{nome(declaracao)}: os centros não estão num anel comum "
                        "com dois substituintes de fora distintos",
                    )
                )
                continue
            alvo = diferenca if declaracao.descritor == "cis" else diferenca ^ 1
            relativos.append((indices[0], indices[1], declaracao.descritor, alvo, declaracao))
            continue
        if len(declaracao.atomos) == 2 and declaracao.operador is None:
            mensagens.append(
                (
                    "STEREO-002",
                    "erro",
                    declaracao,
                    f"dois átomos sem operador aceitam só cis ou trans, "
                    f"encontrado '{declaracao.descritor}'",
                )
            )
            continue
        indice = localizar(declaracao, elementos)
        if indice is None or indice not in estereogenicos:
            mensagens.append(
                (
                    "STEREO-001",
                    "erro",
                    declaracao,
                    f"{nome(declaracao)} não é um elemento estereogênico",
                )
            )
            continue
        elemento = elementos[indice]
        tipo = tipo_descritor(elemento)
        if declaracao.descritor not in DESCRITORES[tipo]:
            esperado = " ou ".join(sorted(DESCRITORES[tipo]))
            dica = ""
            if elemento.pseudo == "anel":
                dica = "; para centros de anel com ramos iguais, use cis/trans entre dois átomos"
            mensagens.append(
                (
                    "STEREO-002",
                    "erro",
                    declaracao,
                    f"{nome(declaracao)} aceita {esperado}, encontrado "
                    f"'{declaracao.descritor}'{dica}",
                )
            )
            continue
        if indice in declarados:
            mensagens.append(
                (
                    "STEREO-003",
                    "erro",
                    declaracao,
                    f"{nome(declaracao)} já tem configuração declarada",
                )
            )
            continue
        declarados[indice] = declaracao.descritor
        pendentes.append((indice, declaracao))
        for x in (*elemento.atomos, *elemento.internos):
            descritores_por_atomo[x] = declaracao.descritor

    # Bits das declarações absolutas; as que dependem de outras (regras
    # 3 a 5) esperam até os descritores dos ramos estarem disponíveis
    bits = {}
    for indice, declaracao in pendentes:
        elemento = elementos[indice]
        outros = {
            x: d for x, d in descritores_por_atomo.items()
            if x not in (*elemento.atomos, *elemento.internos)
        }
        ordem, motivo = ordem_completa(elemento, vizinhos, outros)
        if motivo == "empate":
            mensagens.append(
                (
                    "STEREO-001",
                    "erro",
                    declaracao,
                    f"{nome(declaracao)} não é estereogênico com as demais "
                    "configurações declaradas: os ramos iguais têm os mesmos descritores",
                )
            )
            del declarados[indice]
            continue
        if ordem is None:
            mensagens.append(
                (
                    "STEREO-004",
                    "erro",
                    declaracao,
                    f"{nome(declaracao)}: os ramos de mesma constituição só se "
                    "distinguem pela configuração; declare a dos centros desses ramos",
                )
            )
            del declarados[indice]
            continue
        bits[indice] = bit_do_descritor(elemento, ordem, declaracao.descritor)

    if calculo is None or not (bits or relativos):
        return declarados, relativos, None

    compativeis = set()
    quantidade = len(elementos)
    satisfazem = []
    for configuracao in range(1 << quantidade):
        if any((configuracao >> i & 1) != b for i, b in bits.items()):
            continue
        if any(
            ((configuracao >> i & 1) ^ (configuracao >> j & 1)) != alvo
            for i, j, _, alvo, _ in relativos
        ):
            continue
        satisfazem.append(configuracao)
        compativeis.add(calculo.canonica(configuracao))

    # Um elemento declarado precisa mudar o estereoisômero nesta configuração
    for indice, declaracao in pendentes:
        if indice not in bits:
            continue
        if all(
            calculo.canonica(c) == calculo.canonica(c ^ (1 << indice)) for c in satisfazem
        ):
            mensagens.append(
                (
                    "STEREO-001",
                    "erro",
                    declaracao,
                    f"{nome(declaracao)} não é estereogênico com as demais "
                    "configurações declaradas",
                )
            )
    return declarados, relativos, sorted(compativeis)


# ---------- saída ----------


def rotulo_elemento(elemento, por_id):
    if elemento.tipo == "centro":
        return por_id[elemento.atomos[0]].rotulo()
    if elemento.tipo == "atropo":
        return "-".join(por_id[x].rotulo() for x in elemento.atomos)
    cadeia = (elemento.atomos[0], *elemento.internos, elemento.atomos[1])
    return "=".join(por_id[x].rotulo() for x in cadeia)


def texto_chave(chave, por_id):
    if isinstance(chave, int):
        return por_id[chave].rotulo()
    return "par livre"


def texto_prioridades(niveis, por_id):
    partes = []
    for nivel in niveis:
        partes.append(" ~ ".join(texto_chave(k, por_id) for k in nivel))
    return " > ".join(partes)


def resumo_classes(resultado):
    if resultado.classes is None:
        return None
    total = len(resultado.classes)
    aquirais = sum(1 for c, e in resultado.classes.items() if c == e)
    pares = (total - aquirais) // 2
    partes = []
    if aquirais:
        partes.append(f"{aquirais} aquiral(is)")
    if pares:
        partes.append(f"{pares} par(es) de enantiômeros")
    return total, ", ".join(partes)


def formatar(modelo, dados_elementos, valencias):
    resultado, motivo, _ = analisar(modelo, dados_elementos, valencias)
    if resultado is None:
        return f"Estereoquímica: não avaliada ({motivo})"
    por_id = {a.id: a for a in modelo.atomos}
    elementos = resultado.elementos
    estereogenicos = [elementos[i] for i in resultado.estereogenicos]
    if not estereogenicos:
        return "Estereoquímica: nenhum elemento estereogênico"
    linhas = ["Estereoquímica"]
    secoes = (
        ("centro", "Centros estereogênicos"),
        ("dupla", "Ligações duplas estereogênicas"),
        ("eixo", "Eixos estereogênicos (alenos)"),
        ("atropo", "Eixos declarados (biarilas)"),
    )
    for tipo, titulo in secoes:
        do_tipo = [
            (i, elementos[i]) for i in resultado.estereogenicos if elementos[i].tipo == tipo
        ]
        if not do_tipo:
            continue
        linhas.append(f"  {titulo} ({len(do_tipo)})")
        for indice, elemento in do_tipo:
            if tipo == "centro":
                prioridades = texto_prioridades(elemento.prioridades[0], por_id)
            else:
                prioridades = "; ".join(
                    f"lado {por_id[p].rotulo()} {texto_prioridades(n, por_id)}"
                    for p, n in zip(elemento.atomos, elemento.prioridades)
                )
            nomes = "/".join(sorted(DESCRITORES[tipo_descritor(elemento)]))
            if elemento.pseudo == "anel":
                nomes = "cis/trans no anel"
            if indice in resultado.declarados:
                configuracao = f"configuração {resultado.declarados[indice]} declarada"
            else:
                configuracao = f"configuração {nomes} não especificada"
            extra = ""
            if elemento.pseudo == "ramos":
                extra = " (pseudoassimétrico)"
            elif elemento.pseudo == "anel":
                extra = " (ramos iguais pelo anel)"
            linhas.append(
                f"    {rotulo_elemento(elemento, por_id)}{extra}: prioridades CIP "
                f"{prioridades}; {configuracao}"
            )
    for i, j, descritor, _, _ in resultado.relativos:
        linhas.append(
            f"  Configuração relativa declarada: {rotulo_elemento(elementos[i], por_id)} e "
            f"{rotulo_elemento(elementos[j], por_id)} {descritor}"
        )

    resumo = resumo_classes(resultado)
    if resumo is None:
        linhas.append(
            f"  No máximo {2 ** len(estereogenicos)} estereoisômero(s); contagem exata "
            f"não calculada: {resultado.motivo_contagem}"
        )
    else:
        total, detalhe = resumo
        linhas.append(f"  Estereoisômeros desta constituição: {total} ({detalhe})")

    if resultado.compativeis is not None:
        linhas.extend(texto_declarado(resultado, por_id))
    return "\n".join(linhas)


def texto_declarado(resultado, por_id):
    compativeis = resultado.compativeis
    classes = resultado.classes
    linhas = []
    if not compativeis:
        return ["  As configurações declaradas são incompatíveis entre si"]
    if len(compativeis) == 1:
        canonica = compativeis[0]
        if classes[canonica] == canonica:
            # Meso: aquiral com centros quirais de verdade (não só centros
            # pseudoassimétricos ou de anel com ramos iguais)
            tem_centro = any(
                resultado.elementos[i].tipo == "centro"
                and resultado.elementos[i].pseudo is None
                for i in resultado.estereogenicos
            )
            linhas.append(
                "  Estereoisômero declarado: aquiral"
                + (" (forma meso)" if tem_centro else "")
            )
        else:
            linhas.append("  Estereoisômero declarado: quiral")
            espelhados = []
            for indice, descritor in sorted(resultado.declarados.items()):
                elemento = resultado.elementos[indice]
                espelhados.append(
                    f"{rotulo_elemento(elemento, por_id)} {ESPELHO.get(descritor, descritor)}"
                )
            if espelhados:
                linhas.append("  Enantiômero: " + ", ".join(espelhados))
    elif len(compativeis) == 2 and classes[compativeis[0]] == compativeis[1]:
        linhas.append(
            "  As declarações fixam só a configuração relativa: par de enantiômeros"
        )
    else:
        linhas.append(
            f"  Configuração parcial: {len(compativeis)} estereoisômeros compatíveis"
        )
    return linhas
