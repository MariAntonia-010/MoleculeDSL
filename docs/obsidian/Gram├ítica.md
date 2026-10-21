---
tags: [moleculedsl, gramatica, antlr]
---
# Gramática (`gramatica/MoleculeDSL.g4`)

Combinada (`grammar MoleculeDSL;`), ANTLR 4.13.2, alvo Python3, gerada com `-visitor`.
O parser responde **"a estrutura é válida?"**; as regras químicas ficam para a semântica ([[Pendências semânticas]]).

```antlr
programa    : molecula EOF ;
molecula    : MOLECULE TEXTO ABRE_CHAVE comando* FECHA_CHAVE ;
comando     : atomo | ligacao | anel ;
atomo       : MULTIPLICADOR_ATOMO? ATOM IDENT carga? (AS NOME)? ;
carga       : ABRE_PAREN sinal INTEIRO FECHA_PAREN ;
sinal       : MAIS | LIGACAO ;
ligacao     : BOND referencia operador referencia REPETICAO_LIGACAO? ;
referencia  : IDENT | NOME ;
operador    : LIGACAO | DUPLA | TRIPLA | COORDENADA | METALICA ;
anel        : RING NOME NOME NOME+ ;
```

- A ordem dos comandos é livre (`bond` pode vir antes de `atom`).
- O `-` de `(-1)` reaproveita `LIGACAO`; o contexto resolve.
- O `REAL` existe no lexer mas nenhuma regra o usa.
- Gerado por `sh gerar.sh`; os visitors usam estes nomes de regra em [[ConstrutorAST]].

Relacionadas: [[Tokens e colisões]], [[AST]].
