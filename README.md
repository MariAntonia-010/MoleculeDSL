# MoleculeDSL

MoleculeDSL é uma linguagem de domínio específico para descrever moléculas
simples por meio de átomos, ligações, cargas formais e anéis. O compilador
didático foi escrito em Python e usa ANTLR 4 para as etapas léxica e
sintática.

```text
species molecule "Water" {
    atom O
    2x atom H

    bond H-O
    bond O-H
}
```

A forma antiga `molecule "Nome"` continua aceita por compatibilidade. A forma
`species` declara explicitamente o tipo da espécie, sua carga total quando
for um íon e a quantidade de elétrons desemparelhados quando for radical.

A linguagem aceita ligações simples (`-`), duplas (`=`), triplas (`#`),
coordenadas (`->`) e metálicas (`~`), além de carga (`atom N(+1)`), nomes
(`atom C as c1`), quantificadores (`4x`, `x4`) e anéis
(`ring c1 c2 c3`).

Tipos disponíveis:

```text
species molecule "Water" { ... }
species molecular_ion "Ammonium" charge +1 { ... }
species ionic_solid "Sodium chloride" { ... }
species covalent_network "Diamond motif" { ... }
species metallic_solid "Sodium" { ... }
```

Radicais usam `unpaired`, por exemplo:

```text
species molecule "Nitric oxide" unpaired 1 { ... }
```

## Pré-requisitos e instalação

- Python 3.10 ou mais recente;
- Java JRE 11 ou mais recente, necessário para executar o gerador ANTLR;
- ANTLR 4.13.2.

Instale as dependências:

```bash
python3 -m pip install -r requirements.txt
```

Para habilitar o backend opcional CP-SAT:

```bash
python3 -m pip install -r requirements-solver.txt
```

O `antlr4-tools` pode instalar o executável em `~/.local/bin`. Se o terminal
não o encontrar, inclua essa pasta no `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Gere o lexer, o parser e o visitor:

```bash
sh gerar.sh
```

No Windows, execute o comando equivalente:

```powershell
$env:ANTLR4_TOOLS_ANTLR_VERSION = "4.13.2"
antlr4 -Dlanguage=Python3 -visitor -Xexact-output-dir -o gerado gramatica/MoleculeDSL.g4
```

## Uso

Para analisar uma molécula:

```bash
python3 src/main.py exemplos/agua.mol
```

Opções disponíveis:

| Opção | Saída |
|---|---|
| `--tokens` | tokens produzidos pelo lexer |
| `--ast` | árvore sintática abstrata própria, com posições |
| `--modelo` | grafo expandido de átomos e ligações |
| `--resolver` | infere ligações quando há somente átomos e solução única |
| `--resolver-todas` | enumera até dez estruturas não equivalentes |
| `--max-solucoes=N` | altera o limite da enumeração |
| `--tempo-limite=S` | interrompe a busca após S segundos |
| `--formato=texto\|json\|jsonl` | escolhe a saída do solver |
| `--backend=reference\|cpsat` | seleciona o backend de busca |
| `--aneis=N` | mantém só estruturas com N anéis |
| `--ligacoes-multiplas=N` | mantém só estruturas com N ligações duplas ou triplas |
| `--exigir=C=O` | mantém só estruturas com essa cadeia, como `O-C=O` (pode repetir) |
| `--proibir=C#C` | descarta estruturas com essa cadeia (pode repetir) |
| `--isolar` | roda a busca num processo separado, encerrado no tempo limite |

As opções podem ser combinadas:

```bash
python3 src/main.py --tokens --ast --modelo exemplos/agua.mol
```

### Solver de soluções únicas

O solver usa somente valências confirmadas e não escolhe arbitrariamente
entre isômeros:

```bash
python3 src/main.py --resolver --modelo resolver/agua.mol
```

Nesta etapa estão cobertos H₂O, CO₂, N₂ e NH₄⁺. No modo `--resolver`,
entradas sem solução, ambíguas ou com ligações já declaradas são rejeitadas.
O backend de referência aceita até 40 átomos totais e 12 átomos pesados;
hidrogênios são distribuídos antes da geração da matriz pesada. A matriz é
gerada coluna a coluna, e cada prefixo que não é canônico corta o ramo
(geração ordenada de Read-Faradzev): C₆H₆ dá seus 217 isômeros
constitucionais em menos de um décimo de segundo.

Para inspecionar fórmulas ambíguas pequenas:

```bash
python3 src/main.py --resolver-todas resolver/formula_ambigua.mol
```

Átomos equivalentes são deduplicados por isomorfismo elementar. C₂H₄O
produz três alternativas formais; a enumeração é limitada às dez primeiras.

Para consumo por ferramentas:

```bash
python3 src/main.py --resolver --formato=json resolver/agua.mol
python3 src/main.py --resolver-todas --max-solucoes=2 \
  --formato=jsonl resolver/formula_ambigua.mol
```

O sumário informa `complete`, `unique`, `status`, quantidade emitida,
backend, versão, tempo, nome, versão e digest do perfil químico e os
filtros aplicados. Em `jsonl`, cada solução é escrita assim que é
encontrada, sem acumular a enumeração na memória; o sumário vem por último. `LIMIT_REACHED`, `TIMEOUT` e
`CANCELLED` nunca são apresentados como busca completa.

Filtros objetivos ajudam a escolher entre alternativas sem ranking oculto.
Eles valem para `--resolver` e `--resolver-todas`:

```bash
python3 src/main.py --resolver-todas --exigir=C=O resolver/formula_ambigua.mol
python3 src/main.py --resolver --aneis=0 --proibir=C=O resolver/formula_ambigua.mol
```

Para C₂H₄O, `--exigir=C=O` deixa só o acetaldeído, e `--aneis=0
--proibir=C=O` torna o álcool vinílico a única estrutura. Um fragmento é
uma cadeia de átomos distintos com os operadores das ligações (`C=O`,
`O-C=O`, `C=C-C=C`) e casa em qualquer um dos dois sentidos.

O backend `reference` permanece o oráculo auditável. `cpsat` usa OR-Tools,
a mesma distribuição prévia de H e restrições de líder lexicográfico entre
átomos gêmeos; a conexão é conferida no callback, e só a rotulação canônica
é aceita. A suíte compara os dois backends, e `tests/benchmark_solver.py
--backend=ambos` mede os dois numa lista fixa de fórmulas.

Com `--isolar` (ou `SolveRequest(isolate=True)`), a busca roda num processo
separado; o pai repassa cada solução assim que ela chega e encerra o filho no
tempo limite, mesmo se ele estiver preso numa chamada nativa.

O modelo classifica ligações por diferença de eletronegatividade como
covalente apolar, covalente polar ou iônica. Os limites configuráveis ficam
em `regras/classificacao_ligacoes.json`. Ligação sem dados suficientes
aparece como `não classificada`.

### Relatórios químicos

Depois de uma análise sem erros, estas opções mostram informações extras:

| Opção | Mostra |
|---|---|
| `--eletronico` | pares livres, elétrons não ligantes e ligações pi de cada átomo |
| `--ressonancia` | formas de ressonância, inclusive de radicais; ligações `->` ficam fixas e `~` fica fora |
| `--tautomeros` | tautômeros por deslocamento de H de ou para heteroátomos (ceto-enol, imina-enamina) |
| `--aromaticidade` | regra de Hückel nos ciclos e sistemas fundidos |
| `--estereo` | centros, duplas E/Z, alenos e eixos declarados, com prioridades CIP e a contagem exata de estereoisômeros |
| `--coordenacao` | metais, ligantes, κ/η/μ, estados de oxidação e contagem de elétrons |

```bash
python3 src/main.py --ressonancia exemplos/carbonato.mol
python3 src/main.py --tautomeros exemplos/acetona.mol
python3 src/main.py --aromaticidade exemplos/naftaleno.mol
python3 src/main.py --estereo exemplos/acido_tartarico_meso.mol
python3 src/main.py --coordenacao avisos_semanticos/tetracarbonilniquel.mol
```

A contagem de estereoisômeros agrupa as configurações pelo grupo de
automorfismos do grafo, então já desconta formas meso (ácido tartárico: 3) e
reconhece centros pseudoassimétricos (ácido 2,3,4-tri-hidroxiglutárico: 4).
A contagem de 18 elétrons é só informativa.

### Configuração estereoquímica

O comando `stereo` declara a configuração de um elemento estereogênico:

```text
stereo c2 R          // centro: R ou S; r ou s em centros pseudoassimétricos
stereo c2=c3 Z       // ligação dupla: E ou Z
stereo c3 Ra         // aleno, pelo átomo central: Ra ou Sa
stereo a1-b1 Ra      // eixo de biarila (atropisomeria), com aviso STEREO-005
stereo r1 r2 trans   // configuração relativa de dois centros do mesmo anel
```

Com a configuração declarada, `--estereo` diz se o estereoisômero é quiral,
aquiral ou meso e mostra os descritores do enantiômero. A semântica confere
se o elemento é de fato estereogênico (`STEREO-001`), se o descritor combina
com o tipo do elemento (`STEREO-002`), repetições (`STEREO-003`) e se um
centro pseudoassimétrico tem a configuração dos ramos declarada
(`STEREO-004`).

Cada etapa também pode ser executada isoladamente:

```bash
python3 src/lexico.py exemplos/agua.mol
python3 src/sintatico.py exemplos/agua.mol
python3 src/construtor_ast.py exemplos/agua.mol
```

### Códigos de saída

| Código | Significado |
|---|---|
| `0` | análise concluída; avisos não bloqueiam |
| `1` | erro de entrada, configuração, léxico ou sintático |
| `2` | erro semântico |

## Página de apresentação

[docs/apresentacao/index.html](docs/apresentacao/index.html) abre direto no
navegador, sem servidor nem internet, em tema claro ou escuro. Ela tem
quatro módulos com rotas: **Conteúdo** (a apresentação em 11 páginas, com
setas do teclado), **Uso**, **Doc** (comandos, gramática real, erros e
relatórios) e **Playground**. No playground, o código MoleculeDSL é analisado
no navegador enquanto se digita e a molécula é desenhada em 3D. A aba
"Compilador real" mostra a saída de `src/main.py --modelo` para os exemplos.

Todas as saídas exibidas vêm de execuções reais. Depois de mudar o
compilador, gere a página de novo:

```bash
python3 docs/apresentacao/gerar_apresentacao.py
```

## Árvores em SVG

`desenhar_arvore.py` gera a parse tree do ANTLR ou a AST sem depender de
Graphviz:

```bash
python3 src/desenhar_arvore.py exemplos/agua.mol --tipo sintatica
python3 src/desenhar_arvore.py exemplos/agua.mol --tipo ast
```

Use `-o caminho.svg` para escolher o destino. Sem essa opção, o SVG é salvo
ao lado do arquivo `.mol`.

## Pipeline

```text
arquivo .mol
  → lexer
  → parser ANTLR
  → AST própria
  → modelo em grafo
  → análise semântica
```

Cada etapa só roda quando a anterior não produziu erro. A semântica consome
somente a AST, nunca a parse tree do ANTLR.

## Erros reportados

Os listeners próprios coletam até dez erros por fase e nunca mostram a
mensagem crua, em inglês, do ANTLR:

```text
Erro léxico [LEX-001] na linha 4, coluna 4: caractere inválido '@'
Erro sintático [SIN-004] na linha 3, coluna 10: esperado '}' para fechar a molécula
Erro semântico [VAL-001] na linha 3, coluna 4: a soma das ordens de ligação...
```

O catálogo de códigos, causas e correções está em
[docs/erros.md](docs/erros.md).

## Regras semânticas

| ID | Regra | Severidade |
|---|---|---|
| `ELEM-001` | elemento desconhecido | erro |
| `STRUCT-001` a `STRUCT-007` | integridade de átomos, nomes, ligações e quantidades | erro |
| `BOND-001` | ligação múltipla excede limite estrito de H/F | erro |
| `BOND-002` | ligação múltipla incomum em Cl/Br/I | aviso |
| `VAL-001` | valência excedida | erro |
| `VAL-002` | valência incompleta | aviso |
| `CARGA-001` | carga inconsistente com a valência | erro |
| `CARGA-002` | soma das cargas formais difere da carga total | erro |
| `COORD-001` a `COORD-004` | par livre do doador e espaço eletrônico do receptor | aviso |
| `METAL-001` | ligação `~` envolve participante não metálico | aviso |
| `METAL-002` | grafo molecular não valida sólido metálico | aviso |
| `RAD-001` | contagem ímpar sem `unpaired` | aviso |
| `RAD-002` | paridade de `unpaired` incompatível | erro |
| `SPEC-001` | declaração incompatível com o tipo da espécie | erro |
| `SPEC-002` | grafo finito representa apenas motivo de rede | aviso |
| `RING-001` a `RING-003` | integridade e duplicidade de anéis | erro |
| `RING-004` | ciclo independente sem declaração `ring` | aviso |
| `STRUCT-008` | entidade molecular tem componentes desconectados | erro |
| `STEREO-001` a `STEREO-004` | configuração em elemento não estereogênico, descritor errado, repetido ou sem desempate | erro |
| `STEREO-005` | eixo de biarila declarado sem verificação da barreira | aviso |

As regras completas, suas fontes e as limitações estão em
[docs/plano_semantico.md](docs/plano_semantico.md) e
[docs/levantamento_quimica.md](docs/levantamento_quimica.md). Dados químicos
sem fonte não são inferidos.

## Testes

Execute:

```bash
python3 testar.py
```

O script verifica:

- exemplos válidos em `exemplos/`;
- erros léxicos em `invalidos/`;
- erros sintáticos em `invalidos_sintaticos/`;
- erros semânticos em `invalidos_semanticos/`;
- avisos em `avisos_semanticos/`;
- arquivo inexistente e código ANTLR ausente;
- snapshots textuais da AST e do modelo;
- tipo, ordem e posição dos nós da AST em todos os exemplos;
- soluções únicas e rejeições do solver, contrato JSON/JSONL, filtros,
  isolamento e comparação com o CP-SAT quando o OR-Tools está instalado;
- relatórios químicos (ressonância, tautômeros, aromaticidade,
  estereoquímica e coordenação);
- geração de parse tree e AST em SVG para todos os exemplos.

Casos inválidos e avisos declaram as mensagens esperadas no próprio arquivo:

```text
// esperado: Erro sintático [SIN-001] na linha 3, coluna 8: ...
```

A comparação é exata: ID, linha, coluna e explicação precisam coincidir.
Exemplos válidos também podem declarar avisos esperados, mantendo código de
saída 0.

## Estrutura

```text
gramatica/                  gramática combinada do ANTLR
src/                        lexer, parser, AST, modelo, semântica e relatórios químicos
                            (eletronico, tautomeros, aromaticidade, estereo, complexos)
src/solver/                 solver de estruturas (backends, filtros, geração ordenada, isolamento)
tests/benchmark_solver.py   medição dos backends numa lista fixa de fórmulas
regras/                     dados químicos e limites configuráveis
exemplos/                   programas válidos e snapshots
invalidos/                  casos léxicos inválidos
invalidos_sintaticos/       casos sintáticos inválidos
invalidos_semanticos/       casos semânticos inválidos
avisos_semanticos/          programas válidos que geram avisos
resolver/                   entradas e snapshots do solver
docs/                       especificação, planos e diagramas
docs/apresentacao/          página de apresentação offline (index.html gerado a partir de modelo.html)
gerado/                     código produzido pelo ANTLR, ignorado pelo Git
```

## Documentação

- [Especificação da linguagem](docs/especificacao.md)
- [Árvore Sintática Abstrata](docs/ast.md)
- [Erros léxicos e sintáticos](docs/erros.md)
- [Plano semântico](docs/plano_semantico.md)
- [Levantamento e fontes de química](docs/levantamento_quimica.md)
- [Pesquisa química aprofundada](docs/pesquisa_quimica_aprofundada.md)
- [Plano completo do solver](docs/plano_solver.md)
- [Plano de eliminação dos limites](docs/plano_limites.md)
- [Diário do projeto](docs/DIARIO.md)
- [Página de apresentação](docs/apresentacao/index.html)

## Estado atual e limitações

Léxico, sintaxe, AST, modelo, tipos de espécie, carga total, radicais,
regras estruturais, valência, carga formal,
classificação por eletronegatividade, validação do doador coordenado, anéis,
configuração estereoquímica (`stereo`), solver de estruturas e relatórios
químicos estão implementados e testados.

Continuam pendentes:

- valências ainda sem fonte para Be, Al, Si e metais de transição;
- modelo semântico próprio para sólidos metálicos; nesta iteração,
  `METAL-001` verifica a composição e `METAL-002` informa a limitação
  coletiva de todo uso de `~`.

`OCT-001` foi removida: para elementos com dados, octeto e dueto já são
refletidos pelas regras de valência. Ciclos independentes sem `ring` agora
geram o aviso `RING-004`.

Ficam fora por dependerem da geometria 3D, que a linguagem não descreve:
quiralidade planar (ferrocenos substituídos, ciclofanos) e o cálculo da
barreira de rotação de biarilas, que por isso só entram quando declaradas.
Também ficam fora visualização 3D e isótopos; sem isótopos, a regra CIP 2
nunca tem empate a resolver.

## Solução de problemas

- **`antlr4: not found`:** adicione `~/.local/bin` ao `PATH`.
- **`CFG-001`:** execute `sh gerar.sh`; a pasta `gerado/` não é versionada.
- **Erro de Java:** instale um JRE e confirme com `java -version`.
- **Erro `LEX-005`:** salve o arquivo `.mol` em UTF-8.
- **Windows:** use o comando PowerShell de geração mostrado na instalação.
