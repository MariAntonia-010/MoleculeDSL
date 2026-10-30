from dataclasses import dataclass

from ast_nos import Operador


# Fase 7 do plano do solver: modelo eletrônico da estrutura de Lewis.
#
# Para cada átomo com elétrons de valência conhecidos:
#   elétrons não ligantes = elétrons de valência - carga formal - soma das ordens
# Os elétrons pi são os que excedem a ligação sigma em cada ligação
# múltipla. As formas de ressonância mantêm o esqueleto sigma, a carga
# total e a quantidade de elétrons, e trocam ordens de ligação e cargas
# formais dentro dos estados permitidos por regras/valencias.json. Radicais
# deslocam o elétron desemparelhado; ligações coordenadas ficam fixas.

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


def estados_permitidos(atomo, valencia_eletrons, valencias, radicais=False):
    # Pares (carga, soma das ordens) aceitos pelas regras. Sem radicais,
    # os elétrons não ligantes ficam sempre em pares; com radicais, cada
    # estado fechado também vale com uma ligação a menos e um elétron
    # desemparelhado.
    permitidos = []
    for valor in valencias["valencias"].get(atomo.elemento, []):
        permitidos.append((0, valor))
    for carga, valores in valencias["valencias_com_carga"].get(
        atomo.elemento, {}
    ).items():
        for valor in valores:
            permitidos.append((int(carga), valor))
    fechados = [
        (carga, valor)
        for carga, valor in permitidos
        if valencia_eletrons - carga - valor >= 0
        and (valencia_eletrons - carga - valor) % 2 == 0
    ]
    if not radicais:
        return fechados
    abertos = [(carga, valor - 1) for carga, valor in fechados if valor >= 1]
    return sorted(set(fechados + abertos))


def formas_de_ressonancia(modelo, dados_elementos, valencias, limite=LIMITE_FORMAS):
    """Devolve (formas, observacoes, truncado).

    As ligações simples, duplas e triplas trocam de ordem. As coordenadas
    ficam fixas, e as metálicas ficam fora (o motivo ~ não é estrutura de
    Lewis). Cada átomo aceita os estados das regras e o próprio estado
    declarado; um átomo sem elétrons de valência conhecidos fica no estado
    declarado. Com radicais, o total de elétrons desemparelhados é o da
    forma declarada. A forma declarada é sempre a primeira da lista.
    """
    observacoes = []
    if any(lig.operador is Operador.METALICA for lig in modelo.ligacoes):
        observacoes.append(
            "arestas ~ ficam fora: o motivo do sólido metálico não tem "
            "estrutura de Lewis"
        )
    if any(lig.operador is Operador.COORDENADA for lig in modelo.ligacoes):
        observacoes.append("ligações coordenadas ficam fixas")

    declarada = ordens_do_modelo(modelo, valencias)
    variaveis = set()
    for lig in modelo.ligacoes:
        if lig.operador in (Operador.SIMPLES, Operador.DUPLA, Operador.TRIPLA):
            variaveis.add(tuple(sorted((lig.origem, lig.destino))))
    fixas = {par: valor for par, valor in declarada.items() if par not in variaveis}

    # Átomos ligados por ~ ficam no estado declarado e fora da contagem
    # de elétrons desemparelhados: seus elétrons são do mar metálico
    metalicos = {
        x
        for lig in modelo.ligacoes
        if lig.operador is Operador.METALICA
        for x in (lig.origem, lig.destino)
    }
    lista_estados = estados(modelo, dados_elementos, valencias)
    desemparelhados_declarados = sum(
        estado.desemparelhados or 0
        for estado in lista_estados
        if estado.atomo.id not in metalicos
    )
    radicais = desemparelhados_declarados > 0
    if radicais:
        observacoes.append(
            f"radical: as formas mantêm {desemparelhados_declarados} "
            "elétron(s) desemparelhado(s)"
        )

    eletrons = {}
    permitidos = {}
    for estado in lista_estados:
        atomo = estado.atomo
        declarado = (atomo.carga, estado.soma_ordens)
        valencia = dados_elementos.get(atomo.elemento, {}).get(
            "eletrons_valencia"
        )
        if atomo.id in metalicos:
            valencia = None
        eletrons[atomo.id] = valencia
        if valencia is None or estado.eletrons_nao_ligantes is None:
            permitidos[atomo.id] = [declarado]
            continue
        opcoes = estados_permitidos(atomo, valencia, valencias, radicais)
        if declarado not in opcoes:
            opcoes.append(declarado)
        permitidos[atomo.id] = opcoes

    carga_total = sum(a.carga for a in modelo.atomos)
    pares = sorted(variaveis)
    ultimo_par = {}
    for indice, (a, b) in enumerate(pares):
        ultimo_par[a] = indice
        ultimo_par[b] = indice
    soma = {a.id: 0 for a in modelo.atomos}
    for (a, b), valor in fixas.items():
        soma[a] += valor
        soma[b] += valor
    maximo = {
        atomo_id: max(valor for _, valor in opcoes)
        for atomo_id, opcoes in permitidos.items()
    }
    ordens = dict(fixas)
    encontradas = []
    truncado = False
    # Uma forma com mais octetos incompletos que a declarada (C+ ao lado de
    # C- no eteno ou no benzeno) é contribuinte menor e fica de fora já na
    # busca, sem gastar o limite; o C+ do cátion alila, que está na forma
    # declarada, continua
    limite_incompletos = octetos_incompletos(
        modelo, eletrons, declarada, {a.id: a.carga for a in modelo.atomos}
    )
    menores = 0

    def nao_ligantes(atomo_id, carga):
        if eletrons[atomo_id] is None:
            return 0
        return eletrons[atomo_id] - carga - soma[atomo_id]

    def fechar():
        nonlocal truncado
        ids = [a.id for a in modelo.atomos]
        listas = [
            [carga for carga, valor in permitidos[i] if valor == soma[i]]
            for i in ids
        ]

        def escolher(indice, atuais, total, abertos):
            nonlocal truncado, menores
            if truncado:
                return
            if indice == len(ids):
                if total == carga_total and abertos == desemparelhados_declarados:
                    if octetos_incompletos(modelo, eletrons, ordens, atuais) > limite_incompletos:
                        menores += 1
                        return
                    if len(encontradas) >= limite:
                        truncado = True
                        return
                    encontradas.append(Forma(dict(ordens), dict(atuais)))
                return
            for carga in listas[indice]:
                atuais[ids[indice]] = carga
                escolher(
                    indice + 1,
                    atuais,
                    total + carga,
                    abertos + nao_ligantes(ids[indice], carga) % 2,
                )
            atuais.pop(ids[indice], None)

        escolher(0, {}, 0, 0)

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

    # Átomos sem ligações variáveis precisam estar num estado aceito
    if all(
        x in ultimo_par or any(v == soma[x] for _, v in permitidos[x])
        for x in soma
    ):
        visitar(0)

    if menores:
        observacoes.append(
            f"{menores} forma(s) com mais octetos incompletos que a declarada "
            "ficam de fora (contribuintes menores)"
        )

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
    return encontradas, observacoes, truncado


SEGUNDO_PERIODO = {"B", "C", "N", "O", "F"}


def octetos_incompletos(modelo, eletrons, ordens, cargas):
    # Átomos do segundo período com menos de 8 elétrons em volta:
    # elétrons de valência − carga + soma das ordens (cada ligação traz
    # um elétron do vizinho)
    soma = {a.id: 0 for a in modelo.atomos}
    for (a, b), valor in ordens.items():
        soma[a] += valor
        soma[b] += valor
    return sum(
        1
        for atomo in modelo.atomos
        if atomo.elemento in SEGUNDO_PERIODO
        and eletrons.get(atomo.id) is not None
        and eletrons[atomo.id] - cargas[atomo.id] + soma[atomo.id] < 8
    )


def atomos_com_carga(forma):
    return sum(1 for carga in forma.cargas.values() if carga)


SIMBOLO = {1: "-", 2: "=", 3: "#"}


def formatar_ressonancia(modelo, dados_elementos, valencias):
    formas, observacoes, truncado = formas_de_ressonancia(
        modelo, dados_elementos, valencias
    )
    por_id = {a.id: a for a in modelo.atomos}
    declarada = ordens_do_modelo(modelo, valencias)
    linhas = [f"Ressonância: {len(formas)} forma(s) com o mesmo esqueleto sigma"]
    linhas += [f"  Observação: {texto}" for texto in observacoes]
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
