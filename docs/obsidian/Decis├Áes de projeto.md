---
tags: [moleculedsl, decisoes]
---
# Decisões de projeto

| # | Decisão | Estado |
|---|---|---|
| 1 | `bond` aceita símbolo (`H`) e nome (`c1`) | aplicada |
| 2 | `4x atom H as h` → nome vira prefixo; sintaxe aceita, semântica expande | aplicada (regra do `xN` pendente) |
| 3 | Ligação metálica só como `~`; bloco `metal {}` descartado | aplicada |
| 4 | Uma molécula por arquivo | aplicada |
| 5 | Carga `atom N(+1)`; o `-` reaproveita `LIGACAO` | aplicada |
| 6 | Gramática combinada, rules `atomo`/`ligacao`/`anel` | aplicada |
| 7 | Erro léxico interrompe antes do parser | nova |
| 8 | Colunas em base 0 | nova |
| 9 | Leitura com `utf-8-sig` | nova |

**Aguardando o grupo:** a ampliação da linguagem (`=`, `#`, `->`, `~`, carga, `as`, `ring`) reverte a exclusão de ligações duplas/triplas da especificação antiga e ainda não foi aprovada (ver `DIARIO.md`).
