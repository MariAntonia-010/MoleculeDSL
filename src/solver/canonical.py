"""Identidade canônica de grafos pequenos com vértices coloridos."""

from itertools import combinations, permutations, product


def atom_signature(atom):
    return atom.element, atom.charge


def canonical_key(edges, atoms):
    groups = {}
    for index, atom in enumerate(atoms):
        groups.setdefault(atom_signature(atom), []).append(index)

    best = None
    group_permutations = [
        list(permutations(indices))
        for _, indices in sorted(groups.items())
    ]
    for parts in product(*group_permutations):
        order = [index for part in parts for index in part]
        key = tuple(
            edges.get(tuple(sorted((order[a], order[b]))), 0)
            for a, b in combinations(range(len(atoms)), 2)
        )
        if best is None or key < best:
            best = key
    return best


def canonical_heavy_key(edges, atoms, hydrogen_counts):
    groups = {}
    signatures = []
    for index, (atom, hydrogens) in enumerate(
        zip(atoms, hydrogen_counts)
    ):
        signature = (*atom_signature(atom), hydrogens)
        signatures.append(signature)
        groups.setdefault(signature, []).append(index)

    best = None
    group_permutations = [
        list(permutations(indices))
        for _, indices in sorted(groups.items())
    ]
    for parts in product(*group_permutations):
        order = [index for part in parts for index in part]
        key = (
            tuple(signatures[index] for index in order),
            tuple(
                edges.get(tuple(sorted((order[a], order[b]))), 0)
                for a, b in combinations(range(len(atoms)), 2)
            ),
        )
        if best is None or key < best:
            best = key
    return best


def hydrogens_sorted(atoms, hydrogen_counts):
    """Diz se os H crescem dentro de cada grupo de mesmo elemento e carga.

    Numa rotulação canônica isso sempre vale, então distribuições fora
    dessa ordem podem ser descartadas antes da busca pesada.
    """
    last = {}
    for atom, hydrogens in zip(atoms, hydrogen_counts):
        signature = atom_signature(atom)
        if hydrogens < last.get(signature, 0):
            return False
        last[signature] = hydrogens
    return True


def is_canonical_heavy(edges, atoms, hydrogen_counts):
    """Diz se esta rotulação é a representante da sua órbita.

    A representante é a de menor vetor (H por átomo, ordens das arestas)
    entre as permutações que trocam átomos de mesmo elemento e carga. Com
    os H já ordenados, só as permutações que preservam a quantidade de H
    podem empatar no primeiro componente, então basta testar essas.
    Exatamente uma rotulação de cada classe passa no teste, e nenhuma
    chave precisa ser guardada.
    """
    if not hydrogens_sorted(atoms, hydrogen_counts):
        return False
    count = len(atoms)
    pairs = list(combinations(range(count), 2))
    identity = tuple(edges.get(pair, 0) for pair in pairs)

    groups = {}
    for index, (atom, hydrogens) in enumerate(zip(atoms, hydrogen_counts)):
        groups.setdefault((*atom_signature(atom), hydrogens), []).append(index)
    movable = [indices for indices in groups.values() if len(indices) > 1]
    if not movable:
        return True

    for parts in product(
        *(permutations(indices) for indices in movable)
    ):
        mapping = list(range(count))
        for indices, image in zip(movable, parts):
            for source, target in zip(indices, image):
                mapping[source] = target
        permuted = tuple(
            edges.get(tuple(sorted((mapping[a], mapping[b]))), 0)
            for a, b in pairs
        )
        if permuted < identity:
            return False
    return True
