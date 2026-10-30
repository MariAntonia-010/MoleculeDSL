from collections import deque

import eletronico


# Aromaticidade pela regra de Hückel (plano de limites, L7).
#
# Os ciclos vêm de uma base de ciclos mínimos do grafo (sem as arestas ~).
# Cada átomo do ciclo contribui com elétrons pi pela forma declarada:
# - 1 se tem ligação dupla ou tripla com outro átomo do ciclo;
# - 0 se a ligação dupla sai do ciclo para um átomo mais eletronegativo
#   (C=O exocíclico), ou se não tem par livre e tem orbital vazio
#   (carbocátion, boro trivalente);
# - 2 se não tem ligação múltipla e tem par livre (N de pirrol, O de furano);
# - sem orbital p disponível nos outros casos (o ciclo não é conjugado).
# Com 4n+2 elétrons o ciclo é aromático; com 4n, antiaromático. Quando um
# átomo usa a ligação dupla com o anel vizinho (naftaleno), o sistema
# fundido inteiro é avaliado. A regra supõe ciclos planos: acima de oito
# átomos a saída lembra essa hipótese.

TAMANHO_PLANO = 8
ELETRONEGATIVOS = {"N", "O", "S", "F", "Cl", "Br", "I"}


def grafo(modelo, valencias):
    ordens = eletronico.ordens_do_modelo(modelo, valencias)
    vizinhos = {a.id: {} for a in modelo.atomos}
    for (a, b), ordem in ordens.items():
        vizinhos[a][b] = ordem
        vizinhos[b][a] = ordem
    return vizinhos


def menor_ciclo(vizinhos, a, b):
    # Menor caminho de a até b sem usar a aresta a-b, fechado num ciclo
    anterior = {a: None}
    fila = deque([a])
    while fila:
        atual = fila.popleft()
        for vizinho in vizinhos[atual]:
            if {atual, vizinho} == {a, b} or vizinho in anterior:
                continue
            anterior[vizinho] = atual
            if vizinho == b:
                caminho = [b]
                while anterior[caminho[-1]] is not None:
                    caminho.append(anterior[caminho[-1]])
                return caminho
            fila.append(vizinho)
    return None


def ordenar_ciclo(ciclo):
    # Começa no menor id e segue para o vizinho de menor id
    inicio = ciclo.index(min(ciclo))
    girado = ciclo[inicio:] + ciclo[:inicio]
    if len(girado) > 2 and girado[-1] < girado[1]:
        girado = [girado[0]] + girado[:0:-1]
    return girado


def arestas_do_ciclo(ciclo):
    return frozenset(
        frozenset((ciclo[i], ciclo[(i + 1) % len(ciclo)]))
        for i in range(len(ciclo))
    )


def base_de_ciclos(vizinhos):
    # Candidatos: o menor ciclo por aresta. A base pega os menores que
    # são independentes sobre GF(2), até completar E - V + componentes.
    arestas = {frozenset((a, b)) for a in vizinhos for b in vizinhos[a]}
    candidatos = {}
    for aresta in arestas:
        a, b = tuple(aresta)
        ciclo = menor_ciclo(vizinhos, a, b)
        if ciclo is not None:
            candidatos.setdefault(arestas_do_ciclo(ciclo), ciclo)
    indice = {aresta: i for i, aresta in enumerate(sorted(arestas, key=sorted))}
    base = []
    pivos = {}
    for chave, ciclo in sorted(candidatos.items(), key=lambda item: len(item[1])):
        vetor = 0
        for aresta in chave:
            vetor |= 1 << indice[aresta]
        while vetor:
            alto = vetor.bit_length() - 1
            if alto not in pivos:
                pivos[alto] = vetor
                base.append(ciclo)
                break
            vetor ^= pivos[alto]
    return base


def contribuicao(atomo_id, sistema, vizinhos, por_id, estados):
    # Elétrons pi do átomo no sistema, None se ele não tem orbital p, ou
    # "fora" se a ligação dupla dele vai para um carbono fora do sistema
    multiplas = {v: o for v, o in vizinhos[atomo_id].items() if o >= 2}
    if any(v in sistema for v in multiplas):
        return 1
    if multiplas:
        if all(por_id[v].elemento in ELETRONEGATIVOS for v in multiplas):
            return 0
        return "fora"
    estado = estados[atomo_id]
    if estado.pares_livres:
        return 2
    if estado.eletrons_nao_ligantes == 0 and (
        por_id[atomo_id].carga > 0 or por_id[atomo_id].elemento == "B"
    ):
        return 0
    return None


def avaliar(sistema, vizinhos, por_id, estados):
    total = 0
    for atomo_id in sistema:
        valor = contribuicao(atomo_id, sistema, vizinhos, por_id, estados)
        if valor is None:
            return None, por_id[atomo_id]
        if valor == "fora":
            return "fora", por_id[atomo_id]
        total += valor
    return total, None


def classificar(eletrons):
    if eletrons % 4 == 2:
        return "aromático"
    if eletrons % 4 == 0:
        return "antiaromático"
    return "não aromático"


def analisar(modelo, dados_elementos, valencias):
    vizinhos = grafo(modelo, valencias)
    por_id = {a.id: a for a in modelo.atomos}
    estados = {
        e.atomo.id: e for e in eletronico.estados(modelo, dados_elementos, valencias)
    }
    ciclos = base_de_ciclos(vizinhos)
    resultados = []
    pendentes = []
    for ciclo in ciclos:
        eletrons, atomo = avaliar(set(ciclo), vizinhos, por_id, estados)
        if eletrons == "fora":
            pendentes.append(ciclo)
            continue
        resultados.append((ordenar_ciclo(ciclo), eletrons, atomo))

    # Sistemas fundidos: ciclos pendentes que dividem aresta com outros
    # ciclos são avaliados juntos com todos os ciclos ligados a eles
    restantes = list(pendentes)
    while restantes:
        grupo = [restantes.pop()]
        atomos = set(grupo[0])
        mudou = True
        while mudou:
            mudou = False
            for ciclo in ciclos:
                if ciclo in grupo:
                    continue
                if len(atomos & set(ciclo)) >= 2:
                    grupo.append(ciclo)
                    atomos |= set(ciclo)
                    if ciclo in restantes:
                        restantes.remove(ciclo)
                    mudou = True
        eletrons, atomo = avaliar(atomos, vizinhos, por_id, estados)
        if eletrons == "fora":
            eletrons = None
        resultados.append((sorted(atomos), eletrons, atomo))
    return resultados


def formatar(modelo, dados_elementos, valencias):
    resultados = analisar(modelo, dados_elementos, valencias)
    if not resultados:
        return "Aromaticidade: nenhum ciclo"
    por_id = {a.id: a for a in modelo.atomos}
    linhas = [f"Aromaticidade ({len(resultados)} sistema(s) cíclico(s))"]
    for atomos, eletrons, atomo in resultados:
        nomes = " ".join(por_id[i].rotulo() for i in atomos)
        if eletrons is None:
            texto = f"não aromático: {atomo.rotulo()} não tem orbital p livre"
        else:
            texto = f"{eletrons} elétron(s) pi, {classificar(eletrons)} (Hückel)"
            if len(atomos) > TAMANHO_PLANO and eletrons % 2 == 0:
                texto += "; supõe o ciclo plano"
        linhas.append(f"  [{nomes}] {texto}")
    return "\n".join(linhas)
