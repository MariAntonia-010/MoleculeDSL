# Diário de Desenvolvimento — MoleculeDSL

Este documento registra as principais decisões, alterações e dificuldades encontradas durante o desenvolvimento da MoleculeDSL.

## 09/09/2026 — Definição da linguagem

### O que foi feito

- Escolha do domínio da linguagem.
- Definição da proposta da MoleculeDSL.
- Definição do objetivo e do escopo inicial do projeto.
- Definição das principais construções da linguagem, como `molecule`, `atom` e `bond`.
- Definição inicial dos tokens e da forma de representação de moléculas.
- Elaboração da documentação inicial do projeto.

### Decisões tomadas

Foi decidido criar uma linguagem de domínio específico voltada à descrição de estruturas moleculares simples.

A linguagem foi planejada para permitir a declaração de moléculas, átomos e ligações de forma textual e legível, mantendo um escopo reduzido para facilitar a implementação durante as etapas do projeto.

Também foi definido que a linguagem descreve principalmente a topologia da molécula. A geração de uma representação visual, incluindo uma possível visualização 3D, fica para uma etapa posterior do projeto.

---

## 16/09/2026 — Organização da E2 e repositório

### O que foi feito

- Organização da estrutura do repositório para a etapa E2.
- Criação das pastas `docs`, `gramatica`, `src`, `exemplos` e `invalidos`.
- Criação dos arquivos iniciais necessários para o projeto.
- Envio da estrutura inicial para o repositório Git.
- Adaptação da documentação inicial para o formato de especificação solicitado na E2.
- Organização do arquivo `especificacao.md` seguindo os requisitos da atividade.

### Configuração do ANTLR

Durante a configuração do ANTLR no Windows, a ferramenta inicialmente não conseguiu
identificar automaticamente a versão disponível. Foi definida manualmente a versão
4.13.2, compatível com o runtime Python instalado.

---

## 14/10/2026 — Planejamento da sintaxe e da semântica, e levantamento de química

### O que foi feito

- Correção do `gerar.sh`: final de linha Unix, versão 4.13.2 do ANTLR fixada e `-Xexact-output-dir`, para o lexer ser gerado direto em `gerado/`. O comando do Windows no README recebeu a mesma opção.
- Escrita do plano de análise sintática (`docs/plano_sintatico.md`), já pensando na entrada da semântica: a AST deve guardar linha e coluna de cada nó.
- Escrita do plano de análise semântica (`docs/plano_semantico.md`), em marcos de M1 a M8.
- Levantamento das regras de química (`docs/levantamento_quimica.md`), com a fonte e o status de cada regra: FONTE, CONVENÇÃO, DERIVADA ou PENDENTE.
- Geração de `regras/elementos.json` com os 118 elementos, a partir da tabela periódica da PubChem.
- Abertura do pull request #2 com essas mudanças.

### Decisões tomadas

- A gramática responde se a estrutura é válida na linguagem. As regras químicas ficam na análise semântica, e não na gramática.
- As regras químicas ficam em arquivos de dados (`regras/`), e não escritas direto no código.
- Aromaticidade e visualização 3D ficam fora do escopo.
- Os limites de eletronegatividade que separam ligação apolar, polar e iônica variam entre as fontes. Eles devem ser parâmetros configuráveis, e o resultado é só informativo.
- Valência e estado de oxidação são conceitos diferentes. A coluna de estados de oxidação da PubChem não é usada como valência.

### Propostas que ainda não foram aprovadas

Os planos propõem ampliar a linguagem com ligações duplas (`=`), triplas (`#`), coordenada (`->`) e metálica (`~`), carga formal, átomos com nome e anéis. Isso reverte a exclusão de ligações duplas e triplas da especificação atual. Nada disso foi implementado, e é preciso combinar com o grupo antes.

### Dificuldades encontradas

- O `gerar.sh` do repositório falhava no macOS por causa do final de linha do Windows e da consulta à versão mais recente do ANTLR, que retornava erro HTTP 400.
- Parte das fontes do levantamento de química é didática, e não primária. Os itens que dependem delas precisam ser conferidos num livro-texto.
- Não achei no IUPAC Gold Book uma definição de ligação metálica, então esse ponto ficou pendente.

### Pendências

- A Maria vai fazer o plano de testes.
- Confirmar as valências e as regras marcadas como PENDENTE no levantamento de química.
- Decidir se S e P podem fazer ligação dupla e tripla, como tratar ligação metálica e o que fazer com metais de transição.
- Aprovar ou ajustar a ampliação da linguagem proposta nos planos.

---

## 21/10/2026 — Implementação da análise sintática

### O que foi feito

- Implementação dos marcos S1 a S8 do `plano_sintatico.md`, na branch `feat/sintatico-s1-s2`.
- S1 e S2: a gramática passou a ser combinada (lexer e parser no mesmo `MoleculeDSL.g4`), com os tokens e as regras de ligações dupla, tripla, coordenada e metálica, carga formal, átomos com nome e anéis.
- S3: o `gerar.sh` passou a gerar também o Visitor (`-visitor`).
- S4: `src/sintatico.py`, com mensagens de erro sintático em português para cada regra, com linha e coluna.
- S5: AST com a posição de cada nó (`src/ast_nos.py`), construída por um Visitor (`src/construtor_ast.py`).
- S6: `src/main.py`, que encadeia as etapas, com as opções `--tokens` e `--ast`.
- S7: um exemplo válido por construção nova em `exemplos/`, 14 casos em `invalidos_sintaticos/` e o script `testar.py`.
- S8: gramática em EBNF na especificação e README atualizado.

### Decisões tomadas

- As decisões 1 a 6 do `plano_sintatico.md` foram implementadas como estavam propostas.
- Se houver erro léxico, a análise sintática não roda, para não aparecerem erros em cascata.
- Só é mostrado um erro sintático por linha. Os outros erros da mesma linha quase sempre eram consequência da recuperação de erros do ANTLR.
- Quando falta algo no fim de uma linha, o erro aponta para logo depois do último token dessa linha, e não para o começo da linha seguinte, como o ANTLR faria.
- Na AST, os dois lados de uma ligação e os átomos de um anel guardam a própria posição e se são um elemento ou um nome. Isso vai permitir apontar a coluna exata nos erros semânticos.
- Códigos de saída: 0 sucesso, 1 erro léxico ou sintático e 2 reservado para erro semântico. O `main.py` lê as opções sem o `argparse`, porque ele sai com código 2 quando os argumentos estão errados.
- Cada arquivo inválido diz o erro esperado em linhas `// esperado: ...`, e o `testar.py` confere a mensagem, a linha e a coluna.

### Dificuldades encontradas

- Com a gramática combinada, o ANTLR passou a gerar a classe `MoleculeDSLLexer` em vez de `MoleculeDSL`, e foi preciso ajustar o `lexico.py`.
- A recuperação de erros do ANTLR às vezes "conserta" o programa de um jeito inesperado. Por exemplo, um `atom` sem elemento seguido de `bond H O` na linha de baixo faz o `H` virar o elemento do `atom`, e o erro da segunda linha aparece como comando inválido.

### Pendências

- Combinar com o grupo a ampliação da linguagem antes de abrir o pull request.
- Implementar a análise semântica (`plano_semantico.md`), incluindo a expansão de `4x atom H as h` em `h1` a `h4`, que os exemplos novos já usam.
- Fazer os novos slides.

---

## 21/10/2026 — Início da análise semântica

### O que foi feito

- Modelo interno da molécula em grafo (`src/modelo.py`), marco M3 do `plano_semantico.md`.
- Análise semântica estrutural (`src/semantico.py`), parte do marco M4: ELEM-001 e STRUCT-001 a STRUCT-007.
- O `main.py` passou a rodar a semântica, sai com código 2 em erro semântico e ganhou a opção `--modelo`.
- 13 casos em `invalidos_semanticos/`, um exemplo de molécula de um átomo só (`exemplos/helio.mol`) e o `testar.py` passou a conferir o código de saída de cada pasta.
- Trabalho feito na branch `feat/semantico`, criada a partir da `feat/sintatico-s1-s2`.

### Decisões tomadas

- Símbolo de elemento numa ligação: se há um só átomo do elemento, é ele; se há vários, cada citação usa o próximo átomo ainda não citado, na ordem de declaração. Assim os exemplos da água, do metano e da amônia continuam válidos.
- Regras novas, além das do plano: STRUCT-004 (todos os átomos do elemento já citados), STRUCT-005 (átomo ligado a ele mesmo), STRUCT-006 (ligação repetida entre os mesmos átomos) e STRUCT-007 (quantidade ou repetição zero).
- Uma molécula de um átomo só, como o hélio, não precisa de ligação.
- Os erros semânticos não geram erros em cascata: citar um átomo cuja declaração já deu erro não gera outro erro, e o átomo sem ligação só é conferido quando não há outros erros.
- O exemplo do aminoborano passou a declarar `N(+1)` e `B(-1)`, como indica o levantamento de química (C3 e G4).

### Pendências

- Valência, ordem de ligação, carga formal e octeto (M2, resto do M4 e M5), que dependem das pendências do levantamento de química.
- Validar se a lista do `ring` forma um ciclo (M6).
