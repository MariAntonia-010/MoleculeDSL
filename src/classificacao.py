"""Classificação informativa por Δχ, conforme F1–F3 do levantamento."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ast_nos import Operador


ARQUIVO_CONFIGURACAO = Path(__file__).resolve().parent.parent / "regras" / "ligacoes.json"


class ErroConfiguracao(ValueError):
    pass


def limites(configuracao):
    try:
        apolar = Decimal(str(configuracao["limite_apolar"]))
        polar = Decimal(str(configuracao["limite_polar"]))
        if not (apolar.is_finite() and polar.is_finite() and 0 <= apolar < polar):
            raise ValueError
    except (KeyError, TypeError, InvalidOperation, ValueError) as erro:
        raise ErroConfiguracao(
            "os limites de eletronegatividade devem ser números finitos, "
            "com 0 <= limite_apolar < limite_polar"
        ) from erro
    return apolar, polar


def carregar_configuracao(caminho=ARQUIVO_CONFIGURACAO):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            configuracao = json.load(arquivo)
    except (OSError, ValueError) as erro:
        raise ErroConfiguracao(f"não foi possível ler {caminho}: {erro}") from erro
    limites(configuracao)
    return configuracao


def classificar(modelo, elementos, configuracao):
    apolar, polar = limites(configuracao)
    por_id = {atomo.id: atomo for atomo in modelo.atomos}
    for ligacao in modelo.ligacoes:
        ligacao.diferenca_eletronegatividade = None
        if ligacao.operador == Operador.METALICA:
            ligacao.classificacao = "metálica"
            continue

        origem = elementos[por_id[ligacao.origem].elemento].get("eletronegatividade")
        destino = elementos[por_id[ligacao.destino].elemento].get("eletronegatividade")
        if origem is None or destino is None:
            ligacao.classificacao = None
            continue

        # Decimal preserva as fronteiras 0,4 e 1,7 dos dados decimais.
        diferenca = abs(Decimal(str(origem)) - Decimal(str(destino)))
        ligacao.diferenca_eletronegatividade = float(diferenca)
        if diferenca < apolar:
            ligacao.classificacao = "covalente apolar"
        elif diferenca <= polar:
            ligacao.classificacao = "covalente polar"
        else:
            ligacao.classificacao = "iônica"
