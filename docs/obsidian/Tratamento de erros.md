---
tags: [moleculedsl, erros]
---
# Tratamento de erros

Formato: `Erro léxico|sintático na linha L, coluna C: mensagem` (colunas em base 0).

- [[ColetorLexico]]: caractere não reconhecido, texto sem aspas de fechamento, número malformado (`3.`).
- [[ColetorSintatico]]: *esperado X, mas encontrei Y (contexto)*, montado a partir de `getExpectedTokens()`.
- **Erro léxico para tudo** antes do parser: o ANTLR descartaria o caractere e o programa seria aceito.
- **Cascata:** a recuperação do ANTLR pode gerar um 2º erro que é consequência do 1º (`atom_sem_elemento.mol`). A CLI avisa que o primeiro é o confiável. Alternativa: `BailErrorStrategy`.
- Dica especial: [[Armadilha Hx4]].

Implementado em [[erros.py]]. Testes: [[Testes e corpus]].
