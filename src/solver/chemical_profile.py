"""Perfil químico explícito usado pela busca de referência."""

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ChemicalProfile:
    rules: dict
    digest: str
    name: str
    version: str

    def allowed_valences(self, atom):
        if atom.charge:
            table = self.rules["valencias_com_carga"].get(
                atom.element, {}
            )
            return table.get(f"{atom.charge:+d}")
        return self.rules["valencias"].get(atom.element)


def from_rules(rules):
    serialized = json.dumps(
        rules, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(serialized).hexdigest()[:16]
    # Regras sem o bloco "perfil" continuam aceitas; o digest ainda
    # identifica o conteúdo exato.
    perfil = rules.get("perfil", {})
    return ChemicalProfile(
        rules,
        digest,
        perfil.get("nome", "sem-nome"),
        str(perfil.get("versao", "0")),
    )
