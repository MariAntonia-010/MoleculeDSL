# Plano completo do solver da MoleculeDSL

Baseado na pesquisa de geração constitucional, MAYGEN, Surge, MOLGEN,
nauty/Traces, CP-SAT e nas regras químicas versionadas do projeto.

## Objetivo

Produzir grafos constitucionais corretos dentro de um perfil químico
explícito, distinguindo:

- correção de cada saída;
- completude da enumeração;
- ausência de duplicatas por isomorfismo;
- status conclusivo ou interrompido da busca.

“Todas as estruturas” sempre significa todas as classes sob a equivalência e
o perfil declarados. Não inclui automaticamente estereoisômeros, tautômeros,
formas de ressonância, coordenação metálica ou estabilidade.

## Estado atual

- `--resolver`: exige uma classe canônica única;
- `--resolver-todas`: enumera até dez classes;
- 24 átomos totais e oito pesados;
- H distribuído antes da matriz dos átomos pesados;
- deduplicação exata por permutações que preservam elemento, carga e H;
- status estruturados em `solver.result`;
- nome, versão e digest do perfil químico;
- podas seguras de paridade e conectividade;
- entrega em fluxo das soluções;
- filtros objetivos de anéis, ligações múltiplas e fragmentos;
- oráculo de contagens pequenas no `testar.py`.

## Arquitetura

```text
src/solver/
  __init__.py          fachada compatível
  problem.py           normalização da AST
  result.py            request, summary e status
  chemical_profile.py  regras e digest
  hydrogen.py          distribuições canônicas de H
  canonical.py         identidade estrutural
  backtracking.py      backend de referência
  messages.py          diagnósticos
  serialization.py     JSON versionado
  filters.py           filtros objetivos da Fase 6
```

## Fase 0 — Contrato

Implementado:

- `SolveRequest`;
- `SolveResult`;
- `SolveSummary`;
- `COMPLETE`, `UNSAT`, `LIMIT_REACHED`, `TIMEOUT`, `CANCELLED`, `ERROR`;
- unicidade `TRUE`, `FALSE`, `UNKNOWN`;
- schema JSON e digest das regras;
- JSON na CLI, tempo decorrido, deadline e cancelamento (ver Fase 3);
- versão explícita do perfil químico: o bloco `perfil` de
  `regras/valencias.json` dá nome e versão, e o sumário traz
  `chemical_profile`, `chemical_profile_version` e o digest.

## Fase 1 — Backend de referência

Implementado:

- expansão das declarações de átomos;
- separação entre H e átomos pesados;
- distribuição canônica de H;
- matriz pesada com ordens 0 a 3;
- valências residuais;
- conectividade;
- canonicalização exata;
- limite de soluções.

Podas seguras implementadas em `feasible`, antes da busca pesada, nos dois
backends:

- soma residual par;
- átomo pesado sem valência residual não conecta os demais;
- capacidade mínima: `n` pesados exigem pelo menos `n - 1` arestas.

Ainda possíveis:

- componente fechada antes do fim, durante a busca;
- DBE somente quando o perfil permitir.

Não podar por estabilidade, presença em banco, quantidade de cargas, anéis
pequenos ou preferência por poucas ligações múltiplas.

## Fase 2 — Oráculo e testes

Já conferidos:

| Fórmula | Classes |
|---|---:|
| CH₄ | 1 |
| C₂H₆ | 1 |
| C₂H₆O | 2 |
| C₃H₈O | 3 |
| C₄H₁₀ | 2 |
| C₅H₁₂ | 3 |
| C₆H₁₄ | 5 |

A invariância sob permutação das declarações é conferida em C₂H₆O com três
ordens diferentes de `atom`; os conjuntos de chaves canônicas devem ser
iguais.

Gates obrigatórios:

1. fórmula preservada;
2. carga e paridade preservadas;
3. valências satisfeitas;
4. grafo conectado;
5. chave canônica única;
6. invariância sob permutação das declarações;
7. comparação de conjuntos, não ordem textual.

## Fase 3 — Operação

Implementado:

- `--max-solucoes`;
- `--tempo-limite`;
- `--formato texto|json|jsonl`;
- cancelamento cooperativo;
- status `LIMIT_REACHED`, `TIMEOUT` e `CANCELLED` no contrato estruturado;
- JSON versionado com backend, versão, tempo e digest das regras.

- entrega em fluxo: `SolveRequest.on_solution` recebe cada solução assim que
  ela é encontrada e `SolveResult.solutions` fica vazia; a CLI usa isso em
  `--resolver-todas --formato=jsonl`. No CP-SAT, a entrega acontece ao fim de
  cada busca.

Pendente:

- worker isolado para backends nativos.

Busca interrompida nunca pode ser reportada como `UNSAT` ou única.

## Fase 4 — CP-SAT opcional

Implementado inicialmente:

- variáveis de ordem 0 a 3;
- conectividade por fluxo;
- escolha de estado atômico;
- carga total;
- uma, segunda ou K soluções;
- canonicalização externa.
- distribuição de H antes do modelo CP-SAT;
- deadline, cancelamento e limite de classes;
- comparação diferencial com o backend de referência.

OR-Tools fica em `requirements-solver.txt` e não é requisito do compilador
principal. Antes de ampliar a escala para aproximadamente 20 átomos pesados,
faltam benchmarks, quebra de simetria no modelo e worker isolado.

## Fase 5 — Geração canônica

Opções avaliadas:

1. integração com Surge/MAYGEN: exigiria binário externo ou JVM no caminho
   do compilador e um tradutor do perfil químico; fica para quando a escala
   passar de oito átomos pesados;
2. orderly generation própria por blocos: **implementada** no backend de
   referência;
3. canonical augmentation com nauty/Traces: mesma objeção de dependência
   nativa do item 1.

Implementado em `src/solver/canonical.py` e usado em `backtracking.py`:

- a representante de cada classe é a rotulação de menor vetor (H por átomo,
  ordens das arestas) entre as permutações de átomos de mesmo elemento e
  carga;
- `hydrogens_sorted` descarta, antes da busca pesada, as distribuições de H
  que não crescem dentro de cada grupo, pois nunca são representantes;
- `is_canonical_heavy` testa cada estrutura completa e só emite a
  representante; nenhum conjunto de chaves cresce com a enumeração, o que
  completa o fluxo da Fase 3.

Exatamente uma rotulação de cada classe passa no teste, e a representante
sempre é gerada: os H dela crescem dentro de cada grupo, que é a mesma ordem
exigida por `distributions`. A suíte compara os conjuntos com o CP-SAT, que
ainda deduplica por chave, e confere C₄H₈ (5), C₅H₁₀ (10), C₄H₆ (9),
C₃H₆O (9) e C₃H₉N (4).

Pendente: o teste é feito na estrutura completa. Podar matrizes parciais
(orderly generation de Read-Faradzev) reduziria a busca, mas exige ordenar
o preenchimento por linhas da matriz.

## Fase 6 — Ambiguidade assistida

Implementado em `src/solver/filters.py`:

- filtros objetivos fornecidos pelo usuário (`SolveFilters`);
- fragmentos obrigatórios/proibidos de uma ligação (`--exigir=C=O`,
  `--proibir=C#C`);
- número de ciclos (`--aneis=N`) e de ligações múltiplas
  (`--ligacoes-multiplas=N`);
- seleção sem ranking oculto: o filtro é aplicado antes da deduplicação e do
  limite, e a unicidade de `--resolver` passa a valer dentro do filtro;
- exportação de alternativas canônicas em JSON/JSONL, com os filtros no
  sumário.

Pendente: fragmentos com mais de uma ligação.

Ranking de estabilidade só poderá existir com função, dados, validação e
calibração explícitos.

## Fase 7 — Modelo eletrônico

Implementado em `src/eletronico.py`, com as opções `--eletronico` e
`--ressonancia`:

- pares livres e elétrons não ligantes de cada átomo
  (`elétrons de valência − carga formal − soma das ordens`);
- ligações pi por átomo e elétrons pi da espécie;
- invariantes das formas contribuintes: mesmo esqueleto sigma, mesma carga
  total e, portanto, mesma quantidade de elétrons;
- formas de ressonância: as ordens de 1 a 3 e as cargas formais variam
  dentro dos estados de `regras/valencias.json`, sempre com elétrons não
  ligantes em pares. A forma declarada vem primeiro; as demais são
  ordenadas pela quantidade de átomos com carga, mostrada na saída. Até dez
  formas são exibidas.

Casos conferidos: carbonato (3), benzeno (2), acetato (2), ozônio (2),
água (1) e cianeto (1).

Fora do modelo: ligações coordenadas ou metálicas, radicais e elementos sem
elétrons de valência. Aromaticidade continua fora do escopo
(`plano_semantico.md`); tautomeria muda o esqueleto sigma e por isso não é
ressonância — fica como agrupamento futuro.

## Fase 8 — Estereoquímica

Implementado em `src/estereo.py`, com a opção `--estereo`:

- centros tetraédricos: quatro vizinhos por ligação simples, nenhum par
  livre e quatro substituintes diferentes;
- ligações duplas E/Z: cada ponta com dois substituintes diferentes, ou um
  substituinte e um par livre (C=N); ficam de fora duplas em anéis com menos
  de oito átomos e duplas cumuladas;
- prioridades pela regra 1a de CIP: número atômico esfera a esfera, com
  átomos duplicados para ligações múltiplas e fechamentos de anel;
- como a linguagem não tem sintaxe de configuração, todo elemento aparece
  como não especificado (`unspecified`); `specified` exigiria mudar o
  contrato da linguagem, o que depende de decisão do grupo;
- a enumeração estereoquímica é separada da constitucional: o relatório
  informa o limite de 2ⁿ estereoisômeros.

Fora: regras CIP 2 a 5, descontar formas meso, quiralidade axial e
planar.

## Fase 9 — Coordenação e sólidos

Implementado em `src/complexos.py`, com a opção `--coordenacao`:

- centro metálico: átomo de bloco metálico ligado a não metal;
- ligantes: componentes que sobram ao retirar os metais;
- átomos doadores, denticidade (κ) e hapticidade (η, doadores vizinhos
  entre si);
- pontes (μ): doador ligado a mais de um metal;
- carga do ligante (cargas formais menos a ordem das ligações com metais) e
  estado de oxidação do metal (carga formal mais essa ordem);
- motivos por tipo de ligação: iônica, covalente, coordenada e metálica;
  um sólido só com `~` aparece como motivo metálico, sem centros.

A contagem de elétrons usa o modelo iônico e é só informativa, nunca
aviso. Casos conferidos: Ni(CO)₄ (Ni 0, d10, 18 elétrons), NaCl (Na +1,
Cl −1) e sódio metálico.

## Referências

- [MAYGEN](https://doi.org/10.1186/s13321-021-00529-9)
- [Surge](https://pmc.ncbi.nlm.nih.gov/articles/PMC9034616/)
- [MOLGEN](https://molgen.de/download/pubs/StructEnumHandbookChemInfAlgo.pdf)
- [enu](https://pmc.ncbi.nlm.nih.gov/articles/PMC9867865/)
- [nauty/Traces](https://users.cecs.anu.edu.au/~bdm/nauty/)
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
