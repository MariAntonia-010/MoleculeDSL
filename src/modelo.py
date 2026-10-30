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
