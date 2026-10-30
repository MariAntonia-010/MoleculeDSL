# Plano: estrutura do átomo na MoleculeDSL

Até aqui, um átomo na linguagem era só um símbolo de elemento com carga
formal. Este plano aprofunda a estrutura atômica: o núcleo (prótons e
nêutrons, ou seja, o isótopo) e a eletrosfera (configuração eletrônica,
camadas, subcamadas e elétrons desemparelhados). Cada decisão aponta a
fonte usada.

## 1. Pesquisa

### Núcleo: isótopos

- **Notação de nuclídeo:** a IUPAC indica o número de massa A como
  sobrescrito à esquerda do símbolo, como ¹³C ou ²H
  ([IUPAC, Blue Book P-8](https://iupac.qmul.ac.uk/BlueBook/P8.html)).
- **Em formatos de química computacional:**
  - O OpenSMILES escreve o número de massa antes do símbolo, dentro do
    colchete: `[13CH4]`, `[2H+]`, `[238U]`. Sem número, o átomo tem a
    composição isotópica natural
    ([OpenSMILES](https://github.com/timvdm/OpenSMILES/blob/master/opensmiles.asciidoc)).
  - O CML guarda o número de massa no atributo inteiro `isotopeNumber` do
    átomo ([CML](https://repository.data2type.de/CML/v_3/html/el.atom.html)).
- **Isótopos naturais:** a CIAAW/IUPAC publica os isótopos de composição
  natural de cada elemento
  ([CIAAW, Isotopic Abundances](https://www.ciaaw.org/isotopic-abundances.htm)).
  O projeto guarda os dos 118 elementos em `regras/isotopos.json`, conferidos
  com a tabela da CIAAW; Tc, Pm, Po a Ac e os de Z > 92 têm lista vazia (não
  há composição natural).
- **Contagem de partículas:** A = Z + N, então N = A − Z. Um número de
  massa menor que Z daria número negativo de nêutrons.

### Eletrosfera: configuração eletrônica

- **Pauli:** dois elétrons não têm os mesmos quatro números quânticos, então
  uma subcamada de número l comporta 2(2l+1) elétrons: s2, p6, d10, f14. Para
  cada camada n, l vai de 0 a n−1, então não existem 1p, 2d nem 3f
  ([princípio de Pauli](https://openbooks.lib.msu.edu/collegephysics/chapter/the-pauli-exclusion-principle)).
- **Aufbau e regra de Madelung:** dão a ordem de preenchimento (1s, 2s, 2p,
  3s, 3p, 4s, 3d...). Há cerca de 20 exceções medidas, entre elas Cr
  ([Ar] 3d5 4s1), Cu ([Ar] 3d10 4s1), Nb, Mo, Ru, Rh, Pd ([Kr] 4d10), Ag, Pt
  e Au ([Aufbau principle](https://en.wikipedia.org/wiki/Aufbau_principle),
  [tabela de configurações](https://en.wikipedia.org/wiki/Electron_configurations_of_the_elements_(data_page))).
  Por isso a referência do estado fundamental vem dos dados medidos
  (`regras/elementos.json`, PubChem), não da regra.
- **Hund:** em orbitais de mesma energia, os elétrons ocupam um orbital de
  cada vez antes de formar pares. Daí sai o número de elétrons desemparelhados
  (3d6 tem 4) ([regra de Hund](https://ftp.vedantu.com/chemistry/hunds-rule)).
- **Íons:**
  - Um cátion de metal de transição perde os elétrons ns antes dos (n−1)d:
    Fe é [Ar] 3d6 4s2, e Fe²⁺ é [Ar] 3d6
    ([íons monoatômicos](https://wisc.pb.unizin.org/chem109fall2021ver02/chapter/electron-configurations-of-monoatomic-ions/)).
  - Na regra geral, o cátion perde primeiro os elétrons da camada de maior
    n; o ânion ganha elétrons na ordem de Madelung.

## 2. Decisões de linguagem

### 2.1 Número de massa no `atom`

```text
atom 13C            // carbono-13
2x atom 2H as d     // dois deutérios, d1 e d2
atom 37Cl(-1)       // cloreto de cloro-37
```

O número vem antes do símbolo, como na notação da IUPAC e no OpenSMILES.
Sem número, o átomo tem a composição isotópica natural.

**Gramática:**

```text
atomo : MULTIPLICADOR_ATOMO? ATOM INTEIRO? IDENT carga? (AS NOME)?
```

### 2.2 Comando `configuration`

```text
configuration c [He] 2s2 2p2
configuration na1 1s2 2s2 2p6 3s1
```

O comando cita o átomo e lista as subcamadas ocupadas. O núcleo de gás nobre
entre colchetes é opcional. Na gramática entram três tokens novos:
`CONFIGURATION` (`configuration`), `SUBCAMADA` (`[1-7][spdf][0-9]+`) e os
colchetes.

```text
configuracao : CONFIGURATION referencia nucleo? SUBCAMADA+
nucleo       : '[' IDENT ']'
```

A configuração descreve um átomo isolado ou um íon monoatômico. Dentro de uma
molécula os elétrons ficam em orbitais moleculares, e a configuração atômica
deixa de valer.

## 3. Regras semânticas novas

| ID | Regra | Severidade |
|---|---|---|
| ATOM-001 | número de massa menor que o número atômico (nêutrons negativos) | erro |
| ATOM-002 | subcamada impossível (l ≥ n), acima da capacidade de Pauli ou repetida | erro |
| ATOM-003 | total de elétrons da configuração diferente de Z − carga | erro |
| ATOM-004 | configuração válida, mas diferente do estado fundamental de referência (estado excitado) | aviso |
| ATOM-005 | isótopo fora da lista de isótopos naturais da CIAAW (radioativo ou artificial, como ¹⁴C) | aviso |
| ATOM-006 | `configuration` fora de `atom` ou `monatomic_ion`, átomo inexistente ou configuração repetida | erro |
| ATOM-007 | `unpaired` diferente do número de elétrons desemparelhados pela regra de Hund | aviso |

A referência do estado fundamental de um átomo neutro é a configuração de
`regras/elementos.json`. A de um íon é derivada dela: o cátion perde elétrons
da camada de maior n primeiro (ns antes de (n−1)d), e o ânion ganha na ordem
de Madelung.

## 4. Compilador

- **AST:** `AtomoDecl` ganha `massa`, e há um nó novo, `ConfiguracaoDecl`
  (átomo, núcleo, subcamadas).
- **Modelo:** `Atomo` ganha `massa` e `configuracao`. `--modelo` mostra `A=13`
  quando o número é declarado.
- **`src/atomo.py`:** concentra a química do átomo:
  - expandir o núcleo de gás nobre;
  - validar as regras de Pauli e de l < n;
  - calcular o estado fundamental de átomos e íons;
  - aplicar a regra de Hund;
  - desenhar o diagrama de orbitais.
- **Opção `--estrutura-atomica`:** para cada átomo mostra:
  - Z, A, prótons, nêutrons e elétrons;
  - a configuração (declarada ou de referência), as camadas e os elétrons
    de valência;
  - os desemparelhados e o diagrama de orbitais (↑↓).
- **Solver:** `configuration` entra como comando inválido na entrada do
  solver (SOLVER-001), como `bond` e `stereo`. O número de massa passa para as
  soluções.
- **Dados:** `regras/isotopos.json`, com a fonte (CIAAW) registrada.

## 5. Página

- **Playground:** o compilador do navegador lê o número de massa e a
  configuração, aplica as regras ATOM, e o modelo de Bohr usa a configuração
  declarada, com prótons e nêutrons no núcleo.
- **Tabela periódica:** isótopos naturais de cada elemento, notação
  de nuclídeo e exemplos `atom 13C` e `configuration`.
- **Guia:** a lição "Construindo um átomo" ganha o núcleo (isótopo) e a
  eletrosfera (configuração, Pauli, Aufbau, Hund), com exemplos conferidos
  pelo compilador real, inclusive os erros novos.
- **Doc:** tópico "Estrutura atômica". As tabelas de regras e a gramática se
  atualizam sozinhas pelo gerador.

## 6. Testes

- Fixtures válidos: carbono-13, deutério, configuração completa e com núcleo,
  Cr com a exceção real, Fe²⁺.
- Um fixture inválido para cada regra de erro e um de aviso para cada regra
  de aviso.
- Testes unitários de `src/atomo.py`: expansão, Pauli, referência de íons e
  Hund.
- O teste de sincronia da página cobre as palavras e regras novas.

## 7. Segunda etapa (entregue)

- **Regra CIP 2 com isótopos** (IUPAC P-92.3): a regra 1 é aplicada inteira
  ignorando isótopos; só no empate o número de massa decide, em ordem
  decrescente ('³H > ²H > ¹H (ou H)' e '⁸¹Br > Br > ⁷⁹Br'). O exemplo do
  bromo mostra que o átomo sem número de massa conta com a massa atômica
  natural; ela vem da PubChem (`massa_atomica` em `regras/elementos.json`).
  A duplicata de ligação múltipla ou de anel recebe a massa do átomo
  duplicado. A simetria (automorfismos) também separa isótopos, então
  CHD(CH₃)OH tem um centro e CD₃CH(OH)CH₃ também
  ([IUPAC P-92.3](https://iupac.qmul.ac.uk/BlueBook/P9.html)).
- **Isótopos de todos os elementos:** a lista de `regras/isotopos.json` foi
  conferida automaticamente com a tabela da CIAAW (84 elementos com isótopos
  naturais, todos iguais).
- **Termo espectroscópico fundamental** (²S⁺¹L_J) pelas três regras de Hund:
  S máximo, L máximo e J = |L − S| com a subcamada menos que meio cheia ou
  L + S com mais. Com várias subcamadas abertas, os spins se somam e J segue
  a subcamada de maior l que não está meio cheia. Conferido com os termos
  medidos de 26 elementos (C ³P₀, O ³P₂, Cr ⁷S₃, Fe ⁵D₄, Nb ⁶D₁/₂, Gd ⁹D₂,
  U ⁵L₆...). É uma aproximação: o Ce dá ³H₄ pelas regras, e o medido é ¹G₄
  ([termo espectroscópico](https://en.wikipedia.org/wiki/Term_symbol)).
  Aparece no `--estrutura-atomica`, na legenda do modelo de Bohr e na ficha
  da tabela periódica.

## 8. Fora do escopo

- Orbitais moleculares e termos de estados excitados além do de menor
  energia de cada configuração.
