from dataclasses import dataclass, field

from ast_nos import Operador


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


@dataclass
class Modelo:
    nome: str
    atomos: list[Atomo] = field(default_factory=list)
    ligacoes: list[Ligacao] = field(default_factory=list)
    # Cada anel é a lista de ids dos átomos, na ordem citada
    aneis: list[list[int]] = field(default_factory=list)


def formatar(modelo):
    """Texto legível do modelo, para a opção de depuração"""
    por_id = {a.id: a for a in modelo.atomos}

    linhas = [f"Modelo {modelo.nome!r}"]

    linhas.append(f"  Átomos ({len(modelo.atomos)})")
    for a in modelo.atomos:
        linhas.append(f"    {a.rotulo()} carga={a.carga:+d} [{a.linha}:{a.coluna}]")

    linhas.append(f"  Ligações ({len(modelo.ligacoes)})")
    for lig in modelo.ligacoes:
        linhas.append(
            f"    {por_id[lig.origem].rotulo()} {lig.operador.name} "
            f"{por_id[lig.destino].rotulo()} [{lig.linha}:{lig.coluna}]"
        )

    if modelo.aneis:
        linhas.append(f"  Anéis ({len(modelo.aneis)})")
        for anel in modelo.aneis:
            linhas.append("    " + " ".join(por_id[i].rotulo() for i in anel))

    return "\n".join(linhas)
