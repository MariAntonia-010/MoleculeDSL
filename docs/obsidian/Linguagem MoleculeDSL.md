---
tags: [moleculedsl, linguagem]
---
# Linguagem MoleculeDSL

DSL para descrever moléculas simples: quais átomos existem e como se ligam, sem coordenadas 3D. Um arquivo = uma molécula. Especificação completa: `docs/especificacao.md`.

```text
molecule "Ammonium" {
    atom N(+1) as n1
    4x atom H as h
    bond n1-h x4
}
```

| Recurso | Sintaxe | Regra do parser |
|---|---|---|
| Átomo | `atom O` | `atomo` |
| Quantidade | `4x atom H` | `atomo` (`MULTIPLICADOR_ATOMO`) |
| Carga formal | `atom N(+1)`, `atom O(-1)` | `carga`, `sinal` |
| Nome / grupo | `atom O as o1`, `4x atom H as h` | `atomo` |
| Ligação simples, dupla, tripla | `-`, `=`, `#` | `ligacao`, `operador` |
| Coordenada | `n1->hp` | `operador` |
| Metálica | `na1~na2` | `operador` |
| Repetição | `bond C-H x4` | `ligacao` (`REPETICAO_LIGACAO`) |
| Anel | `ring c1 c2 c3` | `anel` (mínimo 3 nomes) |
| Comentário | `// ...` | ignorado pelo lexer |

Ver [[Gramática]], [[Tokens e colisões]]. Fora do escopo: aromaticidade, ressonância, isótopos, 3D.
