---
tags: [moleculedsl, pipeline]
---
# Pipeline do compilador

```
arquivo .mol ──ler_arquivo (utf-8-sig)──► texto
   texto ──tokenizar──► tokens + erros léxicos ──(erro? PARA)
   texto ──parsear──► parse tree + erros sintáticos ──(erro? PARA)
   parse tree ──ConstrutorAST──► AST (Molecula)
   AST ──[semântica: futura]──► relatório
```

| Etapa | Código | Observação |
|---|---|---|
| Leitura | [[ler_arquivo()]] | descarta o BOM do Windows |
| Léxico | [[tokenizar()]] em [[lexico.py]] | erro léxico interrompe antes do parser |
| Sintático | [[parsear()]] em [[sintatico.py]] | o ANTLR se recupera e coleta vários erros |
| AST | [[ConstrutorAST]] | normaliza `"4x"`→4, `"+1"`→+1, tira aspas |
| Orquestração | [[processar()]] em [[main.py]] | devolve um [[Resultado]] |

Códigos de saída: `0` ok · `1` léxico/sintático · `2` semântico (futuro) · `3` ANTLR não gerado.
CLI: `python src/main.py arq.mol [--tokens] [--ast] [--arvore]`. Ver [[Tratamento de erros]], [[AST]].
