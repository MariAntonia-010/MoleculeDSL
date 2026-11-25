from dataclasses import dataclass, field

from ast_nos import Operador, TipoEspecie


# Modelo interno da molécula: um grafo em que os átomos são os vértices
# e as ligações são as arestas. É montado pela análise semântica a
# partir da AST, já com os multiplicadores e as repetições expandidos.


@dataclass
class Atomo:
    # id é único na molécula; indice conta só os átomos do mesmo elemento
    id: int
    elemento: str
    indice: int
    carga: int
    nome: str | None
    linha: int
    coluna: int
    # Número de massa declarado (atom 13C) e configuração eletrônica
    # declarada, como lista de (n, l, elétrons)
    massa: int | None = None
    configuracao: list | None = None
    # Átomo montado pela semântica (montar_atomos): todo 'atom X' nasce
    # com Z prótons, os nêutrons do isótopo declarado ou do natural mais
    # abundante, e Z − carga elétrons no estado fundamental
    protons: int | None = None
    neutrons: int | None = None
    eletrons: int | None = None
    origem_nucleo: str | None = None
    eletrosfera: dict | None = None

    def rotulo(self):
        # Ex.: "H#2" ou "c1 (C#1)"
        if self.nome is not None:
            return f"{self.nome} ({self.elemento}#{self.indice})"
        return f"{self.elemento}#{self.indice}"


@dataclass
class Ligacao:
    # Na ligação coordenada, origem é o doador e destino o receptor
    origem: int
    destino: int
    operador: Operador
    linha: int
    coluna: int
    classificacao: str | None = None
    diferenca_eletronegatividade: float | None = None


@dataclass
class Estereo:
    # Configuração declarada: atomos são ids; operador é "=", "-" ou None
    atomos: list
    operador: str | None
    descritor: str
    linha: int
    coluna: int


@dataclass
class BuracoNegro:
    # Resultado de 'collapse' numa species black_hole: a matéria que entrou
    # e o que sobra dela pelo teorema da calvície (massa e carga)
    bloco: str
    formula: str
    quantidade_mol: float
    massa_particula_u: float
    massa_kg: float
    massa_solar: float
    raio_schwarzschild_m: float
    temperatura_hawking_k: float
    evaporacao_anos: float
    limite_tov: float


@dataclass
class Modelo:
    nome: str
    tipo: TipoEspecie = TipoEspecie.MOLECULA
    carga_total: int | None = None
    eletrons_desemparelhados: int | None = None
    atomos: list[Atomo] = field(default_factory=list)
    ligacoes: list[Ligacao] = field(default_factory=list)
    # Cada anel é a lista de ids dos átomos, na ordem citada
    aneis: list[list[int]] = field(default_factory=list)
    estereo: list[Estereo] = field(default_factory=list)
    buraco_negro: BuracoNegro | None = None


SOBRESCRITO = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def cientifico(valor, casas=3):
    # 6.16e30 vira "6,16 × 10³⁰"; números entre 0,01 e 9999 ficam por extenso
    if valor == 0:
        return "0"
    from math import floor, log10

    expoente = floor(log10(abs(valor)))
    if -2 <= expoente < 4:
        texto = f"{valor:.{max(casas - 1 - expoente, 0)}f}"
        return texto.replace(".", ",")
    mantissa = valor / 10**expoente
    if round(mantissa, casas - 1) >= 10:
        mantissa /= 10
        expoente += 1
    return f"{mantissa:.{casas - 1}f}".replace(".", ",") + " × 10" + str(expoente).translate(SOBRESCRITO)


def comprimento(metros):
    if metros >= 1e3:
        return f"{cientifico(metros / 1e3)} km"
    if metros >= 1:
        return f"{cientifico(metros)} m"
    if metros >= 1e-3:
        return f"{cientifico(metros * 1e3)} mm"
    return f"{cientifico(metros)} m"


def formatar_buraco_negro(modelo):
    b = modelo.buraco_negro
    rs = b.raio_schwarzschild_m
    return "\n".join([
        f"Modelo {modelo.nome!r} tipo={modelo.tipo.value} carga_total=+0 desemparelhados=não declarado",
        f"  Colapso: {cientifico(b.quantidade_mol)} mol de {b.bloco!r} ({b.formula}, "
        f"{cientifico(b.massa_particula_u, 4)} u por partícula)",
        f"  Massa: {cientifico(b.massa_kg)} kg = {cientifico(b.massa_solar)} M☉ "
        f"(acima do limite de Tolman-Oppenheimer-Volkoff, {cientifico(b.limite_tov)} M☉)",
        f"  Horizonte (raio de Schwarzschild, 2GM/c²): {comprimento(rs)}",
        f"  Esfera de fótons (1,5 r_s): {comprimento(1.5 * rs)}; "
        f"sombra vista de longe (≈2,6 r_s): {comprimento(27**0.5 / 2 * rs)}",
        f"  Temperatura de Hawking: {cientifico(b.temperatura_hawking_k)} K; "
        f"evaporação: {cientifico(b.evaporacao_anos)} anos",
        f"  Teorema da calvície: o horizonte guarda só massa, carga e rotação; "
        f"a fórmula {b.formula} não existe mais",
    ])


def texto_montado(a):
    # " p=8 n=8 (16O, mais abundante) e=8 [He] 2s2 2p4", ou "" sem dados
    if a.protons is None:
        return ""
    import atomo as estrutura_atomica

    if a.neutrons is None:
        nucleo = f" p={a.protons} n=? (sem isótopo natural)"
    else:
        nucleo = f" p={a.protons} n={a.neutrons} ({a.protons + a.neutrons}{a.elemento}, {a.origem_nucleo})"
    config = f" {estrutura_atomica.texto_com_nucleo(a.eletrosfera)}" if a.eletrosfera is not None else ""
    return f"{nucleo} e={a.eletrons}{config}"


def formatar(modelo):
    """Texto legível do modelo, para a opção de depuração"""
    if modelo.buraco_negro is not None:
        return formatar_buraco_negro(modelo)
    por_id = {a.id: a for a in modelo.atomos}

    carga = (
        "não declarada"
        if modelo.carga_total is None
        else f"{modelo.carga_total:+d}"
    )
    desemparelhados = (
        "não declarado"
        if modelo.eletrons_desemparelhados is None
        else str(modelo.eletrons_desemparelhados)
    )
    linhas = [
        f"Modelo {modelo.nome!r} tipo={modelo.tipo.value} "
        f"carga_total={carga} desemparelhados={desemparelhados}"
    ]

    linhas.append(f"  Átomos ({len(modelo.atomos)})")
    for a in modelo.atomos:
        massa = f" A={a.massa}" if a.massa is not None else ""
        linhas.append(f"    {a.rotulo()} carga={a.carga:+d}{massa}{texto_montado(a)} [{a.linha}:{a.coluna}]")

    linhas.append(f"  Ligações ({len(modelo.ligacoes)})")
    for lig in modelo.ligacoes:
        detalhes = (
            f" classificação={lig.classificacao}"
            if lig.classificacao is not None
            else " classificação=não classificada"
        )
        if lig.diferenca_eletronegatividade is not None:
            detalhes += f" Δχ={lig.diferenca_eletronegatividade:.2f}"
        linhas.append(
            f"    {por_id[lig.origem].rotulo()} {lig.operador.name} "
            f"{por_id[lig.destino].rotulo()}{detalhes} "
            f"[{lig.linha}:{lig.coluna}]"
        )

    if modelo.aneis:
        linhas.append(f"  Anéis ({len(modelo.aneis)})")
        for anel in modelo.aneis:
            linhas.append("    " + " ".join(por_id[i].rotulo() for i in anel))

    if modelo.estereo:
        linhas.append(f"  Configurações declaradas ({len(modelo.estereo)})")
        for e in modelo.estereo:
            separador = e.operador or " "
            alvo = separador.join(por_id[i].rotulo() for i in e.atomos)
            linhas.append(f"    {alvo} {e.descritor} [{e.linha}:{e.coluna}]")

    return "\n".join(linhas)
