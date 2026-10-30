import re


# Estrutura do átomo (docs/plano_atomo.md): núcleo e eletrosfera.
#
# - Pauli: a subcamada de número l comporta 2(2l+1) elétrons, e l vai de 0 a
#   n−1 (não existem 1p, 2d, 3f).
# - Aufbau/Madelung: ordem de preenchimento por n + l e, no empate, por n.
#   As exceções reais (Cr, Cu...) ficam nos dados medidos de
#   regras/elementos.json, que são a referência do estado fundamental.
# - Hund: em orbitais de mesma energia os elétrons entram um de cada vez
#   antes de formar pares, o que dá os desemparelhados.
# - Íons: o cátion perde primeiro os elétrons da camada de maior n (ns antes
#   de (n−1)d); o ânion ganha na ordem de Madelung.

L_DA_LETRA = {"s": 0, "p": 1, "d": 2, "f": 3}
LETRA_DO_L = "spdf"
NUCLEOS = {
    "He": "1s2",
    "Ne": "[He] 2s2 2p6",
    "Ar": "[Ne] 3s2 3p6",
    "Kr": "[Ar] 3d10 4s2 4p6",
    "Xe": "[Kr] 4d10 5s2 5p6",
    "Rn": "[Xe] 4f14 5d10 6s2 6p6",
}
SUBCAMADA = re.compile(r"(\d)([spdf])(\d+)")


def capacidade(l):
    return 2 * (2 * l + 1)


def ordem_madelung():
    # (n, l) em ordem de preenchimento: n + l crescente e, no empate, n
    pares = [(n, l) for n in range(1, 8) for l in range(0, min(n, 4))]
    return sorted(pares, key=lambda p: (p[0] + p[1], p[0]))


def ler_subcamadas(texto):
    """Lista de (n, l, elétrons) de um texto como '[Ne] 3s2 3p4'.

    O núcleo de gás nobre é expandido; não confere nada.
    """
    for _ in range(6):
        if "[" not in texto:
            break
        texto = re.sub(r"\[(\w+)\]", lambda m: f" {NUCLEOS.get(m.group(1), '')} ", texto, count=1)
    return [(int(n), L_DA_LETRA[letra], int(e)) for n, letra, e in SUBCAMADA.findall(texto)]


def problemas_de_pauli(subcamadas):
    """Mensagens para subcamadas impossíveis, cheias demais ou repetidas."""
    problemas = []
    vistas = set()
    for n, l, e in subcamadas:
        rotulo = f"{n}{LETRA_DO_L[l]}{e}"
        if l >= n:
            problemas.append(
                f"a subcamada {n}{LETRA_DO_L[l]} não existe: na camada {n}, l vai de 0 a {n - 1}"
            )
        elif e > capacidade(l) or e == 0:
            problemas.append(
                f"{rotulo}: a subcamada {LETRA_DO_L[l]} comporta de 1 a {capacidade(l)} "
                "elétrons (princípio de Pauli)"
            )
        if (n, l) in vistas:
            problemas.append(f"a subcamada {n}{LETRA_DO_L[l]} aparece mais de uma vez")
        vistas.add((n, l))
    return problemas


def normalizar(subcamadas):
    # Dicionário (n, l) -> elétrons, sem subcamadas vazias
    return {(n, l): e for n, l, e in subcamadas if e}


def configuracao_fundamental(simbolo, carga, dados_elementos):
    """Estado fundamental de referência como dicionário (n, l) -> elétrons.

    Neutro: a configuração medida de regras/elementos.json. Íon: derivada
    dela. Devolve None se o elemento não tem configuração nos dados.
    """
    texto = (dados_elementos.get(simbolo) or {}).get("configuracao_eletronica")
    if not texto:
        return None
    config = normalizar(ler_subcamadas(texto))
    if carga > 0:
        for _ in range(carga):
            if not config:
                break
            # maior n primeiro; na mesma camada, maior l primeiro
            n, l = max(config, key=lambda p: (p[0], p[1]))
            config[(n, l)] -= 1
            if not config[(n, l)]:
                del config[(n, l)]
    elif carga < 0:
        for _ in range(-carga):
            for n, l in ordem_madelung():
                if config.get((n, l), 0) < capacidade(l):
                    config[(n, l)] = config.get((n, l), 0) + 1
                    break
    return config


def texto_configuracao(config):
    partes = sorted(config.items(), key=lambda item: (item[0][0], item[0][1]))
    return " ".join(f"{n}{LETRA_DO_L[l]}{e}" for (n, l), e in partes) or "(sem elétrons)"


def texto_com_nucleo(config):
    """Configuração abreviada com o maior núcleo de gás nobre: [He] 2s2 2p4."""
    for gas in reversed(list(NUCLEOS)):
        nucleo = normalizar(ler_subcamadas(f"[{gas}]"))
        if len(config) >= len(nucleo) and all(config.get(c) == e for c, e in nucleo.items()):
            resto = {c: e for c, e in config.items() if c not in nucleo}
            # Igual ao gás nobre (Na+, Cl-): só o núcleo
            return f"[{gas}] {texto_configuracao(resto)}" if resto else f"[{gas}]"
    return texto_configuracao(config)


def desemparelhados(config):
    # Regra de Hund, subcamada por subcamada
    total = 0
    for (n, l), e in config.items():
        orbitais = 2 * l + 1
        total += e if e <= orbitais else 2 * orbitais - e
    return total


LETRA_DO_TERMO = "SPDFGHIKLMNOQRTUV"


def termo_fundamental(config):
    """Termo espectroscópico de menor energia da configuração, 2S+1 L J.

    Regras de Hund, subcamada aberta por subcamada aberta: S máximo
    (elétrons de spin paralelo um por orbital), depois L máximo (orbitais
    de maior ml primeiro) e, para J, |L − S| se a subcamada está menos que
    meio cheia e L + S se está mais. Com várias subcamadas abertas, os
    spins se somam e J segue a subcamada de maior l que não está meio
    cheia: é uma aproximação, que falha em alguns átomos pesados (Ce, por
    exemplo, é ¹G₄ e não ³H₄). Devolve (multiplicidade, L, J em dobro).
    """
    dobro_s = 0
    total_l = 0
    decide_j = None
    for (n, l), e in sorted(config.items(), key=lambda item: (item[0][1], item[0][0])):
        orbitais = 2 * l + 1
        if e >= capacidade(l):
            continue
        acima = min(e, orbitais)
        abaixo = e - acima
        dobro_s += acima - abaixo
        # ml de l até −l: os de spin acima e depois os de spin abaixo
        total_l += sum(range(l, l - acima, -1)) + sum(range(l, l - abaixo, -1))
        if e != orbitais:
            decide_j = e < orbitais
    if decide_j is None or decide_j:
        dobro_j = abs(2 * total_l - dobro_s)
    else:
        dobro_j = 2 * total_l + dobro_s
    return dobro_s + 1, total_l, dobro_j


def texto_termo(termo):
    multiplicidade, l, dobro_j = termo
    j = str(dobro_j // 2) if dobro_j % 2 == 0 else f"{dobro_j}/2"
    letra = LETRA_DO_TERMO[l] if l < len(LETRA_DO_TERMO) else f"L={l}"
    return f"{multiplicidade}{letra}{j}"


def camadas(config):
    maior = max((n for n, _ in config), default=0)
    return [sum(e for (n, _), e in config.items() if n == k) for k in range(1, maior + 1)]


def diagrama(config, quantas=2):
    """Caixas de orbitais (Hund) das últimas subcamadas, em texto."""
    ordenadas = sorted(config.items(), key=lambda item: (item[0][0] + item[0][1], item[0][0]))
    linhas = []
    for (n, l), e in ordenadas[-quantas:]:
        orbitais = 2 * l + 1
        caixas = []
        for k in range(orbitais):
            setas = ("↑" if e > k else "") + ("↓" if e > orbitais + k else "")
            caixas.append(f"[{setas or ' '}]")
        linhas.append(f"{n}{LETRA_DO_L[l]}: {''.join(caixas)}")
    return linhas


def formatar(modelo, dados_elementos):
    """Relatório --estrutura-atomica: núcleo e eletrosfera de cada átomo."""
    linhas = ["Estrutura atômica"]
    for atomo in modelo.atomos:
        dados = dados_elementos.get(atomo.elemento, {})
        z = dados.get("numero_atomico")
        eletrons = z - atomo.carga if z is not None else None
        nucleo = f"Z={z}"
        if atomo.neutrons is not None:
            a = z + atomo.neutrons
            nucleo += f" A={a} prótons={z} nêutrons={atomo.neutrons} ({a}{atomo.elemento}, {atomo.origem_nucleo})"
        else:
            nucleo += f" prótons={z} (sem isótopo natural: nêutrons indefinidos)"
        linhas.append(f"  {atomo.rotulo()}: {dados.get('nome', atomo.elemento)}")
        linhas.append(f"    núcleo: {nucleo}")
        if atomo.configuracao is not None:
            config, origem = normalizar(atomo.configuracao), "declarada"
        else:
            config, origem = configuracao_fundamental(atomo.elemento, atomo.carga, dados_elementos), "referência"
        linhas.append(f"    eletrosfera: elétrons={eletrons} carga={atomo.carga:+d}")
        if config is None:
            linhas.append("    configuração: sem dado na fonte")
            continue
        linhas.append(f"    configuração ({origem}): {texto_configuracao(config)}")
        linhas.append(f"    camadas: {', '.join(str(c) for c in camadas(config))}")
        linhas.append(f"    desemparelhados (Hund): {desemparelhados(config)}")
        linhas.append(f"    termo fundamental (regras de Hund): {texto_termo(termo_fundamental(config))}")
        for caixa in diagrama(config):
            linhas.append(f"    {caixa}")
    if len(modelo.atomos) > 1:
        linhas.append(
            "  Observação: dentro de uma molécula os elétrons de valência ocupam "
            "orbitais moleculares; a configuração mostrada é a do átomo isolado."
        )
    return "\n".join(linhas)
