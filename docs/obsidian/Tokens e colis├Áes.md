---
tags: [moleculedsl, lexer]
---
# Tokens e colisões

Regra do ANTLR: **vence o casamento mais longo; em empate, a regra declarada primeiro.**

| Entrada | Candidatos | Vence | Porque |
|---|---|---|---|
| `atom`, `bond`, `as`, `ring` | palavra-chave, `NOME` | palavra-chave | declarada antes, mesmo tamanho |
| `as1` | `AS`, `NOME` | `NOME` | `as1` é mais longo |
| `x4` | `REPETICAO_LIGACAO`, `NOME` | `REPETICAO_LIGACAO` | declarada antes |
| `4x` | `MULTIPLICADOR_ATOMO`, `INTEIRO`+`NOME` | `MULTIPLICADOR_ATOMO` | mais longo |
| `->` | `COORDENADA`, `LIGACAO` | `COORDENADA` | mais longo |
| `Hx4` | `IDENT 'Hx'` + `INTEIRO` | — | ver [[Armadilha Hx4]] |
| `1.5` | `REAL`, `INTEIRO` | `REAL` | mais longo |

**Nomes reservados:** `molecule`, `atom`, `bond`, `as`, `ring`, e `x` seguido só de dígitos.

Verificado em `invalidos_sintaticos/nome_palavra_reservada.mol` e `nome_reservado_x4.mol` ([[Testes e corpus]]).
