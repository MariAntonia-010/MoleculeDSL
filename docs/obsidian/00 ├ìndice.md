---
tags: [moleculedsl, indice]
---
# MoleculeDSL — Índice

Vault do projeto da disciplina de compiladores. Etapa atual: **E3, análise sintática**.

## Linguagem
- [[Linguagem MoleculeDSL]] — o que ela descreve e a sintaxe por recurso
- [[Gramática]] — regras do parser e do lexer
- [[Tokens e colisões]] — como o lexer desempata
- [[Armadilha Hx4]] — o erro mais provável de quem escreve `bond C-Hx4`

## Compilador
- [[Pipeline do compilador]] — léxico → sintático → AST → (semântico)
- [[AST]] — nós tipados com linha e coluna
- [[Tratamento de erros]] — mensagens, cascata, códigos de saída

## Qualidade
- [[Testes e corpus]] — válidos, inválidos léxicos, sintáticos e semânticos
- [[Análise dos planos]] — o que a prática confirmou e o que contradiz o plano
- [[Decisões de projeto]]
- [[Pendências semânticas]] — o que precisa ser decidido antes do M4

## Código (gerado pelo Graphify)
Grafo de chamadas e estrutura de `src/` e `testes/`, em `grafo-codigo/`:
[[main.py]] · [[lexico.py]] · [[sintatico.py]] · [[erros.py]] · [[arvore.py]] · [[construtor_ast.py]] · [[comum.py]] · [[rodar_testes.py]]
Nós mais conectados: [[ConstrutorAST]], [[processar()]], [[tokenizar()]], [[ler_arquivo()]].
Canvas do grafo: `grafo-codigo/graph.canvas`.

> O Graphify cobre só código Python (AST local). A gramática `.g4`, os `.mol` e os `.md` não entram no grafo; por isso as notas de conceito acima foram escritas à mão.
