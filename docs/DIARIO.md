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

## 21/10/2026 — Revisão da análise sintática

### O que foi feito

- Revisão do código da branch `feat/sintatico-s1-s2` antes do pull request, com testes de casos que ainda não estavam cobertos: arquivo com BOM, arquivo fora de UTF-8, acentos no nome da molécula, tabulação e variações de espaço no multiplicador e na repetição.
- O BOM no início do arquivo passou a ser ignorado. Antes ele gerava um erro léxico na coluna 0 com um caractere invisível.
- Um arquivo fora de UTF-8 passou a gerar um erro léxico com linha e coluna, em vez de um traceback do Python. A coluna é contada em caracteres, como nos outros erros.
- Sem a pasta `gerado/`, o programa pede para rodar o `sh gerar.sh`, em vez de mostrar um traceback.
- As mensagens de erro léxico passaram a ser em português, como `caractere inválido '@'`, em vez do `token recognition error` do ANTLR.
- Os erros de espaço mais comuns no multiplicador e na repetição (`bond C-Hx4`, `x 4`, `4 x atom`, `4 atom`, `x` sem número, `X` maiúsculo e `x4` fora de um `bond`) ganharam mensagens próprias, em vez de "comando inválido".
- A recuperação de erros do ANTLR não apaga mais o token que começa o comando seguinte (`atom`, `bond`, `ring`, multiplicador ou `}`). Isso resolve o caso registrado na entrada anterior, em que um erro estragava a mensagem da linha de baixo.
- Novos casos de teste: 2 em `exemplos/`, 2 em `invalidos/` e 9 em `invalidos_sintaticos/`. Os casos léxicos antigos passaram a conferir também a mensagem.

### Decisões tomadas

- As mensagens de espaço só aparecem quando o contexto deixa claro o que se queria escrever, por exemplo um número logo depois da segunda referência de um `bond`. Nos outros casos continua a mensagem de comando inválido.
- O `testar.py` lê as linhas `// esperado` ignorando o BOM e os bytes fora de UTF-8, para poder testar esses casos.

### Pendências

- Não há teste automático para a falta da pasta `gerado/`, porque o `testar.py` roda sempre com ela. O caso foi conferido à mão.
