from dataclasses import replace

from ast_nos import Operador
import eletronico
from modelo import Ligacao, Modelo
from solver.canonical import canonical_heavy_key


# Tautomeria prototrópica sobre o modelo eletrônico (plano de limites, L6).
#
# Um H sai do átomo doador e deixa a base conjugada com carga -1 nele. As
# formas de ressonância dessa base mostram onde o par pode ficar; o H
# volta em cada átomo que fica com carga -1 numa forma. Isso cobre os
# deslocamentos 1,3 (ceto-enol, imina-enamina, amida-ácido imídico) e 1,5
# (através de ligações conjugadas). O H sempre sai de um heteroátomo ou
# chega a um. A busca repete o passo sobre cada
# tautômero novo, para chegar aos que movem mais de um H.
#
# Estruturas com mais átomos carregados que a declarada não entram: a
# tautomeria troca a posição do H sem criar separação de cargas.

LIMITE_TAUTOMEROS = 20
CARBONO_OU_H = {"C", "H"}
LIMITE_FORMAS_BASE = 50

ORDEM_OPERADOR = {1: Operador.SIMPLES, 2: Operador.DUPLA, 3: Operador.TRIPLA}


class Pesado:
    # Interface mínima esperada por canonical_heavy_key
    def __init__(self, elemento, carga):
        self.element = elemento
        self.charge = carga


def chave(modelo, valencias):
    # Chave canônica do grafo pesado com ordens, cargas e H por átomo
    por_id = {a.id: a for a in modelo.atomos}
    ordens = eletronico.ordens_do_modelo(modelo, valencias)
    pesados = [
        a
        for a in modelo.atomos
        if a.elemento != "H" or not hidrogenio_terminal(a.id, ordens)
    ]
    indice = {a.id: i for i, a in enumerate(pesados)}
    hidrogenios = [0] * len(pesados)
    arestas = {}
    for (a, b), valor in ordens.items():
        if a in indice and b in indice:
            arestas[tuple(sorted((indice[a], indice[b])))] = valor
        else:
            pesado = a if a in indice else b
            hidrogenios[indice[pesado]] += 1
    atomos = [Pesado(por_id[a.id].elemento, por_id[a.id].carga) for a in pesados]
    return canonical_heavy_key(arestas, atomos, hidrogenios)


def hidrogenio_terminal(atomo_id, ordens):
    return sum(1 for par in ordens if atomo_id in par) == 1


def com_forma(modelo, forma):
    # Novo modelo com as ordens e cargas de uma forma de ressonância
    atomos = [replace(a, carga=forma.cargas[a.id]) for a in modelo.atomos]
    ligacoes = []
    for lig in modelo.ligacoes:
        par = tuple(sorted((lig.origem, lig.destino)))
        if lig.operador in (Operador.SIMPLES, Operador.DUPLA, Operador.TRIPLA):
            lig = replace(lig, operador=ORDEM_OPERADOR[forma.ordens[par]])
        ligacoes.append(lig)
    return replace(modelo, atomos=atomos, ligacoes=ligacoes)


def passos(modelo, dados_elementos, valencias):
    # Tautômeros a um deslocamento de H do modelo dado
    por_id = {a.id: a for a in modelo.atomos}
    cargas_declaradas = sum(1 for a in modelo.atomos if a.carga)
    for lig in modelo.ligacoes:
        if lig.operador is not Operador.SIMPLES:
            continue
        for h, doador in ((lig.origem, lig.destino), (lig.destino, lig.origem)):
            if por_id[h].elemento != "H" or por_id[doador].elemento == "H":
                continue
            # Base conjugada: sem a ligação doador-H e com carga -1 no doador
            base = replace(
                modelo,
                atomos=[
                    replace(a, carga=a.carga - 1) if a.id == doador else a
                    for a in modelo.atomos
                    if a.id != h
                ],
                ligacoes=[x for x in modelo.ligacoes if x is not lig],
            )
            formas, _, _ = eletronico.formas_de_ressonancia(
                base, dados_elementos, valencias, LIMITE_FORMAS_BASE
            )
            for forma in formas:
                for receptor, carga in forma.cargas.items():
                    if carga != -1 or receptor == doador:
                        continue
                    # Tautomeria prototrópica: o H sai de um heteroátomo ou
                    # chega a um. Saltos de carbono para carbono são
                    # deslocamentos sigmatrópicos, não tautomeria.
                    if CARBONO_OU_H >= {
                        por_id[doador].elemento,
                        por_id[receptor].elemento,
                    }:
                        continue
                    nova = com_forma(base, forma)
                    atomos = [
                        replace(a, carga=a.carga + 1) if a.id == receptor else a
                        for a in nova.atomos
                    ]
                    atomos.append(por_id[h])
                    atomos.sort(key=lambda a: a.id)
                    ligacoes = nova.ligacoes + [
                        Ligacao(receptor, h, Operador.SIMPLES, lig.linha, lig.coluna)
                    ]
                    candidato = replace(nova, atomos=atomos, ligacoes=ligacoes)
                    if sum(1 for a in atomos if a.carga) > cargas_declaradas:
                        continue
                    if not estados_validos(candidato, dados_elementos, valencias):
                        continue
                    yield candidato


def estados_validos(modelo, dados_elementos, valencias):
    lista = eletronico.estados(modelo, dados_elementos, valencias)
    radicais = any(estado.desemparelhados for estado in lista)
    for estado in lista:
        valencia = dados_elementos.get(estado.atomo.elemento, {}).get(
            "eletrons_valencia"
        )
        if valencia is None:
            continue
        permitidos = eletronico.estados_permitidos(
            estado.atomo, valencia, valencias, radicais
        )
        if (estado.atomo.carga, estado.soma_ordens) not in permitidos:
            return False
    return True


def tautomeros(modelo, dados_elementos, valencias, limite=LIMITE_TAUTOMEROS):
    """Devolve (lista de modelos, truncado). O primeiro é o declarado.

    Ligações coordenadas e metálicas ficam fixas, como na ressonância.
    """
    vistos = {chave(modelo, valencias)}
    encontrados = [modelo]
    fila = [modelo]
    truncado = False
    while fila and not truncado:
        atual = fila.pop(0)
        for candidato in passos(atual, dados_elementos, valencias):
            identidade = chave(candidato, valencias)
            if identidade in vistos:
                continue
            if len(encontrados) >= limite:
                truncado = True
                break
            vistos.add(identidade)
            encontrados.append(candidato)
            fila.append(candidato)
    return encontrados, truncado


def descrever(original, tautomero, valencias):
    por_id = {a.id: a for a in tautomero.atomos}
    ordens_antes = eletronico.ordens_do_modelo(original, valencias)
    ordens_depois = eletronico.ordens_do_modelo(tautomero, valencias)
    simbolo = eletronico.SIMBOLO
    movidos = []
    for par in sorted(set(ordens_depois) - set(ordens_antes)):
        a, b = par
        h, receptor = (a, b) if por_id[a].elemento == "H" else (b, a)
        movidos.append(f"{por_id[h].rotulo()} em {por_id[receptor].rotulo()}")
    mudancas = [
        f"{por_id[a].rotulo()}{simbolo[valor]}{por_id[b].rotulo()}"
        for (a, b), valor in sorted(ordens_depois.items())
        if (a, b) in ordens_antes and ordens_antes[(a, b)] != valor
    ]
    cargas = [
        f"{a.rotulo()}({a.carga:+d})" for a in tautomero.atomos if a.carga
    ]
    texto = "; ".join(movidos)
    if mudancas:
        texto += "; ligações " + ", ".join(mudancas)
    if cargas:
        texto += "; cargas " + ", ".join(cargas)
    return texto


def formatar(modelo, dados_elementos, valencias):
    lista, truncado = tautomeros(modelo, dados_elementos, valencias)
    if len(lista) == 1:
        return "Tautômeros: nenhum deslocamento de H gera outra estrutura"
    linhas = [f"Tautômeros: {len(lista)} estrutura(s), a declarada primeiro"]
    linhas.append("  Tautômero 1: forma declarada")
    for indice, tautomero in enumerate(lista[1:], start=2):
        linhas.append(
            f"  Tautômero {indice}: {descrever(modelo, tautomero, valencias)}"
        )
    if truncado:
        linhas.append(f"  Mais tautômeros existem; exibidos os {len(lista)} primeiros")
    return "\n".join(linhas)
