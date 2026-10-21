---
tags: [moleculedsl, ast]
---
# AST

Todo nó guarda `Pos(linha, coluna)` em base 0, para as mensagens `Erro semântico [ID] linha X`.

| Nó | Campos |
|---|---|
| [[Molecula]] | `nome` (sem aspas), `comandos` |
| [[AtomoDecl]] | `elemento`, `multiplicador` (1 se omitido), `carga` (int com sinal), `nome` |
| [[LigacaoDecl]] | `origem`, `operador`, `destino`, `repeticoes` (1 se omitido) |
| [[AnelDecl]] | `nomes` |
| [[Referencia]] | `texto`, `eh_nome` (nome de átomo ou símbolo de elemento) |
| [[Operador]] | `SIMPLES`, `DUPLA`, `TRIPLA`, `COORDENADA`, `METALICA` |

A expansão de `4x atom H as h` (para `h1..h4`) **não** é feita aqui; é da semântica ([[Pendências semânticas]]).
Construída por [[ConstrutorAST]]; impressa por `formatar()` (`--ast`) e `imprimir_arvore()`.
