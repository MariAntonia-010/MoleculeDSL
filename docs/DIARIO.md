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
- ~~Validar se a lista do `ring` forma um ciclo (M6).~~ Feito no mesmo dia: regras RING-001 (átomo repetido), RING-002 (átomos vizinhos sem ligação, inclusive o fechamento do anel) e RING-003 (anel declarado duas vezes), com 4 casos novos em `invalidos_semanticos/`.
- Decidir se um ciclo que existe no grafo, mas não foi declarado com `ring`, deve gerar aviso.

---

## 21/10/2026 — Valência e carga formal

### O que foi feito

- `regras/valencias.json`, só com as regras do levantamento de química marcadas como FONTE ou DERIVADA (marco M2, em parte).
- Regras BOND-001, VAL-001, VAL-002 e CARGA-001 (resto do M4, menos OCT-001).
- Suporte a avisos: aparecem na saída como `Aviso semântico [...]`, mas não mudam o código de saída.
- 5 casos novos em `invalidos_semanticos/`, a pasta `avisos_semanticos/` com 2 casos e os exemplos do trifluoreto de cloro e do pentacloreto de fósforo.

### Decisões tomadas

- Elemento ou carga sem dado confirmado não é conferido, nem com erro nem com aviso.
- Átomo neutro com valência acima do máximo: se a soma bate com uma carga conhecida (ex.: N com 4 ligações), o erro sugere declarar a carga.
- Átomo neutro com valência abaixo do esperado gera só aviso, porque pode ser um radical. Na primeira versão isso dava erro sugerindo a carga, o que estava errado: um C com 3 ligações pode ser um radical ou um carbocátion, não só C(-1).

### Pendências

- OCT-001 e M5 (tipos de ligação), que dependem dos limites de eletronegatividade (F1) e de decisões do grupo.
- Valências de Br, I e dos demais elementos (B7), ligações múltiplas de S e P (E6) e ligação metálica (H3).

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

---

## 28/10/2026 — Pendências pequenas

### O que foi feito

- O `src/desenhar_arvore.py`, que tinha entrado no repositório sem documentação, foi descrito no README.
- Os SVGs gerados por ele ao lado dos `.mol` (`*.sintatica.svg` e `*.ast.svg`) foram colocados no `.gitignore`.
- A quantidade de átomos e a repetição de ligações passaram a ter limite de 1000 (STRUCT-007). Antes, um número muito grande, como `99999999999x atom H`, fazia a semântica criar um átomo por unidade e o programa travava.
- Caso novo em `invalidos_semanticos/quantidade_acima_do_limite.mol`.

### Decisões tomadas

- O limite é 1000 por declaração, porque a linguagem é para moléculas simples. Ele está na constante `LIMITE_QUANTIDADE` do `src/semantico.py`.
- Uma declaração inválida com quantidade guarda só o prefixo do nome (`h`), e não a lista `h1`, `h2`..., para não precisar percorrer a quantidade inteira.

### Pendências

- Os avisos de valência saem um por átomo. Com `1000x atom O` sem ligações suficientes, são 1000 linhas de aviso. Vale agrupar por declaração, como já é feito no STRUCT-003.

---

## 28/10/2026 — Consolidação de erros, AST e tipos de ligação

### O que foi feito

- Erros léxicos e sintáticos passaram a usar objetos estruturados, IDs
  (`LEX-*` e `SIN-*`) e limite de dez mensagens por fase.
- Testes automáticos para arquivo inexistente, pasta `gerado/` ausente e
  limite de erros. A variável `MOLECULEDSL_GERADO` permite testar uma pasta
  alternativa sem apagar o parser local.
- AST tipada com `TipoReferencia`, união `Comando`, snapshots de quatro
  exemplos e geração de SVG validada para todos os exemplos.
- Classificação informativa de ligações por diferença de eletronegatividade,
  com limites configuráveis em `regras/classificacao_ligacoes.json`.
- Conferência do par livre do doador em ligações coordenadas. A validação do
  orbital vazio no receptor continua pendente por falta de dados.
- Avisos `VAL-002` de átomos equivalentes passaram a ser agrupados por
  declaração e resultado.
- Snapshots de `--modelo` cobrem ligações apolar, polar, iônica e metálica.

### Decisões preservadas

- Nenhum dado químico novo foi inventado; `elementos.json` e
  `valencias.json` continuam limitados ao levantamento.
- A classificação por eletronegatividade é informativa e não usa a regra
  simplificada "metal + ametal".
- OCT-001, ciclo sem `ring`, modelo químico de ligação metálica e solver não
  foram decididos nesta etapa.

---

## 29/10/2026 — Decisões da próxima etapa semântica

### Decisões do grupo

- `OCT-001` foi removida. Octeto e dueto já são refletidos pelas regras de
  valência para elementos com dados; uma regra separada duplicaria avisos.
- Ciclos independentes no grafo sem declaração `ring` passaram a gerar o
  aviso `RING-004`.
- Ligação metálica continua informativa nesta iteração e servirá de
  referência para uma validação semântica própria na continuação.
- O solver foi adiado explicitamente para a próxima iteração.

### Implementação

- `RING-004` compara o posto cíclico do grafo
  (`arestas - vértices + componentes`) com a quantidade de anéis declarados.
- Novo caso `avisos_semanticos/ciclo_sem_ring.mol`; avisos não alteram o
  código de saída.

---

## 29/10/2026 — Validação informativa de ligação metálica

- Criado `regras/ligacoes_metalicas.json`, que lista os blocos metálicos
  exatamente como aparecem na tabela da PubChem.
- `METAL-001` avisa quando o operador `~` envolve pelo menos um elemento
  classificado fora desses blocos.
- A regra é aviso porque H3 não sustenta tratar ligação metálica como ligação
  de uma molécula discreta. Átomos envolvidos em `~` continuam fora da soma
  de valência.
- `exemplos/sodio_metalico.mol` permaneceu inicialmente sem aviso; a revisão
  aprofundada posterior substituiu essa decisão por `METAL-002`.

---

## 29/10/2026 — Receptor da ligação coordenada

- `COORD-003` avisa quando o receptor do primeiro ou segundo período já
  atingia dueto/octeto antes de receber o par eletrônico.
- `COORD-004` avisa que faltam dados para receptores de períodos posteriores,
  evitando inferir expansão de valência ou orbitais disponíveis.
- O aminoborano continua válido: o B tinha seis elétrons ao redor antes da
  doação e espaço para receber o par do N.
- Casos novos cobrem receptor sem espaço e receptor sem dados suficientes.

---

## 29/10/2026 — Mensagens esperadas completas

- `testar.py` deixou de aceitar apenas o início das mensagens.
- Todas as linhas `// esperado:` foram materializadas com a saída completa do
  compilador.
- A comparação agora detecta mudanças em IDs, linha, coluna e explicação,
  mantendo também a ordem e o código de saída.
- Arquivos fora de UTF-8 e com caracteres invisíveis foram preservados em
  bytes durante a migração.

---

## 29/10/2026 — Revisão aprofundada das regras químicas

- A pesquisa foi consolidada em
  `docs/pesquisa_quimica_aprofundada.md`, priorizando IUPAC, NIST, PubChem e
  OpenStax.
- Foi confirmado que bonding number, valência, carga formal, estado de
  oxidação e número de coordenação não podem compartilhar uma única tabela.
- BrF₃, BrF₅, IF₅ e IF₇ mostram que Cl/Br/I não possuem teto universal de
  uma ligação.
- `BOND-001` ficou restrita a H/F; Cl/Br/I em ordem múltipla agora geram o
  aviso `BOND-002`.
- A mensagem de `COORD-003` passou a assumir explicitamente que é resultado
  do modelo dueto/octeto, não prova física da inexistência de orbital.
- Participar de `~` não desativa mais a verificação de outras ligações do
  átomo; o caso de regressão combina C–H e C~Fe.

### Ajuste após a revisão

- Todo uso de `~` agora gera `METAL-002`, deixando explícito que uma aresta
  do grafo não valida um sólido metálico.
- `METAL-001` continua como diagnóstico complementar de composição.
- `testar.py` passou a aceitar exemplos válidos com avisos esperados, e o
  exemplo do sódio registra o novo aviso sem sair com erro.

---

## 29/10/2026 — Tipos de espécie, carga total e radicais

- Novo cabeçalho `species`, mantendo `molecule "Nome"` por compatibilidade.
- Tipos: `molecule`, `molecular_ion`, `ionic_solid`, `covalent_network` e
  `metallic_solid`.
- `molecular_ion` exige `charge`; CARGA-002 compara a carga total com a soma
  das cargas formais dos átomos.
- `unpaired N` representa elétrons desemparelhados. RAD-001 avisa sobre
  contagem ímpar não declarada; RAD-002 rejeita paridade incompatível.
- STRUCT-008 rejeita múltiplos componentes em entidades moleculares
  explicitamente tipadas.
- SPEC-002 deixa claro que sólidos e redes são apenas motivos finitos no
  grafo atual.
- Ressonância não ganhou uma marca superficial: fica documentada até existir
  modelo de pares livres, elétrons pi e formas contribuintes.

---

## 29/10/2026 — Solver de estruturas únicas

- Adicionada a opção `--resolver` e o módulo `src/solver.py`.
- A busca usa valências confirmadas, ordens de 1 a 3 e conectividade.
- O solver só retorna uma estrutura quando a solução é única.
- Casos positivos: H₂O, CO₂, N₂ e NH₄⁺.
- Fórmula sem solução, fórmula ambígua, entrada com ligações e estruturas
  acima de oito átomos recebem `SOLVER-001` a `SOLVER-004`.
- C₂H₄O comprova rejeição por múltiplas estruturas; C₆H₁₂ permanece para uma
  etapa futura de enumeração e seleção assistida.

### Enumeração controlada

- `--resolver-todas` enumera até dez soluções não equivalentes.
- Permutações de átomos com o mesmo elemento e carga são deduplicadas.
- C₂H₄O resulta em três alternativas formais, incluindo uma estrutura
  cíclica; o compilador exibe todas e não escolhe por estabilidade.

---

## 29/10/2026 — Solver modular e hidrogênios pré-distribuídos

- `src/solver.py` foi migrado para o pacote `src/solver/`, mantendo a fachada
  pública usada pelo `main.py`.
- Criados contratos `SolveRequest`, `SolveResult` e `SolveSummary`, com
  status conclusivos e digest do perfil químico.
- Hidrogênios são distribuídos canonicamente antes da busca no grafo pesado.
- A canonicalização pesada inclui quantidade de H e evita permutar os H
  explicitamente.
- Limites atuais: 24 átomos totais e oito pesados.
- Corrigida uma falha de completude: limitar candidatos antes da
  canonicalização podia ocultar classes quando os primeiros rótulos eram
  duplicados.
- O oráculo confere contagens conhecidas de CH₄ a C₆H₁₄ e álcoois/éteres
  pequenos.
- C₆H₁₂ passa a ser enumerável; o limite padrão produz status truncado.

---

## 29/10/2026 — Limites e saída estruturada do solver

- `SolveRequest` ganhou deadline e cancelamento cooperativo.
- A busca diferencia `COMPLETE`, `UNSAT`, `LIMIT_REACHED`, `TIMEOUT`,
  `CANCELLED` e `ERROR`.
- A CLI aceita `--max-solucoes`, `--tempo-limite` e
  `--formato=texto|json|jsonl`.
- JSON e JSONL incluem soluções, mensagens, completude, unicidade, backend,
  versão, tempo e digest do perfil químico.
- Testes cobrem limite, deadline, cancelamento e parsing dos dois formatos.

---

## 29/10/2026 — Fases pendentes do plano do solver

- Perfil químico com nome e versão (`perfil` em `regras/valencias.json`),
  expostos no sumário junto do digest.
- Podas seguras antes da busca pesada: soma residual par, átomo pesado sem
  valência residual e capacidade mínima de `n - 1` arestas.
- Entrega em fluxo: `SolveRequest.on_solution` e JSONL escrito à medida que
  as soluções aparecem.
- Filtros objetivos (`--aneis`, `--ligacoes-multiplas`, `--exigir`,
  `--proibir`), iguais nos backends de referência e CP-SAT.
- Testes de invariância sob permutação das declarações, dos filtros, do
  fluxo e das podas; casos para SOLVER-001, SOLVER-002, SOLVER-003 e
  COORD-002.
- Continuam fora: geração canônica (Fase 5), modelo eletrônico (Fase 7),
  estereoquímica (Fase 8), coordenação e sólidos (Fase 9) e worker isolado.
