---
tags: [moleculedsl, analise]
---
# Análise dos planos

Texto completo: `docs/analise_planos_e_implementacao.md`.

**Confirmado na prática:** colisões `x4`/`NOME`, `4x`, `->` vs `-`, palavras-chave vs `NOME` ([[Tokens e colisões]]).

**Não previsto no plano sintático:** [[Armadilha Hx4]]; lexer do ANTLR segue após erro; cascata de erros; coluna base 0 vs 1; BOM do Windows ([[Tratamento de erros]]).

**Contradições no plano semântico** ([[Pendências semânticas]]):
1. `xN` "só vale para elementos" vs `bond n1-h x4` nos exemplos.
2. O mesmo nome (`h1`) pode ser átomo ou prefixo de grupo.
3. `bond H-O` com dois H: a qual H cada linha se refere?

Ver [[Decisões de projeto]].
