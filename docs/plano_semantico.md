# Plano de implementação: análise semântica da MoleculeDSL

Este plano estende a linguagem (ligações duplas e triplas, carga formal, átomos com nome, anéis, ligações coordenada e metálica) e define a análise semântica.
Ficam fora do escopo: aromaticidade e visualização 3D.

Base das regras: separar a gramática (a estrutura é válida?) da semântica (a molécula é quimicamente válida?). As regras químicas ficam em arquivos de dados, não no código. O octeto é tratado como heurística, não como lei universal.

## Linguagem final

| Recurso | Sintaxe |
|---|---|
| Ligação simples, dupla, tripla | `-`, `=`, `#` |
| Ligação coordenada (dativa) | `->` (do doador para o receptor) |
| Ligação metálica | `~` (o bloco `metal { ... }` ficou de fora, ver decisão 3 do `plano_sintatico.md`) |
| Carga formal | `atom N(+1)`, `atom O(-1)` |
| Átomos com nome | `atom O as o1` |
| Anel | `ring c1 c2 c3 ...` |

Exemplo:

```text
molecule "Ciclohexano" {
    atom C as c1
    atom C as c2
    ...
    bond c1-c2
    ring c1 c2 c3 c4 c5 c6
}
```

## Marcos

### M1: Linguagem e parser
- Lexer com tokens novos para `= # -> ~`, carga, `as` e `ring`.
- Trocar `lexer grammar` por `grammar` combinada, com regras de parser em minúsculas.
- Gerar com `-visitor`.
- Atualizar `especificacao.md` e `DIARIO.md`, registrando a reversão da exclusão de ligações duplas e triplas. Alterações futuras no contrato da linguagem exigem decisão do grupo.

### M2: Dados químicos (`regras/*.json`)
- Elementos: número atômico, elétrons de valência, valências múltiplas (N: 3 e 5; S: 2, 4 e 6), eletronegatividade e tipo (metal, ametal, semimetal).
- `elementos.json` concentra os dados periódicos; `valencias.json` reúne
  valências, cargas conhecidas e ordens de ligação; os limites informativos
  de eletronegatividade ficam em `classificacao_ligacoes.json`.

Feito em parte: `regras/valencias.json` tem só o que o levantamento e a pesquisa aprofundada sustentam. São as valências de H, B, C, N, O, F, P, S e Cl, a valência expandida de Cl ligado só a F ou O, cargas formais conhecidas e a ordem de cada tipo de ligação molecular. Cl, Br e I em ordem múltipla geram aviso; P e S são aceitos conforme soma de ordens. Valências gerais de Be, Al, Si e metais de transição continuam sem regra determinística.

### M3: Modelo interno
Grafo molecular: átomos (id, elemento, carga) e arestas (ordem ou tipo, e direção quando coordenada). Anéis ficam como ciclos marcados.

Implementado em `src/modelo.py` e `src/semantico.py`. Regra para os símbolos de elemento numa ligação (decisão do grupo): se a molécula tem um só átomo do elemento, a ligação usa esse átomo; se tem vários, cada citação usa o próximo átomo do elemento ainda não citado, na ordem de declaração. Quando todos já foram citados, é erro (STRUCT-004) e é preciso usar nomes.

### M4: Semântica estrutural e de valência

| ID | Regra | Severidade |
|---|---|---|
| ELEM-001 | Símbolo de elemento desconhecido | erro |
| STRUCT-001 | `bond` cita átomo inexistente | erro |
| STRUCT-002 | Nomes de átomo duplicados | erro |
| STRUCT-003 | Espécie vazia ou átomo sem ligação (uma espécie de um átomo só não precisa de ligação) | erro |
| STRUCT-004 | Todos os átomos do elemento citado já foram usados em outras ligações | erro |
| STRUCT-005 | Átomo ligado a ele mesmo | erro |
| STRUCT-006 | Mais de uma ligação entre os mesmos dois átomos (inclusive por repetição, como `bond c1-c2 x2`) | erro |
| STRUCT-007 | Quantidade ou repetição fora do intervalo de 1 a 1000 (`0x`, `x0`, `5000x`) | erro |
| STRUCT-008 | Entidade molecular possui componentes desconectados | erro |
| BOND-001 | H ou F excede ligação simples no perfil Lewis clássico | erro |
| BOND-002 | Cl, Br ou I aparece em ligação múltipla formal | aviso |
| VAL-001 | Soma das ordens de ligação acima da valência permitida | erro |
| VAL-002 | Valência incompleta | aviso |
| CARGA-001 | Carga formal inconsistente com a valência | erro |
| CARGA-002 | Soma das cargas formais difere da carga total declarada | erro |
| COORD-001 | Doador sem par livre para ligação coordenada | aviso |
| COORD-002 | Dados insuficientes para conferir o par livre do doador | aviso |
| COORD-003 | Receptor sem espaço eletrônico para receber o par | aviso |
| COORD-004 | Dados insuficientes para conferir o receptor | aviso |
| METAL-001 | Ligação metálica envolve participante fora de um bloco metálico | aviso |
| METAL-002 | Aresta `~` não valida o comportamento coletivo de um sólido | aviso |
| RAD-001 | Contagem eletrônica ímpar sem `unpaired` | aviso |
| RAD-002 | Paridade ou quantidade de `unpaired` incompatível | erro |
| SPEC-001 | Tipo da espécie incompatível com sua declaração | erro |
| SPEC-002 | Grafo finito representa apenas motivo de estrutura estendida | aviso |

Carga formal = elétrons de valência − elétrons não ligantes − ordem total de ligação.

A forma `species` declara o tipo da espécie. `molecular_ion` exige carga
total explícita; `molecule` e os sólidos têm carga total zero. A forma
legada `molecule "Nome"` continua aceita sem conferir soma global, para não
reinterpretar arquivos antigos.

Situação: todas as regras da tabela estão implementadas e têm caso de teste. `OCT-001` foi removida por decisão do grupo: para os elementos com dados, o octeto/dueto já é refletido pelas regras de valência; para os demais, não há fonte suficiente para uma regra independente.

Detalhes da implementação:
- As regras são conferidas em etapas, e cada etapa só roda se a anterior não deu erro, para não aparecerem erros em cascata: estrutura, depois STRUCT-003, depois BOND-001, depois valência e carga.
- BOND-001 fica restrita a H e F, cujo dueto/octeto fornece limite seguro no
  perfil Lewis clássico. Cl, Br e I em ligação múltipla geram BOND-002,
  porque espécies hipervalentes e representações formais impedem uma
  proibição universal. P e S continuam sujeitos à soma de valência e a
  avisos contextuais.
- A coordenada conta como ordem 1. Arestas metálicas não somam ordem; outras ligações do mesmo átomo continuam sendo conferidas.
- Átomo neutro acima da valência: se a soma bate com uma carga da tabela C3, é CARGA-001 com a sugestão da carga (ex.: N com 4 ligações → `N(+1)`); senão, VAL-001.
- Átomo neutro abaixo da valência: é só aviso (VAL-002), porque pode ser um radical (D5). Se a soma bate com uma carga conhecida, o aviso sugere a carga.
- Átomo com carga: CARGA-001 se a soma não bate com a tabela C3. Carga fora da tabela não é conferida.
- A soma das cargas (C2) não é conferida, porque a linguagem não declara a carga total da molécula.

### M5: Tipos de ligação

Implementado em parte:

- Ligações são classificadas pela diferença de eletronegatividade como covalente apolar, covalente polar ou iônica. Os limites padrão 0,4 e 1,7 ficam em `regras/classificacao_ligacoes.json`; o resultado é informativo e aparece em `--modelo`.
- Elemento sem eletronegatividade na fonte produz `não classificada`. Não se usa a regra "metal + ametal = sempre iônica".
- O doador de uma ligação coordenada é conferido pela contagem de elétrons derivada de C4. A falta de par livre gera COORD-001; a falta de dados, COORD-002.
- Para H, He e elementos do segundo período, o receptor é conferido pela capacidade de dueto/octeto antes da doação. Falta de espaço gera COORD-003. Períodos posteriores geram COORD-004, pois expansão de valência e orbitais disponíveis exigem dados que a base não possui.
- Ligações metálicas são identificadas no modelo e mantidas como informação de referência. Todo `~` gera METAL-002, pois uma aresta não valida o comportamento coletivo do sólido; METAL-001 acrescenta o aviso de participante não metálico. A aresta não soma ordem, mas outras ligações do mesmo átomo continuam sendo verificadas.

### M6: Anéis
Detectar ciclos no grafo e validar que a lista do `ring` forma um ciclo conectado, sem átomos repetidos.

Implementado em `src/semantico.py`:

| ID | Regra | Severidade |
|---|---|---|
| RING-001 | Átomo repetido na lista do `ring` | erro |
| RING-002 | Dois átomos vizinhos na lista (ou o último e o primeiro) não estão ligados | erro |
| RING-003 | O mesmo anel declarado mais de uma vez, mesmo começando de outro átomo ou na ordem inversa | erro |
| RING-004 | O grafo contém ciclo independente sem declaração `ring` | aviso |

`RING-004` usa o posto cíclico do grafo (`arestas - vértices + componentes`) para comparar a quantidade de ciclos independentes com os anéis declarados. O aviso não bloqueia a compilação.

### M7: Solver

Implementado para soluções únicas com até 24 átomos totais e oito pesados. O
solver distribui H antes da matriz pesada, busca ordens de 1 a 3 que
satisfaçam as valências confirmadas e exige um grafo conectado. Casos de
referência: H₂O, CO₂, N₂ e NH₄⁺.

`--resolver-todas` enumera até dez estruturas não equivalentes para fórmulas
pequenas. A deduplicação permite permutar átomos do mesmo elemento e carga;
C₂H₄O produz três alternativas formais.

- `SOLVER-001`: entrada já tem ligações/anéis, está vazia ou excede o limite;
- `SOLVER-002`: falta valência confirmada;
- `SOLVER-003`: nenhuma estrutura satisfaz as regras;
- `SOLVER-004`: existem múltiplas estruturas.

C₆H₁₂ já entra no backend por ter seis átomos pesados; sua enumeração é
truncada no limite padrão. A escolha química entre alternativas continua
sendo responsabilidade do usuário, que pode restringir a busca com filtros
objetivos (`--aneis`, `--ligacoes-multiplas`, `--exigir`, `--proibir`). O
plano completo do solver está em `docs/plano_solver.md`.

### M8: Erros, testes e documentação
- Relatório no formato `Erro semântico [ID] na linha X, coluna Y: mensagem`, com código de saída diferente de zero para erros. Avisos não bloqueiam.
- Um exemplo válido e um inválido por regra (`invalidos_semanticos/`).
- Script que roda todos os exemplos e compara exatamente mensagem, ordem e
  código de saída.
- Atualizar README, especificação e slides.

## Ordem sugerida
M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8, fechando M1 a M5 antes de tocar em M6 e M7.

## Riscos e pendências
- Um modelo cristalino para sólidos permanece aberto. A enumeração assistida tem filtros objetivos; fragmentos maiores ficam para depois.
- O enunciado e o prazo da disciplina ainda não foram conferidos contra este plano.
- Mudanças de sintaxe alteram o contrato do projeto e precisam de decisão do grupo.

## Fora do escopo
Aromaticidade e visualização 3D.
