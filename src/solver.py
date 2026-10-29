"""Inferência limitada de ligações a partir de declarações de átomos."""

from dataclasses import dataclass, replace
from itertools import combinations, permutations, product

from ast_nos import (
    AnelDecl,
    AtomoDecl,
    LigacaoDecl,
    Operador,
    Referencia,
    TipoReferencia,
)


LIMITE_ATOMOS_SOLVER = 8
OPERADOR_POR_ORDEM = {
    1: Operador.SIMPLES,
    2: Operador.DUPLA,
    3: Operador.TRIPLA,
}


@dataclass
class MensagemSolver:
    id: str
    linha: int
    coluna: int
    mensagem: str

    def __str__(self):
        return (
            f"Erro de resolução [{self.id}] na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}"
        )


def valencias_candidatas(atomo, regras):
    if atomo.carga:
        tabela = regras["valencias_com_carga"].get(atomo.elemento, {})
        chave = f"{atomo.carga:+d}"
        return tabela.get(chave)
    return regras["valencias"].get(atomo.elemento)


def expandir_atomos(molecula):
    atomos = []
    for comando in molecula.comandos:
        if not isinstance(comando, AtomoDecl):
            continue
        for _ in range(comando.multiplicador):
            indice = len(atomos) + 1
            atomos.append(
                AtomoDecl(
                    multiplicador=1,
                    elemento=comando.elemento,
                    carga=comando.carga,
                    nome=f"r{indice}",
                    linha=comando.linha,
                    coluna=comando.coluna,
                )
            )
    return atomos


def conectado(quantidade, arestas):
    if quantidade < 2:
        return True
    adjacencias = {i: set() for i in range(quantidade)}
    for (a, b), ordem in arestas.items():
        if ordem:
            adjacencias[a].add(b)
            adjacencias[b].add(a)
    visitados = set()
    pilha = [0]
    while pilha:
        atual = pilha.pop()
        if atual in visitados:
            continue
        visitados.add(atual)
        pilha.extend(adjacencias[atual] - visitados)
    return len(visitados) == quantidade


def chave_canonica(arestas, atomos):
    grupos = {}
    for indice, atomo in enumerate(atomos):
        grupos.setdefault((atomo.elemento, atomo.carga), []).append(indice)

    melhor = None
    permutacoes = [
        list(permutations(indices))
        for _, indices in sorted(grupos.items())
    ]
    for partes in product(*permutacoes):
        ordem_indices = [indice for parte in partes for indice in parte]
        chave = tuple(
            arestas.get(tuple(sorted((ordem_indices[a], ordem_indices[b]))), 0)
            for a, b in combinations(range(len(atomos)), 2)
        )
        if melhor is None or chave < melhor:
            melhor = chave
    return melhor


def buscar_arestas(alvos, atomos, limite):
    quantidade = len(alvos)
    pares = list(combinations(range(quantidade), 2))
    restantes = list(alvos)
    solucoes = []
    chaves = set()

    def capacidade_futura(inicio, atomo):
        return sum(
            min(3, restantes[outro])
            for a, b in pares[inicio:]
            if atomo in (a, b)
            for outro in ((b if a == atomo else a),)
        )

    def visitar(indice, arestas):
        if len(solucoes) >= limite:
            return
        if indice == len(pares):
            if all(valor == 0 for valor in restantes) and conectado(
                quantidade, arestas
            ):
                solucao = dict(arestas)
                chave = chave_canonica(solucao, atomos)
                if chave not in chaves:
                    chaves.add(chave)
                    solucoes.append(solucao)
            return

        a, b = pares[indice]
        maximo = min(3, restantes[a], restantes[b])
        for ordem in range(maximo, -1, -1):
            restantes[a] -= ordem
            restantes[b] -= ordem
            if (
                restantes[a] <= capacidade_futura(indice + 1, a)
                and restantes[b] <= capacidade_futura(indice + 1, b)
            ):
                arestas[(a, b)] = ordem
                visitar(indice + 1, arestas)
                arestas.pop((a, b), None)
            restantes[a] += ordem
            restantes[b] += ordem

    visitar(0, {})
    return solucoes


def preparar(molecula, regras):
    for comando in molecula.comandos:
        if isinstance(comando, (LigacaoDecl, AnelDecl)):
            return None, None, [
                MensagemSolver(
                    "SOLVER-001",
                    comando.linha,
                    comando.coluna,
                    "--resolver aceita somente declarações de átomos",
                )
            ]

    atomos = expandir_atomos(molecula)
    if not atomos:
        return None, None, [
            MensagemSolver(
                "SOLVER-001",
                molecula.linha,
                molecula.coluna,
                "não há átomos para resolver",
            )
        ]
    if len(atomos) > LIMITE_ATOMOS_SOLVER:
        return None, None, [
            MensagemSolver(
                "SOLVER-001",
                molecula.linha,
                molecula.coluna,
                f"o solver aceita no máximo {LIMITE_ATOMOS_SOLVER} átomos; "
                "estruturas maiores ou ambíguas exigem ligações explícitas",
            )
        ]

    candidatos = []
    for atomo in atomos:
        aceitas = valencias_candidatas(atomo, regras)
        if not aceitas:
            return None, None, [
                MensagemSolver(
                    "SOLVER-002",
                    atomo.linha,
                    atomo.coluna,
                    f"não há valência confirmada para resolver "
                    f"{atomo.elemento} com carga {atomo.carga:+d}",
                )
            ]
        candidatos.append(aceitas)
    return atomos, candidatos, []


def buscar_solucoes(atomos, candidatos, limite):
    solucoes = []
    for alvos in product(*candidatos):
        restantes = limite - len(solucoes)
        solucoes.extend(buscar_arestas(alvos, atomos, restantes))
        if len(solucoes) >= limite:
            break
    return solucoes


def montar_molecula(molecula, atomos, solucao):
    ligacoes = []
    for (a, b), ordem in solucao.items():
        if not ordem:
            continue
        origem = atomos[a]
        destino = atomos[b]
        ligacoes.append(
            LigacaoDecl(
                origem=Referencia(
                    origem.nome,
                    TipoReferencia.NOME,
                    molecula.linha,
                    molecula.coluna,
                ),
                operador=OPERADOR_POR_ORDEM[ordem],
                destino=Referencia(
                    destino.nome,
                    TipoReferencia.NOME,
                    molecula.linha,
                    molecula.coluna,
                ),
                repeticoes=1,
                linha=molecula.linha,
                coluna=molecula.coluna,
            )
        )
    return replace(molecula, comandos=[*atomos, *ligacoes])


def enumerar(molecula, regras, limite=10):
    atomos, candidatos, mensagens = preparar(molecula, regras)
    if mensagens:
        return [], mensagens, False

    solucoes = buscar_solucoes(atomos, candidatos, limite + 1)
    if not solucoes:
        return [], [
            MensagemSolver(
                "SOLVER-003",
                molecula.linha,
                molecula.coluna,
                "nenhuma estrutura conectada satisfaz as valências conhecidas",
            )
        ], False

    truncado = len(solucoes) > limite
    estruturas = [
        montar_molecula(molecula, atomos, solucao)
        for solucao in solucoes[:limite]
    ]
    return estruturas, [], truncado


def resolver(molecula, regras):
    estruturas, mensagens, _ = enumerar(molecula, regras, limite=2)
    if mensagens:
        return None, mensagens
    if len(estruturas) > 1:
        return None, [
            MensagemSolver(
                "SOLVER-004",
                molecula.linha,
                molecula.coluna,
                "a fórmula admite múltiplas estruturas; declare as ligações",
            )
        ]
    return estruturas[0], []
