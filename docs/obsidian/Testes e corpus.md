---
tags: [moleculedsl, testes]
---
# Testes e corpus

`python testes/rodar_testes.py` → **96 verificações**. Manifesto: `testes/esperados.json`.

| Pasta | Qtde | Espera |
|---|---|---|
| `exemplos/` | 20 | aceito |
| `invalidos/` | 8 | erro **léxico** com linha/coluna |
| `invalidos_sintaticos/` | 36 | erro **sintático**: linha, coluna, trecho, qtde de erros |
| `invalidos_semanticos/` | 12 | **aceito pelo parser**; o ID do erro semântico está no nome (`__ELEM-001`) |

Também confere: AST de exemplos-chave, código de saída da CLI, e se algum `.mol` ficou sem expectativa.
Validado por mutação: quebrar um valor esperado ou a regra `anel` faz o executor falhar.

Os dois arquivos do usuário `coordenada.mol` e `metalica.mol` chegaram vazios (RAR truncado); o manifesto os ignora enquanto estiverem vazios.
Executor: [[rodar_testes.py]]. Ver [[Pipeline do compilador]].
