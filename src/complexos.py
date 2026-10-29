from ast_nos import Operador


# Fase 9 do plano do solver: coordenação e sólidos, separados do modelo de
# valência molecular.
#
# - Centro metálico: átomo de bloco metálico com ligação a não metal.
# - Ligante: componente que sobra ao retirar os átomos metálicos.
# - Átomo doador: átomo do ligante ligado a um metal.
# - Denticidade (κ): doadores do mesmo ligante ligados ao mesmo metal.
# - Hapticidade (η): doadores vizinhos entre si ligados ao mesmo metal.
# - Ponte (μ): átomo doador ligado a mais de um metal.
# - Carga do ligante: soma das cargas formais menos a ordem das ligações
#   com metais, como se cada par voltasse para o ligante.
# - Estado de oxidação do metal: carga formal mais a ordem das ligações
#   com ligantes.
# A contagem de elétrons usa o modelo iônico e serve só de informação:
# a regra dos 18 elétrons nunca vira erro nem aviso.


def numero_do_grupo(numero_atomico):
    # Grupo de 3 a 12 para os metais de transição dos períodos 4 a 7
    for inicio in (21, 39, 71, 103):
        if inicio <= numero_atomico <= inicio + 9:
            return numero_atomico - inicio + 3
    if numero_atomico == 57 or numero_atomico == 89:
        return 3
    return None


def ordem(lig, valencias):
    return valencias["ordem_ligacao"][lig.operador.name]


def analisar(modelo, dados_elementos, valencias, ligacoes_metalicas):
    blocos = set(ligacoes_metalicas["blocos_metalicos"])
    metal = {
        a.id: dados_elementos.get(a.elemento, {}).get("bloco") in blocos
        for a in modelo.atomos
    }
    por_id = {a.id: a for a in modelo.atomos}

    ligacoes_ao_metal = {a.id: [] for a in modelo.atomos}
    vizinhos_ligante = {a.id: set() for a in modelo.atomos}
    for lig in modelo.ligacoes:
        if lig.operador is Operador.METALICA:
            continue
        a, b = lig.origem, lig.destino
        if metal[a] and not metal[b]:
            ligacoes_ao_metal[b].append((a, lig))
            ligacoes_ao_metal[a].append((b, lig))
        elif metal[b] and not metal[a]:
            ligacoes_ao_metal[a].append((b, lig))
            ligacoes_ao_metal[b].append((a, lig))
        elif not metal[a] and not metal[b]:
            vizinhos_ligante[a].add(b)
            vizinhos_ligante[b].add(a)

    centros = [
        a.id for a in modelo.atomos if metal[a.id] and ligacoes_ao_metal[a.id]
    ]
    # Ligantes: componentes conectados dos átomos não metálicos
    ligantes = []
    visto = set()
    for atomo in modelo.atomos:
        if metal[atomo.id] or atomo.id in visto:
            continue
        componente = []
        pilha = [atomo.id]
        visto.add(atomo.id)
        while pilha:
            atual = pilha.pop()
            componente.append(atual)
            for vizinho in vizinhos_ligante[atual]:
                if vizinho not in visto:
                    visto.add(vizinho)
                    pilha.append(vizinho)
        if any(ligacoes_ao_metal[i] for i in componente):
            ligantes.append(sorted(componente))

    descricao_ligantes = []
    for componente in ligantes:
        carga = sum(por_id[i].carga for i in componente) - sum(
            ordem(lig, valencias)
            for i in componente
            for _, lig in ligacoes_ao_metal[i]
        )
        por_metal = {}
        pontes = []
        for i in componente:
            metais = sorted({m for m, _ in ligacoes_ao_metal[i]})
            for m in metais:
                por_metal.setdefault(m, []).append(i)
            if len(metais) > 1:
                pontes.append((i, len(metais)))
        modos = {}
        for m, doadores in por_metal.items():
            # Grupos de doadores vizinhos entre si: cada grupo com mais de
            # um átomo é uma ligação η
            restantes = set(doadores)
            grupos = []
            while restantes:
                inicio = restantes.pop()
                grupo = [inicio]
                pilha = [inicio]
                while pilha:
                    atual = pilha.pop()
                    for vizinho in vizinhos_ligante[atual] & restantes:
                        restantes.discard(vizinho)
                        grupo.append(vizinho)
                        pilha.append(vizinho)
                grupos.append(sorted(grupo))
            modos[m] = sorted(grupos)
        descricao_ligantes.append(
            {
                "atomos": componente,
                "carga": carga,
                "modos": modos,
                "pontes": pontes,
            }
        )

    descricao_centros = []
    for m in centros:
        atomo = por_id[m]
        oxidacao = atomo.carga + sum(
            ordem(lig, valencias) for _, lig in ligacoes_ao_metal[m]
        )
        grupos = [
            grupo
            for ligante in descricao_ligantes
            for grupo in ligante["modos"].get(m, [])
        ]
        eletrons = None
        numero = dados_elementos[atomo.elemento].get("numero_atomico")
        grupo_periodico = numero_do_grupo(numero) if numero else None
        if grupo_periodico is not None:
            d = grupo_periodico - oxidacao
            if d >= 0:
                # Doador simples: 2 elétrons; grupo η^n: n, mais 1 se n for
                # ímpar (ligante aniônico no modelo iônico, como Cp⁻)
                doados = sum(
                    2 if len(g) == 1 else len(g) + len(g) % 2 for g in grupos
                )
                eletrons = (d, doados)
        descricao_centros.append(
            {
                "id": m,
                "oxidacao": oxidacao,
                "coordenacao": len(ligacoes_ao_metal[m]),
                "eletrons": eletrons,
            }
        )

    motivos = {}
    for lig in modelo.ligacoes:
        if lig.operador is Operador.METALICA:
            tipo = "metálica"
        elif lig.operador is Operador.COORDENADA:
            tipo = "coordenada"
        else:
            tipo = lig.classificacao or "não classificada"
        motivos[tipo] = motivos.get(tipo, 0) + 1

    return {
        "centros": descricao_centros,
        "ligantes": descricao_ligantes,
        "motivos": motivos,
    }


def formatar(modelo, dados_elementos, valencias, ligacoes_metalicas):
    resultado = analisar(modelo, dados_elementos, valencias, ligacoes_metalicas)
    if not resultado["centros"] and "metálica" not in resultado["motivos"]:
        return "Coordenação: nenhum centro metálico ligado a ligantes"
    por_id = {a.id: a for a in modelo.atomos}
    linhas = ["Coordenação"]
    if not resultado["centros"]:
        linhas.append(
            "  Sem centros metálicos ligados a ligantes; as arestas ~ "
            "descrevem só um motivo do sólido metálico"
        )
    else:
        linhas.append(f"  Centros metálicos ({len(resultado['centros'])})")
    for centro in resultado["centros"]:
        texto = (
            f"    {por_id[centro['id']].rotulo()}: estado de oxidação "
            f"{centro['oxidacao']:+d}, número de coordenação "
            f"{centro['coordenacao']}"
        )
        if centro["eletrons"] is not None:
            d, doados = centro["eletrons"]
            total = d + doados
            comparacao = (
                "igual a 18"
                if total == 18
                else ("abaixo de 18" if total < 18 else "acima de 18")
            )
            texto += f", d{d}, {total} elétrons ({comparacao}; só informativo)"
        linhas.append(texto)
    if resultado["ligantes"]:
        linhas.append(f"  Ligantes ({len(resultado['ligantes'])})")
    for ligante in resultado["ligantes"]:
        nomes = " ".join(por_id[i].rotulo() for i in ligante["atomos"])
        modos = []
        for m, grupos in sorted(ligante["modos"].items()):
            simples = sum(1 for g in grupos if len(g) == 1)
            partes = []
            if simples:
                partes.append(f"κ{simples}")
            for g in grupos:
                if len(g) > 1:
                    partes.append(f"η{len(g)}")
            modos.append(f"{'/'.join(partes)} em {por_id[m].rotulo()}")
        texto = f"    [{nomes}] carga {ligante['carga']:+d}; " + ", ".join(modos)
        for i, quantidade in ligante["pontes"]:
            texto += f"; ponte μ{quantidade} por {por_id[i].rotulo()}"
        linhas.append(texto)
    motivos = ", ".join(
        f"{tipo}={quantidade}"
        for tipo, quantidade in sorted(resultado["motivos"].items())
    )
    linhas.append(f"  Ligações por tipo: {motivos}")
    return "\n".join(linhas)
