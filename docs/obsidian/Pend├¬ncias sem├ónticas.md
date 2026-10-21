---
tags: [moleculedsl, semantica, pendencias]
---
# Pendências semânticas (antes do M4)

Casos prontos em `invalidos_semanticos/` (aceitos pelo parser, hoje).

| ID | Regra | Arquivo de teste |
|---|---|---|
| ELEM-001 | elemento desconhecido | `elemento_desconhecido__ELEM-001` |
| BOND-001 | ordem de ligação não aceita (`H=O`) | `ordem_nao_aceita__BOND-001` |
| STRUCT-001 | átomo inexistente | `atomo_inexistente__STRUCT-001`, `elemento_em_minusculo_como_nome__STRUCT-001` |
| STRUCT-002 | nome duplicado | `nome_duplicado__STRUCT-002` |
| STRUCT-003 | molécula vazia / átomo sem ligação | `molecula_vazia__`, `atomo_sem_ligacao__` |
| VAL-001 | valência excedida | `valencia_excedida__VAL-001` |
| CARGA-001 | carga inconsistente | `carga_inconsistente__CARGA-001` |
| M6 | anel desconexo / com repetição | `anel_desconexo__M6`, `anel_repetido__M6` |
| **A definir** | `xN` entre átomos simples | `repeticao_em_nome__A-DEFINIR` |

## A decidir
1. **`xN` com nomes.** Proposta: válido só com um **grupo** de tamanho N; entre átomos simples é erro.
2. **Nome = átomo ou grupo?** `2x atom H as h1` gera `h11`, `h12`. Proposta: classificar nomes e reportar colisão como STRUCT-002; preferir prefixo sem dígito.
3. **Referência por símbolo.** Proposta: consome, na ordem de declaração, o primeiro átomo do elemento ainda sem ligação com o outro lado.
4. `->` conta na valência do doador? (define se `NH4+` é válido)
5. `molecule ""` é erro?

Ver [[Análise dos planos]], [[AST]].
