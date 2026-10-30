# Plano para eliminar os limites das fases 5 a 9

Estado: todos os itens L1 a L9 estão implementados e testados em
`testar.py` (caso `solver/limites` e os arquivos `stereo` das pastas de
exemplos).

Este plano parte dos limites registrados ao fim das fases 5, 7, 8 e 9 do
`plano_solver.md`. Cada item diz o limite, a decisão e como fica testado.
Quando um limite vem da própria química (e não do compilador), o item
diz isso e o compilador passa a explicar o motivo na saída, em vez de
calar.

## L1. Poda canônica no meio da busca (fase 5)

**Limite.** O teste de representante só rodava com a estrutura completa.

**Decisão.** Geração ordenada no estilo Read-Faradzev. As arestas entre
átomos pesados passam a ser decididas coluna a coluna da matriz de
adjacência: (0,1), (0,2), (1,2), (0,3), (1,3), (2,3), ... Assim, as
arestas entre os k primeiros átomos formam um prefixo do vetor. Se a
rotulação completa é a menor da sua órbita, o subgrafo dos k primeiros
átomos também é o menor entre as permutações desses k átomos: uma
permutação que o diminuísse, estendida pela identidade, diminuiria o
vetor inteiro. Então, ao fechar cada coluna, um prefixo que não é
canônico corta todo o ramo.

**Consequências.**
- O limite de átomos pesados sobe de 8 para 12.
- A representante de cada classe muda, porque a ordem do vetor mudou.
  As classes continuam as mesmas, e os testes comparam conjuntos de
  chaves canônicas.

**Testes.** Mesmas contagens de antes (C4H8 5, C5H10 10, C3H6O 9 ...),
comparação com o CP-SAT e o C7H16 com 9 isômeros.

## L2. Integração com Surge, MAYGEN e nauty

**Decisão.** Com a L1, o motivo da integração (desempenho) fica coberto
dentro do projeto e sem dependência nativa. O CP-SAT ganha quebra de
simetria (L4) pelo mesmo critério. Nenhum binário externo é exigido.

## L3. Fragmentos de uma ligação só nos filtros

**Decisão.** `--exigir` e `--proibir` aceitam cadeias, como `O-C=O` e
`C=C-C=C`. A cadeia é um caminho com átomos distintos e casa em
qualquer um dos dois sentidos.

## L4. Isolamento, benchmarks e simetria do CP-SAT

**Decisões.**
- `SolveRequest(isolate=True)` e `--isolar` rodam a busca num processo
  separado. Esse processo é encerrado no tempo limite, mesmo se estiver
  preso numa chamada nativa.
- O CP-SAT recebe as mesmas distribuições de H já ordenadas
  (`hydrogens_sorted`) e uma restrição lexicográfica entre átomos
  gêmeos, que têm o mesmo elemento, a mesma carga e a mesma quantidade
  de H. As variáveis de fluxo saem: elas faziam o CP-SAT repetir a mesma
  estrutura para cada fluxo possível. A conexão passa a ser conferida no
  callback, e só a rotulação canônica é aceita.
- `tests/benchmark_solver.py` mede os dois backends numa lista fixa de
  fórmulas.

## L5. Ressonância sem radicais e sem ligações coordenadas ou metálicas

**Decisões.**
- **Radicais.** Cada átomo pode ter um elétron desemparelhado. As formas
  mantêm o total de elétrons desemparelhados da forma declarada, o que
  cobre o deslocamento do radical (alila, NO2).
- **Coordenadas.** A ligação `->` fica fixa: ela não muda de ordem e
  suas pontas guardam o estado declarado como estado permitido. As
  demais ligações da molécula variam normalmente.
- **Metálicas.** As arestas `~` e os átomos metálicos ficam fixos e
  fora da troca de ordens. O relatório diz que o motivo `~` não tem
  ressonância de Lewis.

## L6. Tautômeros

**Decisão.** Nova opção `--tautomeros`, para tautomeria prototrópica. O H
sempre sai de um heteroátomo ou chega a um: saltos de carbono para carbono
são deslocamentos sigmatrópicos, não tautomeria. O
H sai de um átomo doador (heteroátomo ou carbono) e a base conjugada
passa pelas formas de ressonância. O H volta em cada átomo que fica com
carga negativa. As estruturas são deduplicadas pela chave canônica do
grafo com ordens e cargas. Isso cobre deslocamentos 1,3 e 1,5:
ceto-enol, imina-enamina e amida-ácido imídico.

## L7. Aromaticidade

**Decisão.** Nova opção `--aromaticidade`, pela regra de Hückel sobre os
ciclos do grafo.
- **Ciclos testados.** Os ciclos de uma base de ciclos mínimos e as
  fusões entre ciclos vizinhos.
- **Contribuição de cada átomo do ciclo:**
  - 1 elétron pi se tem ligação dupla dentro do ciclo;
  - 0 se a ligação dupla é para fora do ciclo, ou se é cátion com
    orbital vazio;
  - 2 se tem par livre e não tem ligação dupla;
  - sem orbital p (o ciclo não é conjugado) caso contrário.
- **Classificação.** 4n+2 elétrons é aromático, 4n é antiaromático, e
  o resto não é aromático.
- **Hipótese de planaridade.** A regra supõe o ciclo plano. Ciclos com
  mais de 8 átomos e anulenos de 4n elétrons saem marcados com essa
  hipótese explícita, porque podem dobrar e escapar da regra.

## L8. Estereoquímica completa a partir da constituição

**Decisões.**
- **Contagem por simetria.** O compilador enumera as configurações dos
  candidatos e as agrupa pelo grupo de automorfismos do grafo, com os H
  recolhidos como rótulo. Isso dá:
  - o número exato de estereoisômeros, já descontando as formas meso;
  - quais configurações são meso;
  - os pares de enantiômeros;
  - quais candidatos são de fato estereogênicos.

  Exemplos: ácido tartárico (3 estereoisômeros, 1 meso),
  1,4-dimetilciclohexano (cis e trans, ambos aquirais) e
  metilciclohexano (nenhum elemento estereogênico).
- **Centros pseudoassimétricos.** São candidatos com dois ramos de mesma
  constituição que contêm outros elementos estereogênicos. Recebem
  descritor r/s. Quando os dois ramos iguais são os dois sentidos de um
  mesmo anel (1,4-dimetilciclohexano), a configuração é declarada por
  cis/trans entre dois átomos do anel.
- **Átomos com par livre.** Fósforo, enxofre e arsênio com três vizinhos
  e um par livre (sulfóxidos e fosfinas) viram candidatos tetraédricos.
  O par livre conta como o substituinte de menor prioridade. O
  nitrogênio continua fora, porque inverte rápido.
- **Quiralidade axial.**
  - Alenos e cumulenos: com número par de ligações duplas acumuladas, a
    quiralidade é axial (Ra/Sa); com número ímpar, é E/Z.
  - Biarilas (atropisomeria): dependem da barreira de rotação, que o
    grafo não informa. Só entram quando declaradas, com aviso de que a
    barreira não é verificada.
- **Regras CIP.**
  - 1a: segue como antes.
  - 3 (Z > E), 4 (semelhante antes de diferente) e 5 (R > S): desempatam
    ramos de mesma constituição usando os descritores declarados.
  - 2 (massa atômica): fica de fora, porque a linguagem não tem isótopos
    e nunca pode haver empate que ela resolveria.

## L9. Sintaxe para declarar a configuração

**Decisão.** Novo comando, retrocompatível:

```
stereo c2 R          // centro: R, S (ou r, s para pseudoassimétricos)
stereo c2=c3 Z       // ligação dupla: E, Z
stereo c2 Sa         // aleno, pelo átomo central: Ra, Sa
stereo c1-c7 Ra      // eixo de biarila declarado (atropisomeria)
stereo r1 r4 trans   // configuração relativa de dois centros do mesmo anel
```

**Semântica.**

| Código | Situação | Tipo |
|---|---|---|
| STEREO-001 | O átomo ou a ligação não é elemento estereogênico | erro |
| STEREO-002 | O descritor não combina com o tipo do elemento | erro |
| STEREO-003 | Descritor repetido para o mesmo elemento | erro |
| STEREO-004 | Descritor r/s depende de vizinhos sem configuração declarada | erro |
| STEREO-005 | Eixo de biarila declarado sem verificação da barreira | aviso |

**Saída.** Com a configuração declarada, `--estereo` mostra o
estereoisômero, diz se ele é quiral, aquiral ou meso, e mostra o
descritor do enantiômero.

## O que segue fora, por ser limite químico e não do compilador

- **Quiralidade planar** (ferrocenos substituídos, ciclofanos). Depende
  da geometria 3D, que a linguagem não descreve.
- **Barreiras de rotação.** O compilador não calcula se uma biarila é
  atropisômera. A declaração existe justamente para o usuário informar
  isso.
