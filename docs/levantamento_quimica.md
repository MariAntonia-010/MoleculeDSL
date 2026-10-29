# Levantamento das regras de química para a MoleculeDSL

Este documento lista as regras de química que a análise semântica precisa, com a fonte de cada uma e o grau de certeza. Ele não pretende cobrir "toda a química", e sim o que o compilador de moléculas vai usar (ver `plano_semantico.md`).

Foi feito em 2026-10-14, com busca na web e com os dados da PubChem. Nada aqui vem de memória sem fonte. Quando a fonte não confirma, o item está marcado como pendente.

## Legenda de status

| Status | Significado |
|---|---|
| **FONTE** | Confirmado em fonte citada |
| **CONVENÇÃO** | Fontes divergem; é uma escolha de projeto, que deve ser configurável |
| **DERIVADA** | Consequência direta de uma regra FONTE, mas não aparece pronta em uma fonte única |
| **PENDENTE** | Não confirmei. Precisa de um livro-texto ou da decisão do grupo |

## Qualidade das fontes

- **Fortes:** IUPAC Gold Book e PubChem.
- **Fracas:** várias páginas didáticas e de exercícios (LibreTexts, Pearson, Vedantu, sites de estudo). A própria busca avisou que algumas são de baixa qualidade. Os itens que dependem delas valem como "ensinado em cursos de química geral", e devem ser conferidos num livro-texto de química geral antes de virarem regra definitiva.

---

## A. Dados dos elementos

Arquivo gerado: `regras/elementos.json`, com os 118 elementos.

| ID | Regra | Status | Fonte |
|---|---|---|---|
| A1 | Número atômico, símbolo, nome, bloco (metal, ametal, semimetal etc.) e eletronegatividade vêm da tabela da PubChem | FONTE | [PubChem](https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/CSV) |
| A2 | Os valores de eletronegatividade da fonte coincidem com a escala de Pauling para H (2,2), C (2,55), O (3,44) e F (3,98). A PubChem não diz o nome da escala no arquivo | DERIVADA | PubChem |
| A3 | Gases nobres He, Ne e Ar não têm eletronegatividade na fonte. Regra: sem valor, não classificar a ligação | FONTE | PubChem |
| A4 | Elétrons de valência = elétrons s e p da camada mais externa na configuração eletrônica. Só derivado para os blocos principais (50 elementos). Metais de transição, lantanídeos e actinídeos (68) ficam `null` | DERIVADA | Configuração da PubChem |
| A5 | A coluna de "estados de oxidação" da PubChem **não é valência**. Oxidação e valência são conceitos diferentes e não devem ser misturados | FONTE | [IUPAC: oxidation state](https://goldbook.iupac.org/terms/view/O04365) |
| A6 | A configuração do Og (118) é "predicted" na própria fonte. O valor derivado dele não é medido | FONTE | PubChem |

## B. Valência

| ID | Regra | Status | Fonte |
|---|---|---|---|
| B1 | Definição antiga do Gold Book: número máximo de átomos univalentes que podem se combinar com o átomo. Uma recomendação mais recente da IUPAC define valência como o número de ligações de dois elétrons associadas a um átomo. Esta segunda definição é compatível com "valência = soma das ordens de ligação" | FONTE | [Gold Book V06588](https://goldbook.iupac.org/terms/view/V06588), [IUPAC: definição abrangente](https://iupac.org/comprehensive-definition-of-valence-as-a-quantity/) |
| B2 | Valências típicas de átomos neutros em moléculas orgânicas: H 1, C 4, N 3, O 2, F 1, Cl 1 | FONTE (didática) | [Valences of Common Elements](https://organicchemistrydata.org/reusch/virtualtext/problems/pset-valency) e [apêndice eCampus](https://ecampusontario.pressbooks.pub/orgbiochemsupplement/back-matter/appendix-a/) |
| B3 | P: 3 (PH₃) ou 5 (PCl₅). S: 2 por padrão, e 4 ou 6 em compostos como os de sulfato | FONTE (didática) | mesmas fontes de B2 |
| B4 | Flúor só faz 1 ligação. Os halogênios em geral fazem 1 ligação em moléculas simples | FONTE (didática) | [Pearson: preferências de ligação](https://pearson.com/channels/intro-to-chemistry/learn/jules/10-chemical-bonding/bonding-preferences) |
| B5 | Cl, Br e I podem aparecer com 3, 5 ou 7 ligações em interhalogenados (fórmula XYₙ, com n = 1, 3, 5 ou 7) e em oxoácidos, quando ligados a F ou O | FONTE (didática) | [LibreTexts: tendências dos halogênios](https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Supplemental_Modules_and_Websites_(Inorganic_Chemistry)/Descriptive_Chemistry/Elements_Organized_by_Block/2_p-Block_Elements/Group_17%3A_The_Halogens/0Group_17%3A_Physical_Properties_of_the_Halogens/Halogen_Group_(Group_17)_Trends) |
| B6 | B (boro) com 3 ligações: BF₃ é o exemplo clássico de octeto incompleto, com 6 elétrons ao redor do boro. A fonte não lista "valência 3" do B de forma explícita | DERIVADA | [LibreTexts: exceções ao octeto](https://chem.libretexts.org/Bookshelves/Introductory_Chemistry/Introductory_Chemistry_(CK-12)/09:_Covalent_Bonding/9.11:_Exceptions_to_the_Octet_Rule) |
| B7 | Valências de Be, Al, Si, Br e I como átomos neutros comuns, e de qualquer elemento fora de H, C, N, O, F, Cl, P, S | PENDENTE | Não confirmei |

## C. Carga formal

| ID | Regra | Status | Fonte |
|---|---|---|---|
| C1 | Carga formal = elétrons de valência − elétrons não ligantes − (elétrons ligantes ÷ 2) | FONTE | [Pearson](https://pearson.com/channels/general-chemistry/learn/jules/ch-9-bonding-molecular-structure/formal-charge?isTpi=Y), [RevisionDojo](https://www.revisiondojo.com/blog/formal-charge-formula-ib-chemistry) |
| C2 | A soma das cargas formais de todos os átomos deve ser igual à carga total da espécie | FONTE | mesmas fontes de C1 |
| C3 | Ligações por átomo quando a carga formal muda: N⁺ com 4 ligações e sem par livre; O⁺ com 3 e 1 par; O⁻ com 1 e 3 pares; C⁻ com 3 e 1 par; B⁻ com 4 e sem par | DERIVADA | Aplicação de C1 (a busca confirmou que não há uma tabela única publicada) |
| C4 | Elétrons não ligantes de um átomo neutro com ordem total de ligação *b*: V − *b* (resulta de C1 com carga formal 0) | DERIVADA | Álgebra de C1 |

## D. Octeto

| ID | Regra | Status | Fonte |
|---|---|---|---|
| D1 | A regra do octeto é uma heurística, não uma lei. O compilador deve tratá-la como aviso, nunca como erro absoluto | FONTE (didática) | [LibreTexts](https://chem.libretexts.org/Bookshelves/Introductory_Chemistry/Introductory_Chemistry_(CK-12)/09:_Covalent_Bonding/9.11:_Exceptions_to_the_Octet_Rule) |
| D2 | Hidrogênio busca dueto (2 elétrons) | FONTE (didática) | mesma fonte |
| D3 | Octeto incompleto: elementos como Be e B podem ficar com 4 e 6 elétrons ao redor | FONTE (didática) | mesma fonte |
| D4 | Octeto expandido: só para átomos do período 3 em diante. C, N e O (período 2) não expandem | FONTE (didática) | mesma fonte |
| D5 | Moléculas com número ímpar de elétrons (radicais, como NO e NO₂) não fecham octeto para todos os átomos | FONTE (didática) | mesma fonte |

## E. Ordem de ligação

| ID | Regra | Status | Fonte |
|---|---|---|---|
| E1 | Na teoria de ligação de valência, a ordem formal de ligação é o número de pares de elétrons compartilhados entre os dois átomos numa estrutura de Lewis. Simples = 1, dupla = 2, tripla = 3 | FONTE | [Gold Book BT07005](https://goldbook.iupac.org/terms/view/BT07005) |
| E2 | Ligação dupla = 1 sigma + 1 pi. Tripla = 1 sigma + 2 pi | FONTE (didática) | [LibreTexts: ligações múltiplas](https://chem.libretexts.org/Courses/Widener_University/CHEM_176%3A_General_Chemistry_II_(Fischer-Drowos)/14%3A_Advanced_Theories_of_Covalent_Bonding/14.04%3A_Multiple_Bonds) |
| E3 | Ligações pi p–p são comuns nos elementos do período 2 (C, N, O) por causa do tamanho. S e P fazem ligações pi por sobreposição p–d, que é descrita como um modelo de ensino simplificado | FONTE (didática) | [Vedantu: p pi d pi](https://www.vedantu.com/iit-jee/p-pi-d-pi-bonds) |
| E4 | H e halogênios fazem só ligação simples | FONTE (didática) | [Pearson](https://pearson.com/channels/intro-to-chemistry/learn/jules/10-chemical-bonding/bonding-preferences) |
| E5 | Existe ordem de ligação fracionária (média ponderada das estruturas de ressonância). A MoleculeDSL só trabalha com ordens inteiras, então ressonância fica sem representação | FONTE | [Gold Book BT07005](https://goldbook.iupac.org/terms/view/BT07005) |
| E6 | Lista exata de elementos que aceitam dupla e tripla além de C, N, O, S e P | PENDENTE | Não confirmei |

## F. Classificação do tipo de ligação por eletronegatividade

| ID | Regra | Status | Fonte |
|---|---|---|---|
| F1 | A classificação em apolar, polar e iônica usa a diferença de eletronegatividade (Δχ). Os limites **variam entre fontes**: a versão mais comum usa menos de 0,4 (apolar), de 0,4 a 1,7 (polar) e acima de 1,7 (iônica). Outras usam 0,5, 1,9, 2,0 ou 2,2. Os valores de fronteira também mudam de lado conforme o autor | CONVENÇÃO | [Pearson](https://www.pearson.com/channels/gob/textbook-solutions/timberlake-14th-edition-9781292472249/ch6-ionic-and-molecular-compounds/calculate-the-electronegativity-difference-and-classify-each-of-the-following-bo-1), [Socratic](https://socratic.com/answers/194854) |
| F2 | As categorias formam um contínuo. Nenhuma ligação é puramente iônica ou covalente, então o resultado é só um guia | FONTE (didática) | mesmas fontes |
| F3 | Por isso: os limites devem ser **parâmetros configuráveis** (padrão 0,4 e 1,7), e o resultado é informativo, nunca erro. Não usar "metal + ametal = sempre iônica" | CONVENÇÃO | decisão de projeto |

## G. Ligação coordenada (dativa)

| ID | Regra | Status | Fonte |
|---|---|---|---|
| G1 | Segundo a IUPAC, é uma ligação covalente em que os dois elétrons vieram de uma só das partes (formação de um aduto entre um ácido e uma base de Lewis). A origem dos elétrons, por si só, não muda o caráter da ligação: depois de formada, não se distingue de uma covalente comum | FONTE | [Gold Book](https://goldbook.iupac.org/terms/view/C01328) |
| G2 | A IUPAC marca "ligação dativa" como obsoleto. Uma página afirma que "coordinate bond" é o termo preferido. Não consegui confirmar isso no Gold Book | PENDENTE | [Wikipedia](https://en.wikipedia.org/wiki/Coordinate_covalent_bond), não confirmado |
| G3 | A imagem de "doador com par livre e receptor com orbital vazio" vem de livros didáticos, não da IUPAC. Exemplo clássico: NH₃ doando para BF₃ | FONTE (didática) | [Science Notes](https://sciencenotes.org/coordinate-covalent-bond-dative-bond/) |
| G4 | Consequência para o compilador: o `->` conta como uma ligação de 2 elétrons na valência e na carga formal. Em NH₃→BF₃, isso dá N com 4 ligações (N⁺) e B com 4 ligações (B⁻), coerente com C3 | DERIVADA | G1 + C1 + C3 |

## H. Ligação metálica

| ID | Regra | Status | Fonte |
|---|---|---|---|
| H1 | Não encontrei no Gold Book uma entrada própria para "ligação metálica" na busca feita | PENDENTE | — |
| H2 | O Gold Book descreve elétrons deslocalizados como não associados a um átomo ou ligação específica, ocupando orbitais estendidos. Descreve os metais como casos de deslocalização extrema por todo o corpo macroscópico | FONTE | [Gold Book: delocalization](https://goldbook.iupac.org/terms/view/D01583) |
| H3 | Consequência: ligação metálica não é uma molécula discreta e não cabe em "ordem de ligação" nem em "valência" por átomo. Como tratar isso na linguagem é uma **decisão do grupo**, sem regra química confirmada para validar | PENDENTE | — |

## I. Anéis

| ID | Regra | Status | Fonte |
|---|---|---|---|
| I1 | Não pesquisei regras químicas específicas de anéis (tensão de anel, tamanhos de anel estáveis). O que o plano prevê para `ring` é validação de **grafo** (é um ciclo conectado, sem átomo repetido), não regra de química | PENDENTE | — |

## J. O que ficou de fora do levantamento

- **Química de gases nobres:** não pesquisei compostos de gases nobres. Na fonte, He, Ne e Ar não têm eletronegatividade, mas Xe tem (2,6). A valência de elétrons derivada dos gases nobres é o número de elétrons da camada externa (2 para He, 8 para os demais), e isso não diz nada sobre quantas ligações eles fazem.
- **Metais de transição, lantanídeos e actinídeos:** a valência não é derivada automaticamente (68 elementos), e eu não pesquisei como tratá-los.
- **Aromaticidade e 3D:** fora do escopo do projeto.
- **Isômeros, estereoquímica, geometria molecular, polaridade da molécula inteira e energia de ligação:** não pesquisei e não estão no plano.

## K. Decisões e confirmações pendentes

1. Confirmar B2 a B6 num livro-texto de química geral. As fontes usadas são didáticas.
2. Definir valência de Be, Al, Si, Br e I (B7).
3. **Decidido:** limites de F1 em 0,4 e 1,7, mantidos em arquivo de configuração.
4. Decidir se S e P podem fazer ligação dupla e tripla (E3 e E6).
5. **Decidido para esta iteração:** manter ligação metálica como informação de referência e avisar quando `~` envolver participante fora dos blocos metálicos da PubChem; um modelo próprio fica para a continuação.
6. Decidir o que fazer com metais de transição (A4, J).

## Resumo do que o compilador pode validar hoje com fonte

- Soma das ordens de ligação por átomo, contra a valência permitida (B1 a B4).
- Carga formal e soma das cargas (C1, C2).
- Octeto e dueto por meio das regras de valência existentes; não há uma regra `OCT-001` separada.
- Elementos que só aceitam ligação simples (E4).
- Doador e receptor na ligação coordenada, com contagem de elétrons (G1, G4).
- Classificação da ligação por Δχ, informativa (F1).
