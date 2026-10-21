---
tags: [moleculedsl, lexer, armadilha]
---
# Armadilha `Hx4`

`IDENT : [A-Z][a-z]?` aceita qualquer par maiúscula+minúscula. Então `bond C-Hx4` vira `C`, `-`, **`Hx`**, `4`, e o parser falha em `4`.

A mensagem agora inclui a dica: *"'Hx4' foi lido como o elemento 'Hx' seguido de 4 ... separe com espaço: 'H x4'"*.

- Caso de teste: `invalidos_sintaticos/colado_hx4.mol` (linha 4, coluna 14)
- Implementação: `_dica_elemento_colado` em [[erros.py]], usada por [[ColetorSintatico]]
- Consequência de projeto: o lexer **não valida elementos**; `Xx` passa. Isso é o ELEM-001 da semântica ([[Pendências semânticas]]).
