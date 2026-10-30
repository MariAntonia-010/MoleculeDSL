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

---

## 29/10/2026 — Fases 5, 7, 8 e 9 do plano do solver

- Fase 5: geração canônica. Cada classe só é emitida na sua rotulação
  representante, sem conjunto de chaves; distribuições de H que nunca são
  representantes são cortadas antes da busca. Conferido contra o CP-SAT.
- Fase 7: `src/eletronico.py`, com pares livres, ligações pi e formas de
  ressonância (`--eletronico`, `--ressonancia`).
- Fase 8: `src/estereo.py`, com centros tetraédricos e duplas E/Z pela
  regra 1a de CIP (`--estereo`). Configuração sempre não especificada.
- Fase 9: `src/complexos.py`, com centros metálicos, ligantes, κ/η/μ,
  estados de oxidação e contagem informativa de elétrons (`--coordenacao`).
- Exemplos novos: `butan_2_ol.mol`, `but_2_eno.mol` e
  `avisos_semanticos/tetracarbonilniquel.mol`.

---

## 30/10/2026 — Eliminação dos limites das fases 5 a 9

Plano em `docs/plano_limites.md`.

- L1: geração ordenada de Read-Faradzev, com a matriz preenchida coluna a
  coluna e prefixos não canônicos cortados. O limite subiu para 12 átomos
  pesados; C₆H₆ dá 217 isômeros em menos de um décimo de segundo.
- L3: filtros com fragmentos em cadeia (`--exigir=O-C=O`).
- L4: busca isolada em processo separado (`--isolar`), CP-SAT com líder
  lexicográfico e sem variáveis de fluxo, e `tests/benchmark_solver.py`.
- L5: ressonância com radicais, ligações coordenadas fixas e `~` fora.
- L6: tautômeros prototrópicos (`--tautomeros`).
- L7: aromaticidade por Hückel (`--aromaticidade`).
- L8: contagem exata de estereoisômeros pelo grupo de automorfismos (meso,
  enantiômeros, centros pseudoassimétricos), P/S com par livre, alenos e
  eixos de biarila declarados; regras CIP 3 a 5 sobre descritores
  declarados.
- L9: comando `stereo` na gramática, com STEREO-001 a STEREO-005.
- Ficam fora, por dependerem de geometria 3D: quiralidade planar e cálculo
  de barreira de rotação.


---

## 30/10/2026 — Auditoria contra o planejamento da próxima etapa

Conferência item por item do documento "MoleculeDSL — Planejamento da
Próxima Etapa" (28/10/2026).

- Pauta 5 (erros do ANTLR): todos os tipos da tabela têm caso de teste;
  SIN-003 e SIN-005 seguem mapeados, sem entrada alcançável, como já estava
  em `docs/erros.md`. Erros dentro de `stereo` ganharam mensagem própria, em
  vez de citar "ligação".
- Pauta 2 (AST): `EstereoDecl` documentado em `docs/ast.md`, snapshot de AST
  e modelo para `exemplos/e_1_2_dicloroeteno.mol`, SVGs em `docs/` e teste
  de tipo, ordem e posição dos nós em todos os exemplos.
- Pauta 1 (semântica): todas as regras têm caso de teste; OCT-001 e RING-004
  estão registrados na especificação.
- Pauta 3 (apresentação): contagem de testes, regras STEREO, seção com
  solver e relatórios químicos e limites atualizados, com saídas reais.
- Pauta 4 (README): estrutura e testes atualizados; os 22 comandos do
  README rodam numa cópia limpa, com `sh gerar.sh` do zero.
- Pendente com o grupo: nomes dos integrantes e da disciplina na capa,
  descrição e tópicos do repositório no GitHub e o aval da Maria para a
  mudança de sintaxe (`stereo`).

---

## 30/10/2026 — Nova página de apresentação

- `docs/apresentacao/` virou um app de página única, com rotas para Início,
  Conteúdo (11 páginas com paginação), Uso, Doc e Playground. Tons neutros
  com destaque lilás, temas claro e escuro, responsivo e sem dependências
  externas. O fundo é uma malha de nós interligados.
- Playground: lexer, parser e verificação semântica em JavaScript (nomes,
  anéis, valências de `regras/valencias.json`) e desenho 3D próprio em
  canvas, por layout de forças com pares livres (a água sai angular). A aba
  "Compilador real" mostra a saída de `src/main.py --modelo` dos exemplos.
- `gerar_apresentacao.py` monta `index.html` a partir de `modelo.html`, com
  saídas reais do compilador, da suíte e do benchmark. Isso corrigiu um
  painel de tokens antigo que mostrava 18 tokens em vez dos 19 reais.
- Capa com a equipe (Geisbelly Victoria, Murilo e Maria Antonia) e a
  disciplina (Linguagens Formais e Compiladores).

---

## 30/10/2026 — Laboratório, tabela periódica e demonstração da tradução

- Laboratório: misturas (moléculas em movimento, com agitação ajustável e
  composição) e reações animadas (síntese da água, combustões, Haber-Bosch,
  HCl, decomposição da água oxigenada), com conferência do balanceamento e
  das ligações rompidas e formadas. As espécies são os programas de
  `exemplos/`; a gramática não mudou.
- Tabela periódica com os 118 elementos de `regras/elementos.json`, modelo
  de Bohr calculado da configuração eletrônica e, para cada elemento, a
  leitura química e a do compilador (token, nó da AST, regra de valência).
- Árvore de tradução em cinco etapas com duas lentes (computação e
  química); botão "Demonstrar tradução" em todos os módulos. O parser do
  navegador passou a montar a árvore sintática regra por regra.
- Benzeno da capa girando mais devagar.

---

## 30/10/2026 — Guia de uso, erro semântico em destaque e simulação montável

- Guia com 11 lições e 21 exemplos (`docs/apresentacao/conteudo_guia.py`).
  O gerador compila cada exemplo com o compilador real e falha se o código
  de saída não for o esperado.
- Playground: erro semântico numa faixa vermelha com código, motivo,
  correção e código de saída; linha marcada no editor; átomo culpado
  pulsando em vermelho no 3D.
- Laboratório: montador de reações (exemplos ou código próprio, coeficientes,
  balanceamento automático) e misturas com componentes em código próprio.
  Espécie inválida bloqueia a simulação com o mesmo destaque de erro.
- Tabela periódica: bancada que monta o código de uma molécula a partir dos
  elementos escolhidos.

---

## 30/10/2026 — Nomenclatura alinhada à IUPAC e tipos de ligação visíveis

Pesquisa: Gold Book da IUPAC (molécula é entidade neutra com mais de um
átomo; "entidade molecular" cobre átomo, molécula, íon e radical; "dativa"
é sinônimo obsoleto de ligação coordenada) e Red Book 2005 (O₂ dioxigênio,
O₃ trioxigênio; cátion monoatômico "sódio(1+)", ânion "cloreto"). O limite
Δχ = 1,7 é convenção didática de Pauling, não fronteira rígida.

- Linguagem: novos tipos `species atom` e `species monatomic_ion` (com
  `charge`). SPEC-001 para um átomo só com ligações, mais de um átomo ou
  carga incompatível; SPEC-003 (aviso) para `molecule` com um átomo só.
  Espécies atômicas não passam pela conferência de valência.
- Exemplos: argônio, hélio e neônio como `atom`; H⁺ como `monatomic_ion`
  "Hydron"; novos sódio(1+), cloreto e óxido; NaCl como `ionic_solid`;
  substâncias elementares diatômicas renomeadas (Dihydrogen, Dioxygen,
  Dinitrogen, Dichlorine, Difluorine, Dibromine).
- Documentação sem o termo "dativa".
- Página: cada ligação com cor e traço do tipo (covalente apolar, polar,
  iônica, coordenada, metálica) e legenda com Δχ; modelo do playground com a
  classificação igual à do compilador; espécies atômicas desenhadas pelo
  modelo de Bohr com a carga; nomes em português (elementos e espécies, com
  nomes estequiométricos da IUPAC); duas lições novas no guia.

---

## 30/10/2026 — Desenho das árvores na página

- Playground: painel "Árvores da linguagem", com a AST e a árvore sintática do
  código atual desenhadas em SVG (layout em árvore, arestas em cotovelo, zoom
  e rolagem), nas lentes de computação e de química. Na AST, os atributos de
  cada nó ficam dentro da caixa, como num registro.
- As etapas 2 a 4 da demonstração da tradução e a ficha de cada elemento da
  tabela periódica (inclusive a bancada) também mostram o desenho.
- A classe raiz da AST passou de `Molecula` para `Especie`, porque a espécie
  pode ser átomo, íon, molécula ou sólido; `Molecula` continua como apelido.

---

## 30/10/2026 — Página sincronizada com a linguagem

- Palavras reservadas, tipos de espécie, operadores e gramática da página
  passam a ser lidos de `gramatica/MoleculeDSL.g4`; a tabela de regras
  semânticas, do README (`docs/apresentacao/linguagem_fontes.py`). O
  compilador do navegador usa as mesmas listas.
- Corrigidas defasagens: SPEC-003 faltava na tabela do Conteúdo, e
  `monatomic_ion` e `atom` faltavam nas palavras reservadas e nos tipos da
  Doc. Doc ganhou o tópico "Regras semânticas"; Conteúdo, a tabela de tipos
  de espécie.
- Teste `apresentacao/sincronizada`: falha se a página não reflete a
  gramática e as regras atuais.

---

## 30/10/2026 — Nome de todo átomo na AST

- A AST mostrava `nome=None` para átomos sem `as`. Agora todo AtomoDecl tem
  nome: o declarado; os gerados pelo multiplicador (`h1…h4`); ou, sem `as`,
  o nome automático que o modelo e as mensagens usam (`O#1 (automático)`),
  guardado em `AtomoDecl.nome_automatico` pelo construtor da AST.
- Vale para `--ast`, para o SVG do `desenhar_arvore.py` e para a página.
  Snapshots de AST, `docs/ast.md` e os SVGs de `docs/` foram atualizados.
- Teste: nenhum exemplo mostra `None` na AST, e o nome automático de cada
  átomo é o mesmo rótulo do modelo.

---

## 30/10/2026 — Guia: construindo um átomo passo a passo

- Nova lição de abertura do guia: os passos para escrever a estrutura mais
  simples (tipo da espécie, nome, chaves, declaração do átomo, compilação,
  visualização), a anatomia do comando `atom Na(+1) as na1` e seis exemplos
  conferidos pelo compilador real, inclusive os erros mais comuns (símbolo em
  minúsculas, elemento inexistente, carga em `species atom`).
- Exemplos de átomo mostram o modelo de Bohr na própria lição; exemplos
  pequenos de todas as lições mostram a AST desenhada.

---

## 30/10/2026 — Estrutura do átomo: núcleo e eletrosfera

Pesquisa e plano em `docs/plano_atomo.md` (notação de nuclídeo da IUPAC,
OpenSMILES, CML, isótopos da CIAAW, Pauli, Aufbau/Madelung com exceções,
Hund, íons de metais de transição).

- Linguagem: número de massa antes do símbolo (`atom 13C`, `2x atom 2H as d`)
  e o comando `configuration` com núcleo de gás nobre opcional
  (`configuration fe [Ar] 3d6`). Tokens novos: `configuration`, `SUBCAMADA`
  e colchetes; `[` deixou de ser erro léxico.
- Semântica: ATOM-001 a ATOM-007 (massa menor que Z, Pauli e l < n, total de
  elétrons, estado excitado, isótopo não natural, configuration fora de
  átomo/íon monoatômico, unpaired contra Hund). Átomos isolados usam a
  configuração medida de `regras/elementos.json` como referência; íons, a
  regra de remoção por maior n.
- `src/atomo.py` e o relatório `--estrutura-atomica` (núcleo, configuração,
  camadas, Hund, diagrama de orbitais). `regras/isotopos.json` (CIAAW, Z ≤ 20).
- Solver: isótopos passam para as soluções e distinguem átomos na
  deduplicação (corrigida a distribuição de H, que fundia 13C com C).
- Página: compilador do navegador com as regras ATOM, Bohr com configuração
  declarada e prótons/nêutrons, isótopos na tabela periódica, lição "Núcleo e
  eletrosfera" no guia e tópico "Estrutura atômica" na Doc.

---

## 30/10/2026 — Átomo, segunda etapa: regra CIP 2, isótopos e termo

- Regra CIP 2 (IUPAC P-92.3) no `--estereo`: a chave de cada ramo é o par
  (esferas de números atômicos, esferas de massas), então a massa só decide
  com a regra 1 esgotada. Átomo sem número de massa usa a massa atômica
  natural (PubChem, novo campo `massa_atomica`). Os automorfismos separam
  isótopos (D só troca com D). No (1-²H)etanol: O > C > ²H > H.
- `regras/isotopos.json` com os 118 elementos, conferido com a tabela da
  CIAAW; elementos sem composição natural têm lista vazia e o ATOM-005 diz
  que todo isótopo deles é radioativo.
- Termo fundamental pelas regras de Hund em `src/atomo.py`
  (`termo_fundamental`), no relatório, na legenda do Bohr e na tabela
  periódica.

---

## 30/10/2026 — Corpus de 300 exemplos

- `corpus/gerar_corpus.py` gera 180 válidos e 120 inválidos ou avisos. As
  moléculas saem de SMILES (parser próprio, hidrogênios pela valência e
  `ring` para cada anel), e os átomos e íons, da configuração de
  referência com núcleo de gás nobre.
- Cada arquivo é conferido pelo compilador. Um válido sem nenhuma
  mensagem e um inválido com a regra planejada; o resto é descartado e
  listado.
- `testar.py` roda o corpus junto com os exemplos curados: 700 testes.

---

## 30/10/2026 — Alimentação de exemplos, rodada 2

- Válidos: (E)-pent-2-eno, (R)-2-clorobutano, (2R,3R)-2,3-diclorobutano,
  cianato, tiocianato, radical metila, aduto água-BF3 e óxido de magnésio.
- Inválidos: E/Z em alceno terminal, R numa dupla, `e` minúsculo, unpaired
  par no CH3, carga total errada no cianato, carga `(1+)` e `=>`.
- VAL-002 não sai quando o `unpaired` declarado explica as ligações que
  faltam (o NO• deixou de avisar). Setas fora de `->` ganharam dica no
  LEX-001.

---

## 30/10/2026 — Alimentação de exemplos, rodada 3

- Válidos: azida, nitrônio, cetena, subóxido de carbono, ácido
  isociânico, glicina zwitteriônica, (Ra)-hexa-2,3-dieno e
  cis-1,3-dimetilciclohexano.
- Inválidos: E num eixo de aleno, núcleo [Ar] no sódio, 2p depois de
  [Ne], zwitterion declarado como íon, azida sem cargas formais, `atom H2`
  e `unpaired -1`.
- Núcleo grande demais tem mensagem própria (ATOM-003, com sugestão do
  gás nobre certo), e subcamada repetida dentro do núcleo diz isso em vez
  de "aparece mais de uma vez". A dica de `atom H2` agora oferece as duas
  leituras: `2x atom H` ou `atom 2H`.

---

## 30/10/2026 — Átomos, íons e sólidos em todos os módulos da página

- Playground: 64 exemplos em dez grupos (`<optgroup>`): átomos isolados,
  íons monoatômicos, substâncias simples, moléculas, anéis, íons
  moleculares, isótopos, estereoquímica, radicais e coordenada, sólidos.
  A lista sai de `GRUPOS_EXEMPLOS` em `gerar_apresentacao.py`.
- Laboratório: qualquer exemplo da página entra em reações e misturas.
  Reações novas com íons (neutralização, autoionização da água,
  protonação da amônia, Na⁺ + Cl⁻) e ozônio. A conservação confere também
  a carga e separa isótopos (²H não conta como H). Misturas prontas: ar
  atmosférico (com o átomo de Ar), salmoura, gases nobres, H₂O e D₂O.
- Fórmula de Hill marca o isótopo (²H2O, ¹³C...) e a lista da mistura e
  as equações mostram a carga.
- Uso: demonstrações de átomo (carbono-13), íon (Fe²⁺) e sólido (NaCl), e
  o comando `--estrutura-atomica`.

---

## 30/10/2026 — Alimentação de exemplos, rodada 4

- Válidos: PF₆⁻, AlCl₄⁻, ácido sulfuroso, tiofosgênio, (E)-diazeno,
  (E)-acetaldoxima, ciclobutadieno e germano (com `bond Ge-H x4`); os oito
  entram nos grupos da página.
- Inválidos: anel fora da ordem do ciclo, `x0`, `x5` com quatro H, P neutro
  com seis ligações num íon, R numa dupla N=N, `charge` em `molecule` e
  nome com maiúscula.
- Mensagens: `charge` numa molécula aponta `species molecular_ion`, e nome
  com maiúscula diz que o começo foi lido como elemento e sugere o nome em
  minúsculas (juntando 'Ag' + 'ua' em 'agua').

---

## 30/10/2026 — O átomo montado: prótons, nêutrons e elétrons

Pergunta da gerente: "o átomo nasce por mágica?". Até aqui, `atom O`
virava só "O#1 carga=+0" no modelo.

- `montar_atomos` (semântica) dá a cada átomo Z prótons, os nêutrons do
  isótopo declarado ou do natural mais abundante e Z − carga elétrons, com
  a configuração declarada ou a do estado fundamental. O isótopo mais
  abundante vem da composição representativa da CIAAW
  (`mais_abundante` em `regras/isotopos.json`).
- `--modelo` mostra `p=8 n=8 (16O, mais abundante) e=8 [He] 2s2 2p4`;
  snapshots do modelo e do solver atualizados (só as linhas de átomo).
- Página: aba Átomos no playground (núcleo, eletrosfera, configuração e se
  é neutro, cátion ou ânion), a aba Modelo com as mesmas contas, e dois
  passos novos na lição "Construindo um átomo".

---

## 30/10/2026 — Alimentação de exemplos, rodada 5 (íons e o átomo montado)

- Bug: `atom H(+2)` era aceito com −1 elétron. Regra nova ATOM-008 (erro):
  a carga positiva vai no máximo até +Z, o núcleo nu (Li³⁺, H⁺).
- Gramática: `configuration na [Ne]` aceita o núcleo sozinho, a notação
  química dos íons isoeletrônicos de gás nobre. Configurações iguais a um
  gás nobre aparecem como o núcleo ([Ne]) no modelo e na página.
- Mensagem: Na⁺ escrito `[Ne] 3s1` agora diz que o 3s1 sobra, em vez de
  sugerir [He]. `--estrutura-atomica` mostra os nêutrons do átomo montado.
- Válidos: Li³⁺, partícula alfa, dêuteron, Al³⁺, S²⁻, Zn²⁺, Ag⁺ e Na⁺ =
  [Ne]. Avisos: trítio e Fe³⁺ tirando 3d antes de 4s. Inválidos: H(+2),
  He(+3), Na⁺ e Cl⁻ com a configuração do átomo neutro, Ca sem a carga no
  átomo.

---

## 30/10/2026 — Alimentação de exemplos, rodada 6 (radicais)

- Válidos: O₂ tripleto (`unpaired 2`), metileno tripleto, NO₂ com cargas
  formais, átomo de H (1s¹) e hidroperoxila; entram no grupo de radicais
  da página. Avisos: ClO₂ (Cl=O) e ligação `~` numa molécula.
- Inválidos: unpaired maior que o número de elétrons, unpaired ímpar no O₂,
  configuration com nome inexistente, núcleo [C] e configuration vazia.
- O NO₂ com N⁺ de três ligações dava erro CARGA-001 mesmo com
  `unpaired 1`. Agora a conta do radical declarado inclui os átomos com
  carga; sem unpaired, o erro continua. "1 elétrons" virou "1 elétron".

---

## 30/10/2026 — Alimentação de exemplos, rodada 7 (combinações e sólidos)

- Válidos: etano com dois ¹³C (`2x atom 13C`), ácido hipocloroso, N com
  `configuration N` pelo símbolo, MgCl₂ e SiO₂ como motivos, cobre
  metálico (Cu₃); os sólidos e o etano entram nos grupos da página.
- Inválidos: `x3` sem H suficientes, sólido iônico com carga sobrando,
  `atom 2x 13C` e `atom (-1)37Cl`, com dicas novas nos dois compiladores.
- O motivo Cu₃ recebia RAD-001 e RING-004. Sólidos e redes não recebem
  mais RAD-001 (a paridade de um motivo não indica radical), e ciclos só
  de ligações `~` não contam no RING-004.

---

## 30/10/2026 — Alimentação de exemplos, rodada 8 (aromáticos com carga)

- Válidos: ânion ciclopentadienila, cátion tropílio, cátion
  ciclopropenila (os três aromáticos pelo `--aromaticidade`) e imidazol;
  entram no grupo de anéis da página. Aviso: ciclopentadienila sem a
  carga, que deixa de ser aromática.
- Inválidos vindos do SMILES: `atom c` minúsculo e a ligação aromática
  `:`. As duas mensagens agora dizem como escrever na DSL (`atom C`,
  simples e duplas alternadas); `atom na` sugere `atom Na`.

---

## 30/10/2026 — Alimentação de exemplos, rodada 9 (relatórios químicos)

Os exemplos novos (cátion alila, enolato, etanimina, 2-piridona e
[Ag(NH₃)₂]⁺) expuseram quatro problemas nos relatórios:

- Ressonância do cátion alila com 1 forma: faltava o carbocátion (C⁺ com 3
  ligações) nos dados. Entrou em `regras/valencias.json`, derivado de C1
  como os outros estados de C3. Para não encher alcenos e benzeno de
  formas C⁺/C⁻, a busca descarta formas com mais octetos incompletos que
  a declarada (contribuintes menores), sem gastar o limite de formas:
  eteno 1, benzeno 2, naftaleno 3, cátion alila 2.
- Imina ⇌ enamina não aparecia: faltava N⁻ com 2 ligações (amideto).
  Entrou nos dados; um carbono só doa H se for saturado (o C sp² da
  piridina daria aleno cíclico), e o H não vai para metais.
- `B(-1) -> N(+1)` passava em silêncio: doador negativo com estado
  inválido antes da doação gera COORD-001 com dica de seta invertida.
- O fixture do COORD-003 (N⁻ com 4 ligações) agora também dá CARGA-001 e
  foi para `invalidos_semanticos`; `radical_amino` ganhou a dica de N(−1).

---

## 30/10/2026 — Alimentação de exemplos, rodada 10 (complexos de metais)

- Válidos: [Cu(NH₃)₄]²⁺ (d⁹, `unpaired 1`), [Co(NH₃)₆]³⁺ e [Fe(CN)₆]⁴⁻; o
  `--coordenacao` dá Cu(II) d⁹ 17 e⁻, Co(III) d⁶ 18 e⁻ e Fe(II) d⁶ 18 e⁻.
  Grupo novo "Complexos de metais" na página, com o [Ag(NH₃)₂]⁺.
- Aviso: [Cu(NH₃)₄]²⁺ sem `unpaired`. Inválidos: Fe(+2) no ferrocianeto
  (estado de oxidação no lugar da carga formal −4) e H como doador.
- COORD-004 sai uma vez por metal, com a quantidade de ligações
  coordenadas, em vez de repetir em cada seta.

---

## 30/10/2026 — Alimentação de exemplos, rodada 11 (resolvedor)

- Casos novos em `resolver/`, só com átomos: HCN, formaldeído, etino,
  hidrazina, metilamina e H₂O₂ têm estrutura única, e a saída fica em
  `.saida.txt`. CH₅ e O₂H₄ não têm estrutura (SOLVER-003). C₃H₈O é
  ambíguo (SOLVER-004), e `--resolver-todas` lista os três isômeros
  (propan-1-ol, propan-2-ol e metoxietano) em `.todas.txt`.
- O resolvedor acertou todos os casos; nenhuma mudança no compilador.

---

## 30/10/2026 — Corpus de 1000 exemplos e documentação dos dois lugares

- `docs/exemplos.md` explica os dois lugares dos exemplos: os curados
  (escritos à mão, usados pela página) e o corpus gerado (`corpus/`, não
  se edita à mão). README e o slide "Testes" da página apontam para ele.
- O gerador passou de 300 para 1000: átomos até Z = 86, todos os isótopos
  naturais até o Kr, 40 íons, 250 moléculas por nomenclatura de classe
  funcional (18 grupos R × 15 grupos X, sem repetir estrutura pela chave
  canônica do grafo) e erros mais variados, inclusive ATOM-008.

---

## 30/10/2026 — Fundo mais lento

- A malha do fundo andava uma fração de pixel por quadro: rápida, e o
  dobro em telas de 120 Hz. Agora a velocidade é medida no tempo (até
  2,5 px/s em qualquer tela), de 3 a 6 vezes mais devagar que antes.

---

## 30/10/2026 — Site no ar

- O Pages foi ativado com a fonte "branch `main`, pasta `/docs`". A raiz
  dava 404, porque a apresentação está em `docs/apresentacao/`;
  `docs/index.html` redireciona para ela.
- Endereço: https://mariantonia-010.github.io/MoleculeDSL/

