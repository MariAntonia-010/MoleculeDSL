"""Desenha a Parse Tree do ANTLR ou a AST da MoleculeDSL em SVG.

Uso dentro do repositório:
    python src/desenhar_arvore.py exemplos/agua.mol --tipo sintatica
    python src/desenhar_arvore.py exemplos/agua.mol --tipo ast

O SVG é gerado sem depender de Graphviz, matplotlib ou outras bibliotecas de desenho.
"""

from __future__ import annotations

import argparse
import html
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class NoVisual:
    rotulo: str
    filhos: list["NoVisual"] = field(default_factory=list)
    largura: float = 0
    largura_subarvore: float = 0
    centro_x: float = 0
    topo_y: float = 0


def parse_tree_para_visual(no, parser) -> NoVisual:
    """Converte recursivamente a Parse Tree do ANTLR numa estrutura visual."""
    if hasattr(no, "getRuleIndex"):
        indice = no.getRuleIndex()
        nomes_regras = parser.ruleNames
        rotulo = nomes_regras[indice] if 0 <= indice < len(nomes_regras) else "regra"
        filhos = [parse_tree_para_visual(filho, parser) for filho in (no.children or [])]
        return NoVisual(rotulo, filhos)

    simbolo = no.getSymbol()
    if simbolo.type == -1:  # EOF no runtime do ANTLR
        return NoVisual("EOF")

    nomes = getattr(parser, "symbolicNames", [])
    tipo = nomes[simbolo.type] if 0 <= simbolo.type < len(nomes) else None
    texto = simbolo.text if simbolo.text is not None else ""
    if not tipo or tipo == "<INVALID>":
        tipo = "TOKEN"
    return NoVisual(f"{tipo}: {texto}")


def ast_para_visual(molecula) -> NoVisual:
    """Converte os nós próprios da AST da MoleculeDSL em nós visuais."""
    from ast_nos import AnelDecl, AtomoDecl, LigacaoDecl

    comandos = []
    for comando in molecula.comandos:
        if isinstance(comando, AtomoDecl):
            comandos.append(
                NoVisual(
                    "AtomoDecl",
                    [
                        NoVisual(f"elemento: {comando.elemento}"),
                        NoVisual(f"multiplicador: {comando.multiplicador}"),
                        NoVisual(f"carga: {comando.carga}"),
                        NoVisual(f"nome: {comando.nome if comando.nome is not None else 'None'}"),
                    ],
                )
            )
        elif isinstance(comando, LigacaoDecl):
            comandos.append(
                NoVisual(
                    "LigacaoDecl",
                    [
                        NoVisual(
                            f"origem: {comando.origem.texto} "
                            f"({comando.origem.tipo.value})"
                        ),
                        NoVisual(f"operador: {comando.operador.name}"),
                        NoVisual(
                            f"destino: {comando.destino.texto} "
                            f"({comando.destino.tipo.value})"
                        ),
                        NoVisual(f"repeticoes: {comando.repeticoes}"),
                    ],
                )
            )
        elif isinstance(comando, AnelDecl):
            comandos.append(
                NoVisual(
                    "AnelDecl",
                    [
                        NoVisual(f"nome: {ref.texto} ({ref.tipo.value})")
                        for ref in comando.nomes
                    ],
                )
            )
        else:
            comandos.append(NoVisual(type(comando).__name__))

    return NoVisual(
        f'Molecula: "{molecula.nome}"',
        [NoVisual("comandos", comandos)],
    )


def medir_subarvores(no: NoVisual, altura_no: float = 38, espacamento_x: float = 22) -> float:
    """Calcula a largura necessária para posicionar cada subárvore."""
    # Largura aproximada para a fonte sans-serif usada no SVG.
    no.largura = max(76, len(no.rotulo) * 7.4 + 26)
    if not no.filhos:
        no.largura_subarvore = no.largura
    else:
        soma_filhos = sum(medir_subarvores(f, altura_no, espacamento_x) for f in no.filhos)
        soma_filhos += espacamento_x * (len(no.filhos) - 1)
        no.largura_subarvore = max(no.largura, soma_filhos)
    return no.largura_subarvore


def posicionar(no: NoVisual, esquerda: float, profundidade: int,
               margem_topo: float, espacamento_y: float, espacamento_x: float) -> int:
    """Posiciona os nós por nível e centraliza os pais sobre os filhos."""
    no.centro_x = esquerda + no.largura_subarvore / 2
    no.topo_y = margem_topo + profundidade * espacamento_y
    maior_profundidade = profundidade

    if no.filhos:
        largura_filhos = sum(f.largura_subarvore for f in no.filhos)
        largura_filhos += espacamento_x * (len(no.filhos) - 1)
        x = esquerda + (no.largura_subarvore - largura_filhos) / 2
        for filho in no.filhos:
            maior_profundidade = max(
                maior_profundidade,
                posicionar(filho, x, profundidade + 1, margem_topo, espacamento_y, espacamento_x),
            )
            x += filho.largura_subarvore + espacamento_x
    return maior_profundidade


def renderizar_svg(raiz: NoVisual, destino: Path, titulo: str) -> None:
    margem = 30
    altura_no = 38
    espacamento_x = 22
    espacamento_y = 82
    margem_topo = 54

    medir_subarvores(raiz, altura_no, espacamento_x)
    profundidade_maxima = posicionar(
        raiz, margem, 0, margem_topo, espacamento_y, espacamento_x
    )
    largura_svg = raiz.largura_subarvore + margem * 2
    altura_svg = margem_topo + profundidade_maxima * espacamento_y + altura_no + margem

    linhas: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura_svg:.0f}" '
        f'height="{altura_svg:.0f}" viewBox="0 0 {largura_svg:.0f} {altura_svg:.0f}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;font-size:13px;fill:#172033}'
        '.no{fill:#ffffff;stroke:#64748b;stroke-width:1.3}'
        '.aresta{fill:none;stroke:#94a3b8;stroke-width:1.3}'
        '.titulo{font-size:19px;font-weight:700;fill:#0f172a}</style>',
        f'<text class="titulo" x="{margem}" y="27">{html.escape(titulo)}</text>',
    ]

    # Desenha as arestas antes dos retângulos para as linhas ficarem por baixo dos nós.
    def desenhar_arestas(no: NoVisual) -> None:
        for filho in no.filhos:
            x1 = no.centro_x
            y1 = no.topo_y + altura_no
            x2 = filho.centro_x
            y2 = filho.topo_y
            meio_y = (y1 + y2) / 2
            linhas.append(
                f'<path class="aresta" d="M {x1:.1f} {y1:.1f} '
                f'L {x1:.1f} {meio_y:.1f} L {x2:.1f} {meio_y:.1f} L {x2:.1f} {y2:.1f}"/>'
            )
            desenhar_arestas(filho)

    def desenhar_nos(no: NoVisual) -> None:
        x = no.centro_x - no.largura / 2
        y = no.topo_y
        linhas.append(
            f'<rect class="no" x="{x:.1f}" y="{y:.1f}" '
            f'width="{no.largura:.1f}" height="{altura_no}" rx="8" ry="8"/>'
        )
        # SVG escapa caracteres especiais, como aspas e sinais < ou >.
        linhas.append(
            f'<text x="{no.centro_x:.1f}" y="{y + 23:.1f}" '
            f'text-anchor="middle">{html.escape(no.rotulo)}</text>'
        )
        for filho in no.filhos:
            desenhar_nos(filho)

    desenhar_arestas(raiz)
    desenhar_nos(raiz)
    linhas.append("</svg>")
    destino.write_text("\n".join(linhas), encoding="utf-8")


def main() -> int:
    argumento = argparse.ArgumentParser(
        description="Gera um desenho SVG da árvore sintática ou da AST da MoleculeDSL."
    )
    argumento.add_argument("arquivo", help="arquivo .mol que será analisado")
    argumento.add_argument(
        "--tipo", choices=("sintatica", "ast"), default="sintatica",
        help="tipo de árvore a desenhar (padrão: sintatica)",
    )
    argumento.add_argument(
        "-o", "--saida", help="caminho do SVG de saída; por padrão, fica ao lado do .mol"
    )
    args = argumento.parse_args()

    entrada = Path(args.arquivo)
    if not entrada.is_file():
        print(f"Arquivo não encontrado: {entrada}", file=sys.stderr)
        return 1

    # Importações locais funcionam quando este arquivo está dentro de src/.
    from sintatico import analisar

    arvore_sintatica = analisar(str(entrada))
    if arvore_sintatica is None:
        print("Não foi possível desenhar: corrija os erros léxicos/sintáticos primeiro.", file=sys.stderr)
        return 1

    if args.tipo == "sintatica":
        raiz_visual = parse_tree_para_visual(arvore_sintatica, arvore_sintatica.parser)
        tipo_titulo = "Árvore sintática (Parse Tree)"
    else:
        from construtor_ast import construir

        arvore_ast = construir(arvore_sintatica)
        raiz_visual = ast_para_visual(arvore_ast)
        tipo_titulo = "Árvore Sintática Abstrata (AST)"

    destino = Path(args.saida) if args.saida else entrada.with_name(
        f"{entrada.stem}.{args.tipo}.svg"
    )
    renderizar_svg(raiz_visual, destino, f"MoleculeDSL — {tipo_titulo}")
    print(f"Árvore gerada: {destino.resolve()}")
    print("Abra o arquivo SVG no navegador para visualizar e ampliar o desenho.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
