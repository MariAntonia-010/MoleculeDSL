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
