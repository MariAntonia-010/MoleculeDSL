"""Filtros objetivos para escolher entre alternativas sem ranking oculto."""

import re
from dataclasses import dataclass


ORDER_BY_SYMBOL = {"-": 1, "=": 2, "#": 3}
FRAGMENT = re.compile(r"^([A-Z][a-z]?)([-=#])([A-Z][a-z]?)$")


@dataclass(frozen=True)
class Fragment:
    first: str
    order: int
    second: str

    def matches(self, bond):
        a, order, b = bond
        return order == self.order and (
            (a, b) == (self.first, self.second)
            or (b, a) == (self.first, self.second)
        )

    def __str__(self):
        symbol = {1: "-", 2: "=", 3: "#"}[self.order]
        return f"{self.first}{symbol}{self.second}"


def parse_fragment(text):
    match = FRAGMENT.match(text)
    if match is None:
        return None
    first, symbol, second = match.groups()
    return Fragment(first, ORDER_BY_SYMBOL[symbol], second)


@dataclass(frozen=True)
class SolveFilters:
    rings: int | None = None
    multiple_bonds: int | None = None
    required: tuple = ()
    forbidden: tuple = ()

    @property
    def active(self):
        return (
            self.rings is not None
            or self.multiple_bonds is not None
            or bool(self.required)
            or bool(self.forbidden)
        )

    def accepts(self, heavy, heavy_edges, hydrogen_distribution):
        bonds = [
            (heavy[a].element, order, heavy[b].element)
            for (a, b), order in heavy_edges.items()
            if order
        ]
        bonds += [
            (atom.element, 1, "H")
            for atom, count in zip(heavy, hydrogen_distribution)
            if count
        ]
        # O solver só aceita grafos conectados, e os H são folhas: o
        # número de ciclos independentes vem só da parte pesada.
        heavy_bonds = sum(1 for order in heavy_edges.values() if order)
        rings = max(0, heavy_bonds - len(heavy) + 1)
        return self.accepts_bonds(bonds, rings)

    def accepts_bonds(self, bonds, rings):
        if self.rings is not None and rings != self.rings:
            return False
        multiple = sum(1 for _, order, _ in bonds if order >= 2)
        if self.multiple_bonds is not None and multiple != self.multiple_bonds:
            return False
        for fragment in self.required:
            if not any(fragment.matches(bond) for bond in bonds):
                return False
        for fragment in self.forbidden:
            if any(fragment.matches(bond) for bond in bonds):
                return False
        return True

    def describe(self):
        parts = []
        if self.rings is not None:
            parts.append(f"anéis={self.rings}")
        if self.multiple_bonds is not None:
            parts.append(f"ligações múltiplas={self.multiple_bonds}")
        parts += [f"exigir={fragment}" for fragment in self.required]
        parts += [f"proibir={fragment}" for fragment in self.forbidden]
        return parts
