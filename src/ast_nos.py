from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# Nós da AST da MoleculeDSL. Todos guardam linha e coluna (coluna a
# partir de 0, como nos erros léxicos e sintáticos), para a semântica
# poder apontar onde está o problema.


class Operador(Enum):
    SIMPLES = "-"
    DUPLA = "="
    TRIPLA = "#"
    COORDENADA = "->"
    METALICA = "~"


class TipoReferencia(Enum):
    ELEMENTO = "elemento"
    NOME = "nome"


class TipoEspecie(Enum):
    MOLECULA = "molecule"
    ION_MOLECULAR = "molecular_ion"
    SOLIDO_IONICO = "ionic_solid"
    REDE_COVALENTE = "covalent_network"
    SOLIDO_METALICO = "metallic_solid"


@dataclass
class Referencia:
    texto: str
    tipo: TipoReferencia
    linha: int
    coluna: int


@dataclass
class AtomoDecl:
    multiplicador: int
    elemento: str
    carga: int
    nome: str | None
    linha: int
    coluna: int


@dataclass
class LigacaoDecl:
    origem: Referencia
    operador: Operador
    destino: Referencia
    repeticoes: int
    linha: int
    coluna: int


@dataclass
class AnelDecl:
    nomes: list[Referencia]
    linha: int
    coluna: int


Comando = AtomoDecl | LigacaoDecl | AnelDecl


@dataclass
class Molecula:
    nome: str
    linha: int
    coluna: int
    comandos: list[Comando] = field(default_factory=list)
    tipo: TipoEspecie = TipoEspecie.MOLECULA
    carga_total: int | None = None
    eletrons_desemparelhados: int | None = None
    declaracao_legacy: bool = True


def formatar(molecula):
    """Texto legível da AST, um nó por linha, para a opção de depuração"""

    def pos(no):
        return f"[{no.linha}:{no.coluna}]"

    def ref(r):
        return f"{r.texto} ({r.tipo.value}) {pos(r)}"

    carga = (
        "não declarada"
        if molecula.carga_total is None
        else f"{molecula.carga_total:+d}"
    )
    desemparelhados = (
        "não declarado"
        if molecula.eletrons_desemparelhados is None
        else str(molecula.eletrons_desemparelhados)
    )
    linhas = [
        f"Molecula {molecula.nome!r} tipo={molecula.tipo.value} "
        f"carga_total={carga} desemparelhados={desemparelhados} {pos(molecula)}"
    ]

    for c in molecula.comandos:
        if isinstance(c, AtomoDecl):
            linhas.append(
                f"  AtomoDecl elemento={c.elemento} multiplicador={c.multiplicador} "
                f"carga={c.carga:+d} nome={c.nome} {pos(c)}"
            )
        elif isinstance(c, LigacaoDecl):
            linhas.append(
                f"  LigacaoDecl {c.operador.name} repeticoes={c.repeticoes} {pos(c)}"
            )
            linhas.append(f"    origem:  {ref(c.origem)}")
            linhas.append(f"    destino: {ref(c.destino)}")
        elif isinstance(c, AnelDecl):
            linhas.append(f"  AnelDecl {pos(c)}")
            for r in c.nomes:
                linhas.append(f"    {ref(r)}")

    return "\n".join(linhas)
