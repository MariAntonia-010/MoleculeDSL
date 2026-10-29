"""Normalização da AST para o domínio do solver."""

from dataclasses import dataclass

from ast_nos import AnelDecl, AtomoDecl, LigacaoDecl


@dataclass(frozen=True)
class SolverAtom:
    index: int
    element: str
    charge: int
    line: int
    column: int
    name: str

    @property
    def is_hydrogen(self):
        return self.element == "H"


@dataclass(frozen=True)
class SolveProblem:
    molecule: object
    atoms: tuple[SolverAtom, ...]

    @property
    def heavy_atoms(self):
        return tuple(atom for atom in self.atoms if not atom.is_hydrogen)

    @property
    def hydrogens(self):
        return tuple(atom for atom in self.atoms if atom.is_hydrogen)


def normalize(molecule):
    for command in molecule.comandos:
        if isinstance(command, (LigacaoDecl, AnelDecl)):
            return None, command

    atoms = []
    for command in molecule.comandos:
        if not isinstance(command, AtomoDecl):
            continue
        for _ in range(command.multiplicador):
            index = len(atoms)
            atoms.append(
                SolverAtom(
                    index=index,
                    element=command.elemento,
                    charge=command.carga,
                    line=command.linha,
                    column=command.coluna,
                    name=f"r{index + 1}",
                )
            )
    return SolveProblem(molecule, tuple(atoms)), None
