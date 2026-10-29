from collections import deque

from ast_nos import Operador
import eletronico


# Fase 8 do plano do solver: elementos estereogênicos sobre a constituição.
#
# A linguagem não tem sintaxe para configuração, então todo elemento
# encontrado aparece como "não especificado". O módulo identifica:
# - centros tetraédricos: quatro vizinhos por ligação simples, nenhum par
#   livre e quatro substituintes diferentes;
# - ligações duplas E/Z: cada ponta com dois substituintes diferentes, ou
#   com um substituinte e um par livre (C=N), fora de anéis com menos de
#   oito átomos e sem ligações cumuladas.
# Substituintes são comparados pela regra 1a de Cahn-Ingold-Prelog
# (número atômico, esfera a esfera, com átomos duplicados para ligações
# múltiplas e fechamentos de anel). As regras 2 a 5 não entram, porque
# exigiriam isótopos e descritores que a linguagem não representa.

TAMANHO_MINIMO_ANEL_E_Z = 8


def grafo(modelo, valencias):
    ordens = eletronico.ordens_do_modelo(modelo, valencias)
    vizinhos = {a.id: [] for a in modelo.atomos}
    for (a, b), ordem in ordens.items():
        vizinhos[a].append((b, ordem))
        vizinhos[b].append((a, ordem))
    return vizinhos


class Arvore:
    """Dígrafo hierárquico de CIP a partir de uma ligação."""

    def __init__(self, vizinhos, numero_atomico):
        self.vizinhos = vizinhos
        self.z = numero_atomico

    def esferas(self, atomo, pai, ordem_pai, caminho):
        # Devolve as esferas do ramo como tuplas de números atômicos, cada
        # uma em ordem decrescente de prioridade
        filhos = []
        for vizinho, ordem in self.vizinhos[atomo]:
            if vizinho == pai:
                continue
            if vizinho in caminho:
                # Fechamento de anel: átomo duplicado, sem filhos
                filhos.append([(self.z[vizinho],)])
            else:
                filhos.append(
                    self.esferas(vizinho, atomo, ordem, caminho | {vizinho})
                )
            # Ligação múltipla: duplicatas do vizinho
            for _ in range(ordem - 1):
                filhos.append([(self.z[vizinho],)])
        if pai is not None:
            for _ in range(ordem_pai - 1):
                filhos.append([(self.z[pai],)])

        filhos.sort(key=chave_esferas, reverse=True)
        resultado = [(self.z[atomo],)]
        profundidade = max((len(f) for f in filhos), default=0)
        for nivel in range(profundidade):
            camada = []
            for filho in filhos:
                if nivel < len(filho):
                    camada.extend(filho[nivel])
            resultado.append(tuple(camada))
        return resultado

    def ramo(self, centro, inicio, ordem):
        return self.esferas(inicio, centro, ordem, {centro, inicio})


def chave_esferas(esferas):
    # Esferas menores são completadas com átomos fantasmas (número 0)
    return tuple(tuple(camada) + (0,) * (64 - len(camada)) for camada in esferas)


def tamanho_menor_anel(vizinhos, a, b):
    # Menor ciclo que contém a ligação a-b, ou None se ela não está em anel
    distancia = {a: 0}
    fila = deque([a])
    while fila:
        atual = fila.popleft()
        for vizinho, _ in vizinhos[atual]:
            if (atual, vizinho) in ((a, b), (b, a)) or vizinho in distancia:
                continue
            distancia[vizinho] = distancia[atual] + 1
            if vizinho == b:
                return distancia[vizinho] + 1
            fila.append(vizinho)
    return None


def analisar(modelo, dados_elementos, valencias):
    if any(lig.operador is Operador.METALICA for lig in modelo.ligacoes):
        return None, "ligações metálicas ficam fora da análise"
    vizinhos = grafo(modelo, valencias)
    z = {}
    for atomo in modelo.atomos:
        numero = dados_elementos.get(atomo.elemento, {}).get("numero_atomico")
        if numero is None:
            return None, f"falta o número atômico de {atomo.elemento}"
        z[atomo.id] = numero
    arvore = Arvore(vizinhos, z)
    pares_livres = {
        estado.atomo.id: estado.pares_livres
        for estado in eletronico.estados(modelo, dados_elementos, valencias)
    }

    def ordenar(centro, ligados):
        ramos = [
            (chave_esferas(arvore.ramo(centro, vizinho, ordem)), vizinho)
            for vizinho, ordem in ligados
        ]
        ramos.sort(reverse=True)
        distintos = len({chave for chave, _ in ramos}) == len(ramos)
        return [vizinho for _, vizinho in ramos], distintos

    centros = []
    for atomo in modelo.atomos:
        ligados = vizinhos[atomo.id]
        if (
            len(ligados) == 4
            and all(ordem == 1 for _, ordem in ligados)
            and pares_livres[atomo.id] == 0
        ):
            ordem_cip, distintos = ordenar(atomo.id, ligados)
            if distintos:
                centros.append((atomo.id, ordem_cip))

    duplas = []
    for (a, b), ordem in sorted(eletronico.ordens_do_modelo(modelo, valencias).items()):
        if ordem != 2:
            continue
        anel = tamanho_menor_anel(vizinhos, a, b)
        if anel is not None and anel < TAMANHO_MINIMO_ANEL_E_Z:
            continue
        lados = []
        for ponta, outra in ((a, b), (b, a)):
            outros = [(v, o) for v, o in vizinhos[ponta] if v != outra]
            if any(o > 1 for _, o in outros):
                break
            if len(outros) == 2:
                ordem_cip, distintos = ordenar(ponta, outros)
                if not distintos:
                    break
                lados.append((ponta, ordem_cip))
            elif len(outros) == 1 and (pares_livres[ponta] or 0) >= 1:
                lados.append((ponta, [outros[0][0]]))
            else:
                break
        if len(lados) == 2:
            duplas.append(lados)
    return (centros, duplas), None


def formatar(modelo, dados_elementos, valencias):
    resultado, motivo = analisar(modelo, dados_elementos, valencias)
    if resultado is None:
        return f"Estereoquímica: não avaliada ({motivo})"
    centros, duplas = resultado
    por_id = {a.id: a for a in modelo.atomos}

    def lista(ids):
        return " > ".join(por_id[i].rotulo() for i in ids)

    if not centros and not duplas:
        return "Estereoquímica: nenhum elemento estereogênico"
    linhas = ["Estereoquímica"]
    if centros:
        linhas.append(f"  Centros estereogênicos ({len(centros)})")
        for centro, ordem in centros:
            linhas.append(
                f"    {por_id[centro].rotulo()}: prioridades CIP {lista(ordem)}; "
                "configuração R/S não especificada"
            )
    if duplas:
        linhas.append(f"  Ligações duplas estereogênicas ({len(duplas)})")
        for (a, ordem_a), (b, ordem_b) in duplas:
            linhas.append(
                f"    {por_id[a].rotulo()}={por_id[b].rotulo()}: "
                f"lado {por_id[a].rotulo()} {lista(ordem_a)}; "
                f"lado {por_id[b].rotulo()} {lista(ordem_b)}; "
                "configuração E/Z não especificada"
            )
    total = len(centros) + len(duplas)
    linhas.append(
        f"  No máximo {2 ** total} estereoisômero(s) para esta constituição "
        "(formas meso não são descontadas)"
    )
    return "\n".join(linhas)
