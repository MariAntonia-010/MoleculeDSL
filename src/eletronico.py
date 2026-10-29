from dataclasses import dataclass

from ast_nos import Operador


# Fase 7 do plano do solver: modelo eletrônico da estrutura de Lewis.
#
# Para cada átomo com elétrons de valência conhecidos:
#   elétrons não ligantes = elétrons de valência - carga formal - soma das ordens
# Os elétrons pi são os que excedem a ligação sigma em cada ligação
# múltipla. As formas de ressonância mantêm o esqueleto sigma, a carga
# total e a quantidade de elétrons, e trocam ordens de ligação e cargas
# formais dentro dos estados permitidos por regras/valencias.json.

LIMITE_FORMAS = 10


@dataclass
class EstadoAtomo:
    atomo: object
    soma_ordens: int
    eletrons_nao_ligantes: int | None
    ligacoes_pi: int

    @property
    def pares_livres(self):
        if self.eletrons_nao_ligantes is None:
            return None
        return self.eletrons_nao_ligantes // 2

    @property
    def desemparelhados(self):
        if self.eletrons_nao_ligantes is None:
            return None
        return self.eletrons_nao_ligantes % 2


@dataclass
class Forma:
    # ordens[(a, b)] com a < b e cargas[id]
    ordens: dict
    cargas: dict


def ordens_do_modelo(modelo, valencias):
    ordem = valencias["ordem_ligacao"]
    resultado = {}
    for lig in modelo.ligacoes:
        if lig.operador is Operador.METALICA:
            continue
        par = tuple(sorted((lig.origem, lig.destino)))
        resultado[par] = ordem[lig.operador.name]
    return resultado


def estados(modelo, dados_elementos, valencias):
    ordens = ordens_do_modelo(modelo, valencias)
    soma = {a.id: 0 for a in modelo.atomos}
    pi = {a.id: 0 for a in modelo.atomos}
    for (a, b), valor in ordens.items():
        soma[a] += valor
        soma[b] += valor
        pi[a] += valor - 1
        pi[b] += valor - 1

    resultado = []
    for atomo in modelo.atomos:
        valencia = dados_elementos.get(atomo.elemento, {}).get(
            "eletrons_valencia"
        )
        nao_ligantes = None
        if valencia is not None:
            nao_ligantes = valencia - atomo.carga - soma[atomo.id]
            if nao_ligantes < 0:
                nao_ligantes = None
        resultado.append(
            EstadoAtomo(atomo, soma[atomo.id], nao_ligantes, pi[atomo.id])
        )
    return resultado


def formatar_estados(modelo, dados_elementos, valencias):
    lista = estados(modelo, dados_elementos, valencias)
    linhas = ["Modelo eletrônico"]
    for estado in lista:
        if estado.eletrons_nao_ligantes is None:
            detalhe = "sem dados de elétrons de valência"
        else:
            detalhe = (
                f"pares livres={estado.pares_livres} "
                f"elétrons não ligantes={estado.eletrons_nao_ligantes}"
            )
            if estado.desemparelhados:
                detalhe += " desemparelhado=1"
        linhas.append(
            f"  {estado.atomo.rotulo()} carga={estado.atomo.carga:+d} "
            f"soma das ordens={estado.soma_ordens} "
            f"ligações pi={estado.ligacoes_pi} {detalhe}"
        )
    ordens = ordens_do_modelo(modelo, valencias)
    sigma = len(ordens)
    eletrons_pi = sum(2 * (valor - 1) for valor in ordens.values())
    linhas.append(
        f"  Totais: ligações sigma={sigma} elétrons pi={eletrons_pi} "
        f"carga formal={sum(a.carga for a in modelo.atomos):+d}"
    )
    return "\n".join(linhas)


def estados_permitidos(atomo, valencia_eletrons, valencias):
    # Pares (carga, soma das ordens) aceitos pelas regras, sempre com
    # elétrons não ligantes em pares
    permitidos = []
    for valor in valencias["valencias"].get(atomo.elemento, []):
        permitidos.append((0, valor))
    for carga, valores in valencias["valencias_com_carga"].get(
        atomo.elemento, {}
    ).items():
        for valor in valores:
            permitidos.append((int(carga), valor))
    return [
        (carga, valor)
        for carga, valor in permitidos
        if valencia_eletrons - carga - valor >= 0
        and (valencia_eletrons - carga - valor) % 2 == 0
    ]


def formas_de_ressonancia(modelo, dados_elementos, valencias, limite=LIMITE_FORMAS):
    """Devolve (formas, motivo, truncado).

    Quando a molécula fica fora do modelo, formas é None e motivo diz por
    quê. A forma declarada é sempre a primeira da lista.
    """
    if any(
        lig.operador in (Operador.METALICA, Operador.COORDENADA)
        for lig in modelo.ligacoes
    ):
        return None, "ligações coordenadas ou metálicas ficam fora do modelo", False

    permitidos = {}
    for atomo in modelo.atomos:
        valencia = dados_elementos.get(atomo.elemento, {}).get(
            "eletrons_valencia"
        )
        if valencia is None:
            return None, f"faltam elétrons de valência de {atomo.elemento}", False
        opcoes = estados_permitidos(atomo, valencia, valencias)
        if not opcoes:
            return None, f"não há estados de valência para {atomo.rotulo()}", False
        permitidos[atomo.id] = opcoes

    declarada = ordens_do_modelo(modelo, valencias)
    for estado in estados(modelo, dados_elementos, valencias):
        if estado.desemparelhados:
            return None, "radicais ficam fora do modelo de ressonância", False

    carga_total = sum(a.carga for a in modelo.atomos)
    pares = sorted(declarada)
    ultimo_par = {}
    for indice, (a, b) in enumerate(pares):
        ultimo_par[a] = indice
        ultimo_par[b] = indice
    soma = {a.id: 0 for a in modelo.atomos}
    maximo = {
        atomo_id: max(valor for _, valor in opcoes)
        for atomo_id, opcoes in permitidos.items()
    }
    ordens = {}
    encontradas = []
    truncado = False

    def cargas_possiveis():
        # Cada átomo pode ter mais de uma carga com a mesma soma de ordens
        listas = []
        for atomo in modelo.atomos:
            listas.append(
                [
                    carga
                    for carga, valor in permitidos[atomo.id]
                    if valor == soma[atomo.id]
                ]
            )
        return listas

    def fechar():
        nonlocal truncado
        ids = [a.id for a in modelo.atomos]
        listas = cargas_possiveis()

        def escolher(indice, atuais, total):
            nonlocal truncado
            if truncado:
                return
            if indice == len(ids):
                if total == carga_total:
                    if len(encontradas) >= limite:
                        truncado = True
                        return
                    encontradas.append(Forma(dict(ordens), dict(atuais)))
                return
            for carga in listas[indice]:
                atuais[ids[indice]] = carga
                escolher(indice + 1, atuais, total + carga)
            atuais.pop(ids[indice], None)

        escolher(0, {}, 0)

    def visitar(indice):
        if truncado:
            return
        if indice == len(pares):
            fechar()
            return
        a, b = pares[indice]
        for valor in (1, 2, 3):
            if soma[a] + valor > maximo[a] or soma[b] + valor > maximo[b]:
                break
            soma[a] += valor
            soma[b] += valor
            ordens[(a, b)] = valor
            # Um átomo cuja última ligação já foi decidida precisa ter uma
            # soma aceita pelas regras
            completo = all(
                ultimo_par[x] != indice
                or any(v == soma[x] for _, v in permitidos[x])
                for x in (a, b)
            )
            if completo:
                visitar(indice + 1)
            soma[a] -= valor
            soma[b] -= valor
            del ordens[(a, b)]

    visitar(0)

    # A forma declarada vai primeiro; as demais, por quantidade de átomos
    # com carga formal (critério exibido na saída, não uma estabilidade)
    cargas_declaradas = {a.id: a.carga for a in modelo.atomos}
    encontradas.sort(
        key=lambda forma: (
            not (
                forma.ordens == declarada
                and forma.cargas == cargas_declaradas
            ),
            atomos_com_carga(forma),
        )
    )
    return encontradas, None, truncado


def atomos_com_carga(forma):
    return sum(1 for carga in forma.cargas.values() if carga)


SIMBOLO = {1: "-", 2: "=", 3: "#"}


def formatar_ressonancia(modelo, dados_elementos, valencias):
    formas, motivo, truncado = formas_de_ressonancia(
        modelo, dados_elementos, valencias
    )
    if formas is None:
        return f"Ressonância: não avaliada ({motivo})"
    por_id = {a.id: a for a in modelo.atomos}
    declarada = ordens_do_modelo(modelo, valencias)
    linhas = [f"Ressonância: {len(formas)} forma(s) com o mesmo esqueleto sigma"]
    for indice, forma in enumerate(formas, start=1):
        mudancas = [
            f"{por_id[a].rotulo()}{SIMBOLO[valor]}{por_id[b].rotulo()}"
            for (a, b), valor in sorted(forma.ordens.items())
            if valor != 1 or declarada[(a, b)] != 1
        ]
        cargas = [
            f"{por_id[i].rotulo()}({carga:+d})"
            for i, carga in sorted(forma.cargas.items())
            if carga
        ]
        texto = ", ".join(mudancas) if mudancas else "só ligações simples"
        if cargas:
            texto += "; cargas " + ", ".join(cargas)
        linhas.append(
            f"  Forma {indice} ({atomos_com_carga(forma)} átomo(s) com carga): "
            f"{texto}"
        )
    if truncado:
        linhas.append(f"  Mais formas existem; exibidas as {len(formas)} primeiras")
    return "\n".join(linhas)
