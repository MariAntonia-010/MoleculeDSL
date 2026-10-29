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
- digest do perfil químico;
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
```

## Fase 0 — Contrato

Implementado:

- `SolveRequest`;
- `SolveResult`;
- `SolveSummary`;
- `COMPLETE`, `UNSAT`, `LIMIT_REACHED`, `TIMEOUT`, `CANCELLED`, `ERROR`;
- unicidade `TRUE`, `FALSE`, `UNKNOWN`;
- schema JSON e digest das regras.

Pendente:

- expor JSON na CLI;
- tempo decorrido;
- deadline e cancelamento;
- versão explícita do perfil químico.

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

Próximas podas seguras:

- soma residual par;
- capacidade global restante;
- impossibilidade de conectar componentes;
- componente fechada antes do fim;
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

Pendente:

- streaming real sem acumular soluções;
- worker isolado para backends nativos.

Busca interrompida nunca pode ser reportada como `UNSAT` ou única.

## Fase 4 — CP-SAT opcional

Escopo:

- até aproximadamente 20 átomos pesados com restrições;
- variáveis de ordem 0 a 3;
- conectividade por fluxo;
- escolha de estado atômico;
- carga total;
- uma, segunda ou K soluções;
- canonicalização externa.

O backend precisa reproduzir o conjunto do oráculo pequeno. OR-Tools será
dependência opcional, não requisito do compilador principal.

## Fase 5 — Geração canônica

Avaliar:

1. integração com Surge/MAYGEN;
2. orderly generation própria por blocos;
3. canonical augmentation com nauty/Traces.

Critério: gerar um representante por órbita durante a construção, em vez de
produzir rótulos duplicados para filtrar no final.

## Fase 6 — Ambiguidade assistida

- filtros objetivos fornecidos pelo usuário;
- fragmentos obrigatórios/proibidos;
- número de ciclos e ligações múltiplas;
- seleção sem ranking oculto;
- exportação de alternativas canônicas.

Ranking de estabilidade só poderá existir com função, dados, validação e
calibração explícitos.

## Fase 7 — Modelo eletrônico

Antes de ressonância:

- pares livres;
- elétrons pi;
- invariantes de formas contribuintes;
- carga total;
- conectividade sigma.

Depois:

- grupos de ressonância;
- percepção configurável de aromaticidade;
- tautomeria como agrupamento opcional.

## Fase 8 — Estereoquímica

Após conectividade:

- elementos estereogênicos;
- R/S e E/Z;
- `specified`, `unspecified`, `unknown`;
- enumeração separada dos grafos constitucionais.

## Fase 9 — Coordenação e sólidos

Módulo separado para:

- metal central e ligantes;
- átomos doadores;
- denticidade e hapticidade;
- pontes;
- carga/estado de oxidação;
- motivos iônicos, covalentes e metálicos.

A regra dos 18 elétrons será no máximo aviso/ranking.

## Referências

- [MAYGEN](https://doi.org/10.1186/s13321-021-00529-9)
- [Surge](https://pmc.ncbi.nlm.nih.gov/articles/PMC9034616/)
- [MOLGEN](https://molgen.de/download/pubs/StructEnumHandbookChemInfAlgo.pdf)
- [enu](https://pmc.ncbi.nlm.nih.gov/articles/PMC9867865/)
- [nauty/Traces](https://users.cecs.anu.edu.au/~bdm/nauty/)
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
