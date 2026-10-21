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
- Atualizar `especificacao.md` e `DIARIO.md`, registrando a reversão da exclusão de ligações duplas e triplas. Combinar com a Maria antes de abrir PR.

### M2: Dados químicos (`regras/*.json`)
- Elementos: número atômico, elétrons de valência, valências múltiplas (N: 3 e 5; S: 2, 4 e 6), eletronegatividade e tipo (metal, ametal, semimetal).
- Arquivos separados para ordens de ligação aceitas e cargas comuns.

### M3: Modelo interno
Grafo molecular: átomos (id, elemento, carga) e arestas (ordem ou tipo, e direção quando coordenada). Anéis ficam como ciclos marcados.

Implementado em `src/modelo.py` e `src/semantico.py`. Regra para os símbolos de elemento numa ligação (decisão do grupo): se a molécula tem um só átomo do elemento, a ligação usa esse átomo; se tem vários, cada citação usa o próximo átomo do elemento ainda não citado, na ordem de declaração. Quando todos já foram citados, é erro (STRUCT-004) e é preciso usar nomes.

### M4: Semântica estrutural e de valência

| ID | Regra | Severidade |
|---|---|---|
| ELEM-001 | Símbolo de elemento desconhecido | erro |
| STRUCT-001 | `bond` cita átomo inexistente | erro |
| STRUCT-002 | Nomes de átomo duplicados | erro |
| STRUCT-003 | Molécula vazia ou átomo sem ligação (uma molécula de um átomo só não precisa de ligação) | erro |
| STRUCT-004 | Todos os átomos do elemento citado já foram usados em outras ligações | erro |
| STRUCT-005 | Átomo ligado a ele mesmo | erro |
| STRUCT-006 | Mais de uma ligação entre os mesmos dois átomos (inclusive por repetição, como `bond c1-c2 x2`) | erro |
| STRUCT-007 | Quantidade ou repetição igual a zero (`0x`, `x0`) | erro |
| BOND-001 | Elemento não aceita essa ordem de ligação (`H=O`) | erro |
| VAL-001 | Soma das ordens de ligação acima da valência permitida | erro |
| VAL-002 | Valência incompleta | aviso |
| CARGA-001 | Carga formal inconsistente com a valência | erro |
| OCT-001 | Octeto ou dueto não atendido (exceções conhecidas) | aviso |

Carga formal = elétrons de valência − elétrons não ligantes − ordem total de ligação.

Situação: ELEM-001 e STRUCT-001 a STRUCT-007 estão implementadas. As demais dependem dos dados do M2 e das pendências do `levantamento_quimica.md`. STRUCT-003 só é conferida quando não há outros erros, para não aparecerem erros em cascata.

### M5: Tipos de ligação
- Classificar pela diferença de eletronegatividade: covalente apolar, polar ou iônica. Não usar a regra "metal + ametal = sempre iônica".
- Ligação coordenada: o doador precisa ter par livre e o receptor precisa ter orbital vazio.
- Ligação metálica num modelo separado, porque não é uma molécula discreta.

### M6: Anéis
Detectar ciclos no grafo e validar que a lista do `ring` forma um ciclo conectado, sem átomos repetidos.

### M7: Solver
Para uma entrada só com átomos, montar a estrutura: distribuir ligações, recalcular carga e valência, aceitar ou rejeitar. Casos de teste: H₂O, CO₂, N₂, NH₄⁺ e ciclohexano.

### M8: Erros, testes e documentação
- Relatório no formato `Erro semântico [ID] linha X: mensagem`, com código de saída diferente de zero para erros. Avisos não bloqueiam.
- Um exemplo válido e um inválido por regra (`invalidos_semanticos/`).
- Script que roda todos os exemplos e confere sucesso ou o ID de erro esperado.
- Atualizar README, especificação e slides.

## Ordem sugerida
M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8, fechando M1 a M5 antes de tocar em M6 e M7.

## Riscos e pendências
- Ligação metálica e solver são as partes mais abertas.
- O enunciado e o prazo da disciplina ainda não foram conferidos contra este plano.
- A mudança de linguagem altera o contrato do projeto, então precisa ser combinada com a Maria.

## Fora do escopo
Aromaticidade e visualização 3D.
