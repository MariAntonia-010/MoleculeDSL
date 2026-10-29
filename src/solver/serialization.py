"""Serialização versionada dos resultados do solver."""

import json

from ast_nos import AtomoDecl, LigacaoDecl


SCHEMA_VERSION = "1"


def summary_dict(summary):
    return {
        "schema_version": SCHEMA_VERSION,
        "status": summary.status.value,
        "unique": summary.unique.value,
        "complete": summary.complete,
        "solutions_emitted": summary.solutions_emitted,
        "classes_seen": summary.classes_seen,
        "backend": summary.backend,
        "backend_version": summary.backend_version,
        "truncated": summary.truncated,
        "elapsed_ms": summary.elapsed_ms,
        "details": summary.details,
    }


def summary_json(summary):
    return json.dumps(
        summary_dict(summary), ensure_ascii=False, sort_keys=True
    )


def solution_dict(molecule, index):
    atoms = []
    bonds = []
    for command in molecule.comandos:
        if isinstance(command, AtomoDecl):
            atoms.append(
                {
                    "name": command.nome,
                    "element": command.elemento,
                    "formal_charge": command.carga,
                }
            )
        elif isinstance(command, LigacaoDecl):
            bonds.append(
                {
                    "from": command.origem.texto,
                    "to": command.destino.texto,
                    "order": command.operador.value,
                }
            )
    return {
        "type": "solution",
        "index": index,
        "species": {
            "name": molecule.nome,
            "type": molecule.tipo.value,
            "total_charge": molecule.carga_total,
            "unpaired_electrons": molecule.eletrons_desemparelhados,
        },
        "atoms": atoms,
        "bonds": bonds,
    }


def result_dict(result):
    return {
        "summary": summary_dict(result.summary),
        "messages": [str(message) for message in result.messages],
        "solutions": [
            solution_dict(solution, index)
            for index, solution in enumerate(result.solutions, start=1)
        ],
    }


def result_json(result):
    return json.dumps(
        result_dict(result), ensure_ascii=False, sort_keys=True
    )


def solution_jsonl(molecule, index):
    return json.dumps(
        solution_dict(molecule, index), ensure_ascii=False, sort_keys=True
    )


def summary_jsonl(summary):
    return json.dumps(
        {"type": "summary", **summary_dict(summary)},
        ensure_ascii=False,
        sort_keys=True,
    )


def result_jsonl(result):
    lines = [
        solution_jsonl(solution, index)
        for index, solution in enumerate(result.solutions, start=1)
    ]
    lines.append(summary_jsonl(result.summary))
    return "\n".join(lines)
