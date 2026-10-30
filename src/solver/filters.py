"""Filtros objetivos para escolher entre alternativas sem ranking oculto."""

import re
from dataclasses import dataclass


ORDER_BY_SYMBOL = {"-": 1, "=": 2, "#": 3}
SYMBOL_BY_ORDER = {1: "-", 2: "=", 3: "#"}
FRAGMENT = re.compile(r"^[A-Z][a-z]?(?:[-=#][A-Z][a-z]?)+$")
TOKEN = re.compile(r"[A-Z][a-z]?|[-=#]")


@dataclass(frozen=True)
class Fragment:
    """Cadeia de átomos distintos, como C=O ou O-C=O.

    Casa com um caminho do grafo em qualquer um dos dois sentidos.
    """

    elements: tuple
    orders: tuple

    def found_in(self, elements, adjacency):
        # elements[i] é o elemento do vértice i; adjacency[i] é uma lista
        # de (vizinho, ordem)
        def extend(vertex, position, used):
            if position == len(self.orders):
                return True
            for neighbor, order in adjacency[vertex]:
                if (
                    neighbor not in used
                    and order == self.orders[position]
                    and elements[neighbor] == self.elements[position + 1]
                    and extend(neighbor, position + 1, used | {neighbor})
                ):
                    return True
            return False

        return any(
            element == self.elements[0] and extend(vertex, 0, {vertex})
            for vertex, element in enumerate(elements)
        )

    def __str__(self):
        text = self.elements[0]
        for order, element in zip(self.orders, self.elements[1:]):
            text += SYMBOL_BY_ORDER[order] + element
        return text


def parse_fragment(text):
    if FRAGMENT.match(text) is None:
        return None
    tokens = TOKEN.findall(text)
    return Fragment(
        tuple(tokens[0::2]),
        tuple(ORDER_BY_SYMBOL[symbol] for symbol in tokens[1::2]),
    )


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
        # Os H entram como folhas, depois dos átomos pesados
        elements = [atom.element for atom in heavy]
        adjacency = [[] for _ in heavy]
        for (a, b), order in heavy_edges.items():
            if order:
                adjacency[a].append((b, order))
                adjacency[b].append((a, order))
        for index, count in enumerate(hydrogen_distribution):
            for _ in range(count):
                elements.append("H")
                adjacency.append([(index, 1)])
                adjacency[index].append((len(elements) - 1, 1))
        # O solver só aceita grafos conectados, e os H são folhas: o
        # número de ciclos independentes vem só da parte pesada.
        heavy_bonds = sum(1 for order in heavy_edges.values() if order)
        rings = max(0, heavy_bonds - len(heavy) + 1)
        return self.accepts_graph(elements, adjacency, rings)

    def accepts_graph(self, elements, adjacency, rings):
        if self.rings is not None and rings != self.rings:
            return False
        multiple = (
            sum(
                1
                for vertex in adjacency
                for _, order in vertex
                if order >= 2
            )
            // 2
        )
        if self.multiple_bonds is not None and multiple != self.multiple_bonds:
            return False
        for fragment in self.required:
            if not fragment.found_in(elements, adjacency):
                return False
        for fragment in self.forbidden:
            if fragment.found_in(elements, adjacency):
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
