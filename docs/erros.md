# Erros da MoleculeDSL

A MoleculeDSL substitui os listeners padrão do ANTLR 4 para que nenhuma
mensagem interna em inglês seja exibida. Os erros são coletados, limitados a
dez por fase e só então apresentados pela interface de linha de comando.

O formato é:

```text
Erro <fase> [<código>] na linha <linha>, coluna <coluna>: <mensagem>
```

As linhas começam em 1 e as colunas em 0, seguindo a convenção do ANTLR.
Erros de entrada, configuração, léxicos e sintáticos encerram o programa com
código 1; erros semânticos e de resolução, com código 2. Avisos não mudam o
código de saída. A análise
sintática não é executada quando há erro léxico, evitando mensagens em
cascata.

## Erros léxicos

| Código | Causa | Exemplo |
|---|---|---|
| `LEX-001` | Caractere que não pertence à linguagem | `atom C @` |
| `LEX-002` | Texto sem aspas de fechamento na mesma linha | `molecule "Agua {` |
| `LEX-003` | Ponto fora de um número real válido | `atom C.` |
| `LEX-004` | Caractere invisível não aceito | espaço de largura zero |
| `LEX-005` | Arquivo com codificação diferente de UTF-8 | arquivo salvo em ISO-8859-1 |

O lexer reconhece esses casos a partir de `LexerNoViableAltException`, antes
que o texto cru `token recognition error` do ANTLR chegue ao usuário.

## Erros sintáticos

| Código | Mecanismo do ANTLR | Significado |
|---|---|---|
| `SIN-001` | inserção, `missing` ou token incompatível | faltou um token obrigatório |
| `SIN-002` | remoção ou `extraneous input` | há um token inesperado ou sobrando |
| `SIN-003` | `NoViableAltException` | nenhuma alternativa da gramática aceita a entrada |
| `SIN-004` | token encontrado é `EOF` | o arquivo terminou antes de a construção ficar completa |
| `SIN-005` | `FailedPredicateException` | um predicado da gramática falhou |

A regra `comando` atual é simples e o ANTLR reporta palavras desconhecidas
como token incompatível (`SIN-002`), sem produzir `NoViableAltException`.
Assim, `SIN-003` está mapeado no listener, mas não tem hoje um caso de entrada
alcançável. A gramática também não usa predicados semânticos; `SIN-005` é
documentado para completar o mapeamento, mas não possui entrada capaz de
produzi-lo. A estratégia `RecuperacaoPorComando`, baseada em
`DefaultErrorStrategy`, mantém inserção, remoção e sincronização, mas impede
que a recuperação descarte o início do comando seguinte. Também é mantido no
máximo um erro por linha para reduzir cascatas.

Os diagnósticos `reportAmbiguity`, `reportAttemptingFullContext` e
`reportContextSensitivity` pertencem ao `DiagnosticErrorListener`. Eles não
são erros de entrada e não são habilitados no modo normal. A gramática não
possui atualmente uma opção de diagnóstico.

## Erros de entrada e configuração

| Código | Causa | Correção |
|---|---|---|
| `ENT-001` | Arquivo solicitado não existe | conferir caminho e nome do arquivo |
| `CFG-001` | Lexer/parser gerados não estão disponíveis | executar `sh gerar.sh` |
| `LIM-001` | Mais de dez erros foram encontrados na mesma fase | corrigir os primeiros erros e executar novamente |

A variável `MOLECULEDSL_GERADO` pode apontar para outra pasta de código
gerado. Ela é usada pelo teste automatizado de `CFG-001`; no uso normal, a
pasta é `gerado/`.

## Erros semânticos e avisos

A análise semântica usa os prefixos `ELEM`, `STRUCT`, `BOND`, `VAL`, `CARGA`,
`COORD`, `METAL`, `RAD`, `SPEC`, `RING`, `STEREO`, `ATOM` e `BLOCK`. A tabela
completa, com a severidade de cada regra (erro ou aviso), está em
[plano_semantico.md](plano_semantico.md), e o resumo está no README.

## Erros de resolução

Usados só com `--resolver` e `--resolver-todas`. Saem com código 2.

| Código | Causa |
|---|---|
| `SOLVER-001` | a entrada já tem ligações, anéis ou outros comandos além de `atom`, está vazia ou passa do limite de 40 átomos (12 pesados) |
| `SOLVER-002` | algum átomo não tem valência confirmada em `regras/valencias.json` |
| `SOLVER-003` | nenhuma estrutura satisfaz as regras |
| `SOLVER-004` | a fórmula admite mais de uma estrutura; declare as ligações ou use `--resolver-todas` |
| `SOLVER-005` | a busca foi interrompida (tempo limite ou cancelamento) antes de provar a unicidade |
| `SOLVER-006` | falha da própria busca: backend desconhecido, erro do backend ou processo isolado que terminou sem resultado |

## Exemplos

```text
Erro léxico [LEX-001] na linha 4, coluna 4: caractere inválido '@'
Erro sintático [SIN-004] na linha 3, coluna 10: esperado '}' para fechar a molécula
```

Os arquivos em `invalidos/` e `invalidos_sintaticos/` registram a saída
esperada em linhas `// esperado:`. O script `python testar.py` confere a
mensagem completa, a ordem e o código de saída.
