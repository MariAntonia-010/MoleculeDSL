# Plano de implementação: análise sintática da MoleculeDSL

Este plano cobre a análise sintática já pensando no que a análise semântica precisa receber (ver `plano_semantico.md`). A sintaxe cobre ligações simples, duplas e triplas, coordenada e metálica, carga formal, átomos com nome e anéis. Aromaticidade e 3D ficam fora.

Princípio: a gramática responde "a estrutura é válida na linguagem?". A semântica responde "é uma molécula quimicamente válida?". O parser aceita tudo o que é bem formado e deixa as regras químicas para a semântica.

## Divisão de responsabilidades

| Exemplo | Sintaxe | Semântica |
|---|---|---|
| `atom Xx` | aceita (forma de IDENT) | ELEM-001, elemento desconhecido |
| `bond H=O` | aceita | BOND-001, ordem não aceita |
| `bond c1-c9` | aceita | STRUCT-001, átomo inexistente |
| `atom O as o1` duas vezes | aceita | STRUCT-002, nome duplicado |
| `bond H-O` antes de `atom H` | aceita (ordem livre) | a semântica coleta as declarações primeiro |
| `bond c1-c2 x2` | aceita | erro: repetição só vale para elementos, não para átomos com nome |
| `bond H O` (sem operador) | erro sintático | não chega |
| `ring c1 c2` (menos de 3) | erro sintático | não chega |

Se houver erro léxico ou sintático, o programa para antes da semântica. Assim não aparecem erros em cascata.

## Decisões (confirmar antes de codificar)

1. **Referências em `bond`:** manter símbolo de elemento (`H`) e aceitar também nome de átomo (`c1`). Isso mantém os exemplos atuais válidos.
2. **Multiplicador com nome:** `4x atom H as h` cria `h1` a `h4` (o nome vira prefixo). A sintaxe só aceita, e a semântica expande.
3. **Ligação metálica:** só o operador `~`. O bloco `metal { }` do plano semântico fica de fora. Ajustar o M1 do `plano_semantico.md`.
4. **Uma molécula por arquivo**, por enquanto.
5. **Carga:** `atom N(+1)` e `atom O(-1)`. O sinal `-` reaproveita o token `LIGACAO`, e o parser resolve pelo contexto.
6. **Gramática combinada** em um só `MoleculeDSL.g4`, como na aula de ANTLR.

## Gramática proposta

```antlr
grammar MoleculeDSL;

// ---------- PARSER ----------
programa   : molecula EOF ;
molecula   : MOLECULE TEXTO ABRE_CHAVE comando* FECHA_CHAVE ;
comando    : atomo | ligacao | anel ;

atomo      : MULTIPLICADOR_ATOMO? ATOM IDENT carga? (AS NOME)? ;
carga      : ABRE_PAREN sinal INTEIRO FECHA_PAREN ;
sinal      : MAIS | LIGACAO ;

ligacao    : BOND referencia operador referencia REPETICAO_LIGACAO? ;
referencia : IDENT | NOME ;
operador   : LIGACAO | DUPLA | TRIPLA | COORDENADA | METALICA ;

anel       : RING NOME NOME NOME+ ;
```

## Marcos

### S1: Estender o lexer
Tokens novos, definidos depois dos já existentes:

| Token | Texto |
|---|---|
| `DUPLA` | `=` |
| `TRIPLA` | `#` |
| `COORDENADA` | `->` |
| `METALICA` | `~` |
| `MAIS` | `+` |
| `ABRE_PAREN`, `FECHA_PAREN` | `(`, `)` |
| `AS`, `RING` | palavras-chave `as`, `ring` |
| `NOME` | `[a-z] [a-z0-9_]*` |

Pontos de atenção, todos de ordem de regras ou de maior casamento:
- Palavras-chave (`molecule`, `atom`, `bond`, `as`, `ring`) vêm antes de `NOME`. Num empate de tamanho vence a regra definida primeiro. Consequência: nenhum átomo pode se chamar `atom`, `bond`, `as` ou `ring`.
- `x4` casa com `REPETICAO_LIGACAO` e com `NOME` com o mesmo tamanho. Vence `REPETICAO_LIGACAO`. Nomes no formato `x` seguido só de dígitos ficam reservados e devem ser documentados.
- `->` ganha de `-` por maior casamento.
- `MULTIPLICADOR_ATOMO` (`4x`) continua ganhando de `INTEIRO` seguido de `NOME`.

### S2: Regras do parser
Escrever as regras acima. Conferir que `exemplos/agua.mol`, `metano.mol` e `amonia.mol` continuam válidos sem mudança.

### S3: Geração e build
- `gerar.sh` gera lexer e parser com `-visitor`, mantendo `ANTLR4_TOOLS_ANTLR_VERSION=4.13.2` e `-Xexact-output-dir`.
- Ferramenta de depuração: `antlr4-parse gramatica/MoleculeDSL.g4 programa -tokens`, ou `-tree` para a árvore.

### S4: Tratamento de erros sintáticos
- Uma classe `ErroSintatico` no estilo do `ErroLexico` de `src/lexico.py`, com linha e coluna.
- Mensagens em português por regra, por exemplo "esperado elemento depois de `atom`".
- Coletar todos os erros possíveis (recuperação do ANTLR), não só o primeiro.
- Códigos de saída: 0 sucesso, 1 erro léxico ou sintático, 2 erro semântico.

### S5: Construção da AST com posições
É a parte que serve à semântica. Um Visitor sobre a parse tree gera nós tipados, todos com `linha` e `coluna`, para as mensagens `Erro semântico [ID] linha X`:

```
Molecula(nome, comandos)
AtomoDecl(multiplicador, elemento, carga, nome, pos)
LigacaoDecl(origem, operador, destino, repeticoes, pos)
AnelDecl(nomes, pos)
Operador: SIMPLES=1, DUPLA=2, TRIPLA=3, COORDENADA, METALICA
```
Normalizações já nesta fase: tirar as aspas do `TEXTO`, converter `carga` em inteiro com sinal, ler o multiplicador como inteiro. A expansão de `4x ... as h` fica na semântica.

### S6: Interface de linha de comando
Um `src/main.py` com etapas encadeadas (léxico, sintático, semântico) e opções `--tokens` e `--ast`. O `lexico.py` atual continua funcionando sozinho.

### S7: Testes
- Válidos: os 3 exemplos atuais e um exemplo novo por construção (`=`, `#`, `->`, `~`, carga, nome, `ring`).
- Inválidos em `invalidos_sintaticos/`:
  - falta `}` ou `{`
  - `molecule` sem nome
  - `atom` sem elemento
  - `bond H O` sem operador
  - `bond H-` incompleto
  - `ring c1 c2` com menos de 3
  - `atom N(1)` sem sinal
  - `4x bond ...`
  - texto depois do `}` (`EOF`)
- Um script confere sucesso ou o erro esperado, com linha e coluna.

### S8: Documentação
Escrever a gramática em EBNF na `especificacao.md`, entrada no `DIARIO.md`, README com o novo fluxo e novos slides.

## Ligação com o plano semântico
S1 a S5 cobrem o M1 e alimentam o M3 do `plano_semantico.md`, porque a AST com posições é a entrada do modelo interno. A ordem sugerida é S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8.

## Riscos
- Colisões entre `NOME`, palavras-chave e `x4`: coberto por testes específicos.
- A mudança de linguagem altera o contrato do projeto, então combine com a Maria antes de abrir PR.
- Enunciado e prazo da disciplina ainda não foram conferidos.
