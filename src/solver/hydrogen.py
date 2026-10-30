"""Distribuição canônica de hidrogênios sobre átomos pesados."""

from solver.canonical import atom_signature


def distributions(heavy_atoms, target_valences, hydrogen_count):
    if not heavy_atoms:
        return [()] if hydrogen_count == 0 else []

    results = []
    current = [0] * len(heavy_atoms)

    def equivalent(a, b):
        # Mesma assinatura do canônico: elemento, carga e número de massa
        return (
            atom_signature(heavy_atoms[a]) == atom_signature(heavy_atoms[b])
            and target_valences[a] == target_valences[b]
        )

    def visit(index, remaining):
        if index == len(heavy_atoms):
            if remaining == 0:
                results.append(tuple(current))
            return

        maximum = min(target_valences[index], remaining)
        minimum = 0
        if index and equivalent(index - 1, index):
            minimum = current[index - 1]
        for count in range(minimum, maximum + 1):
            current[index] = count
            visit(index + 1, remaining - count)
        current[index] = 0

    visit(0, hydrogen_count)
    if results:
        average = hydrogen_count / len(heavy_atoms)
        results.sort(
            key=lambda values: (
                max(values) - min(values),
                sum(abs(value - average) for value in values),
                values,
            )
        )
    return results
