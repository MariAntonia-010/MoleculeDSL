# Pesquisa química aprofundada para a MoleculeDSL

Pesquisa realizada em 29/10/2026 para revisar as regras semânticas antes de
ampliar `regras/valencias.json`.

## 1. Conclusão executiva

Uma tabela `elemento → valências permitidas` não é uma lei química geral.
Ela mistura conceitos que precisam permanecer separados:

- número de coordenação;
- soma das ordens formais de ligação;
- carga formal;
- estado de oxidação;
- pares livres e elétrons desemparelhados;
- ressonância e ligações multicêntricas;
- fase e tipo da espécie química.

As valências usuais são adequadas como padrão didático e aviso. Elas só
podem virar erro dentro de um perfil explicitamente limitado a estruturas de
Lewis simples, com carga e radical representáveis.

Política recomendada:

1. **Erro:** inconsistência objetiva do modelo, como átomo inexistente,
   ligação duplicada, carga total incompatível quando declarada ou limite de
   segurança.
2. **Aviso:** valência incomum, regra de octeto, hipervalência, heurística de
   eletronegatividade e capacidade coordenante.
3. **Documentação:** fase da matéria, ressonância, aromaticidade, geometria,
   estabilidade e sólidos estendidos.

## 2. Hierarquia das fontes

| Fonte | Força | Uso no projeto |
|---|---|---|
| [IUPAC Gold Book](https://goldbook.iupac.org/) | normativa | definições e separação dos conceitos |
| [IUPAC Blue Book](https://iupac.qmul.ac.uk/BlueBook/P1.html) | normativa | bonding numbers e convenção lambda |
| [NIST Chemistry WebBook](https://webbook.nist.gov/chemistry/) e [CCCBDB](https://cccbdb.nist.gov/) | muito alta | espécies, geometrias e dados experimentais |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | alta | elementos, estruturas, cargas e identificadores |
| [OpenStax Chemistry 2e](https://openstax.org/details/books/chemistry-2e) | alta, didática | Lewis, octeto, sólidos e coordenação |
| LibreTexts universitário | média a alta | exemplos avançados, conferidos por obra |

Fontes didáticas ajudam a escolher mensagens, mas não devem sozinhas criar
proibições universais.

## 3. Conceitos que não podem ser confundidos

### 3.1 Bonding number e valência

A IUPAC define [bonding number](https://goldbook.iupac.org/terms/view/B00703)
como a soma dos equivalentes de ligação a átomos do esqueleto e hidrogênios
ligados. A própria definição dá `SH₂` com 2 e `SH₆` com 6.

A [valência](https://goldbook.iupac.org/terms/view/V06588.html) é uma
definição histórica baseada na quantidade máxima de átomos univalentes que
podem combinar com um átomo ou fragmento. Nenhuma das duas grandezas é
estado de oxidação.

### 3.2 Estado de oxidação

O [estado de oxidação](https://goldbook.iupac.org/terms/view/O04365.html) é a
carga obtida por uma aproximação iônica das ligações heteronucleares. Não
deve ser usado como:

- número de ligações;
- soma das ordens;
- carga formal real;
- limite de valência.

### 3.3 Ordem de ligação

A IUPAC observa que a [ordem de ligação](https://goldbook.iupac.org/terms/view/BT07005)
depende do modelo. Em teoria de ligação de valência, pode ser a média
ponderada das ordens formais das estruturas de ressonância.

Na MoleculeDSL, `-`, `=` e `#` são ordens **formais da representação**. Isso
não afirma que a ordem física seja sempre um inteiro localizado.

### 3.4 Carga formal

A [carga formal](https://goldbook.iupac.org/terms/view/08169) segue:

```text
carga formal =
    elétrons de valência
    - elétrons não ligantes
    - metade dos elétrons ligantes
```

O formalismo divide igualmente os elétrons da ligação, independentemente da
eletronegatividade. Carga formal, carga parcial e estado de oxidação são
grandezas diferentes.

## 4. Octeto, deficiência e hipervalência

A [regra do octeto da IUPAC](https://goldbook.iupac.org/terms/view/LT07065)
é especialmente adequada aos elementos do segundo período e possui muitas
exceções nos períodos posteriores.

O [OpenStax, seção 7.3](https://openstax.org/books/chemistry-2e/pages/7-3-lewis-symbols-and-structures)
separa as exceções em:

- espécies com número ímpar de elétrons, como NO;
- moléculas deficientes, como BeH₂ e BF₃;
- moléculas hipervalentes, como PCl₅ e SF₆.

A [hipervalência](https://goldbook.iupac.org/terms/view/HT07054) é comum nos
grupos 15 a 18 após o segundo período. A definição cita ligações de três
centros e quatro elétrons.

Consequências:

- `OCT-001` não deve voltar como erro ou aviso universal;
- B e Be não devem ser rejeitados por octeto incompleto;
- P, S, Cl, Br e I não devem receber teto universal derivado do octeto;
- radicais exigem representação própria.

## 5. Matriz de elementos

| Elemento | Padrão introdutório | Evidências e exceções | Tratamento |
|---|---:|---|---|
| H | 1 | dueto; ligações multicêntricas exigem outro modelo | erro apenas no perfil simples |
| Be | 2 | BeH₂ é deficiente; coordenação varia com agregação | aviso |
| B | 3 | BF₃ tem seis elétrons e recebe par eletrônico | aviso |
| C | 4 | simples, dupla e tripla; carga/radical importam | erro condicional |
| N | 3 | N₂ tripla; N⁺ pode ter quatro ligações; NO é radical | erro condicional |
| O | 2 | CO possui representação `[C−]#[O+]` | erro condicional |
| F | 1 | elemento do segundo período, sem expansão de octeto | erro no perfil simples |
| Al | 3 | Al₂Cl₆ e sólidos alteram coordenação | aviso |
| Si | 4 | tetraédrico usual; também forma redes | aviso |
| P | 3 | PCl₅, `P=O` e `C≡P` existem | aviso |
| S | 2 | SO₂/SO₃, SF₆ e `[C−]≡[S+]` | aviso |
| Cl | 1 | ClF₃ e oxocompostos são hipervalentes | aviso |
| Br | 1 | BrF₃ e BrF₅ neutros | aviso |
| I | 1 | IF₅ e IF₇ neutros | aviso |

O padrão da tabela é útil para mensagens, não como teto físico.

### 5.1 Evidências específicas para P, S, Br e I

- [PubChem POCl₃](https://pubchem.ncbi.nlm.nih.gov/compound/24813):
  representação `O=P(Cl)(Cl)Cl`.
- [PubChem SO₂](https://pubchem.ncbi.nlm.nih.gov/compound/Sulfur-Dioxide):
  representação `O=S=O`, sujeita a ressonância.
- [PubChem phosphaethyne](https://pubchem.ncbi.nlm.nih.gov/compound/138843):
  representação `C#P`.
- [PubChem carbon monosulfide](https://pubchem.ncbi.nlm.nih.gov/compound/Carbon-monosulfide):
  representação `[C-]#[S+]`.
- [PubChem BrF₃](https://pubchem.ncbi.nlm.nih.gov/compound/24594) e
  [BrF₅](https://pubchem.ncbi.nlm.nih.gov/compound/24606): espécies neutras
  com três e cinco ligações Br–F.
- [PubChem IF₅](https://pubchem.ncbi.nlm.nih.gov/compound/Iodine-pentafluoride)
  e [IF₇](https://pubchem.ncbi.nlm.nih.gov/compound/Iodine-heptafluoride):
  espécies neutras com cinco e sete ligações I–F.

Portanto, `Cl`, `Br` e `I` acima de ligação simples devem gerar aviso
contextual, não `BOND-001` universal.

## 6. Ligação coordenada

Segundo a [IUPAC](https://goldbook.iupac.org/terms/view/C01329), coordenação é
a formação de uma ligação covalente cujos dois elétrons vieram da mesma
parte. A origem dos elétrons não altera, por si só, o caráter da ligação
formada.

Uma [base de Lewis](https://goldbook.iupac.org/terms/view/L03511) fornece um
par, e um [ácido de Lewis](https://goldbook.iupac.org/terms/view/L03508) o
aceita.

Limites do modelo atual:

- `COORD-001` só detecta doação por par livre; ligantes pi também podem doar;
- `COORD-003` usa dueto/octeto para inferir capacidade receptora apenas no
  bloco principal;
- “o modelo não identificou capacidade” é correto; “não existe orbital
  vazio” é uma afirmação forte demais;
- metais de transição precisam de orbitais d, ligantes, denticidade,
  hapticidade e contagem eletrônica próprias.

## 7. Molécula, íon e sólidos

A IUPAC define [molécula](https://goldbook.iupac.org/terms/view/M04002) como
entidade eletricamente neutra com mais de um átomo e mínimo suficientemente
profundo na superfície de energia potencial. “Entidade molecular” é um
termo mais geral para moléculas, íons, radicais e complexos.

O [OpenStax, estado sólido](https://openstax.org/books/chemistry-2e/pages/10-5-the-solid-state-of-matter)
distingue:

- sólidos iônicos, como NaCl;
- sólidos metálicos, com elétrons deslocalizados no cristal;
- redes covalentes, como diamante, grafite e SiO₂;
- sólidos moleculares.

Consequências:

- `NaCl` sólido não é uma molécula discreta Na–Cl;
- `Cu~Cu` não valida um cristal metálico;
- diamante e grafite não podem ser inferidos apenas da fórmula `C`;
- a DSL futura precisa declarar o tipo de espécie.

## 8. Espécies canônicas para testes

| Caso | O que deve testar |
|---|---|
| H₂O | conectividade simples e valência usual |
| CO₂ | ligações duplas |
| N₂ | ligação tripla |
| NH₄⁺ | carga total de íon molecular |
| BF₃ | deficiência eletrônica válida |
| NH₃→BF₃ | aduto de Lewis |
| SO₂ e SO₃ | ressonância e representação formal |
| PCl₅ | dependência de fase |
| SF₆ | hipervalência |
| ClF₃ | hipervalência com pares livres |
| NaCl | sólido iônico, não molécula discreta |
| diamante e grafite | redes/alótropos |
| Cu e Fe sólidos | ligação metálica coletiva |

## 9. Redesenho recomendado

Campos que devem permanecer separados:

| Conceito | Campo sugerido |
|---|---|
| ordem formal | `bond_order` |
| carga atômica | `formal_charge` |
| carga da espécie | `species_charge` |
| radical | `unpaired_electrons` ou `multiplicity` |
| origem coordenada | `coordinate_origin` |
| tipo da espécie | `molecule`, `molecular_ion`, `ionic_solid`, `covalent_network`, `metallic_solid` |
| ressonância | `resonance_group` |

Próximas etapas seguras:

1. separar em `valencias.json` limites estritos de padrões que só geram
   aviso;
2. rebaixar Cl/Br/I em ligação múltipla de erro para aviso;
3. manter H/F como limites estritos do perfil Lewis simples;
4. ~~adicionar carga total da espécie antes de conferir a soma das cargas;~~
   implementado em `species molecular_ion ... charge`;
5. ~~modelar radical antes de transformar valência incompleta em erro;~~
   implementado com `unpaired` e verificação de paridade;
6. ~~fazer `~` sempre informar que o grafo não valida um sólido metálico;~~
   implementado como `METAL-002`;
7. ~~criar tipo de espécie antes de representar NaCl, redes ou cristais;~~
   implementado com `molecule`, `molecular_ion`, `ionic_solid`,
   `covalent_network` e `metallic_solid`.

### Limite deliberado: ressonância

Ressonância ainda não recebeu sintaxe. Um `resonance_group` seguro precisa
representar pares livres, elétrons pi e formas contribuintes que preservem
os núcleos, a conectividade sigma e a carga total. Apenas rotular duas
ligações como “ressonantes” no grafo atual criaria falsa precisão.

Até existir esse modelo eletrônico, SO₂, SO₃ e espécies semelhantes usam uma
forma formal localizada e a documentação explica que ela não é uma ordem
física única. Aromaticidade permanece pelo mesmo motivo fora do escopo desta
iteração.

## 10. Regra de governança

Nenhum dado novo deve entrar em `regras/*.json` apenas porque aparece como
estado de oxidação ou “valência comum” numa tabela. Cada regra precisa:

1. definir exatamente a grandeza química;
2. citar fonte;
3. delimitar o escopo;
4. escolher erro, aviso ou documentação;
5. ter caso válido, inválido ou limítrofe correspondente.
