# Especificação da MoleculeDSL

## 1. Para que serve a linguagem?

A MoleculeDSL é uma linguagem de domínio específico criada para descrever moléculas simples por meio da declaração de átomos e das ligações existentes entre eles.

Seu objetivo é permitir que estruturas moleculares sejam representadas de forma textual, simples e legível, sem exigir a definição manual de coordenadas espaciais.

---

## 2. Programa de exemplo

O exemplo abaixo representa uma molécula de água (H₂O):

```text
species molecule "Water" {   // Inicia uma espécie molecular neutra
    atom O           // Declara um átomo de oxigênio
    atom H           // Declara um átomo de hidrogênio
    atom H           // Declara outro átomo de hidrogênio

    bond H-O         // Declara uma ligação entre hidrogênio e oxigênio
    bond O-H         // Declara a segunda ligação entre oxigênio e hidrogênio
}                    // Encerra a definição da molécula
```

Um exemplo com átomos com nome, ligação dupla e anel (ciclopropeno, C₃H₄):

```text
species molecule "Cyclopropene" {
    atom C as c1
    atom C as c2
    atom C as c3
    4x atom H as h       // cria h1, h2, h3 e h4

    bond c1=c2           // ligação dupla
    bond c2-c3
    bond c3-c1
    bond c1-h1
    bond c2-h2
    bond c3-h3
    bond c3-h4

    ring c1 c2 c3
}
```

Há um exemplo para cada construção da linguagem na pasta `exemplos/`.

---

## 3. Tipos de dados

A MoleculeDSL trabalha com os seguintes tipos de dados:

- **Texto:** utilizado para representar o nome de uma molécula. Os textos são escritos entre aspas duplas, como `"Water"`, e não podem ter quebra de linha.
- **Número inteiro:** utilizado em quantidades, repetições e cargas, como `4` em `4x atom H` e `1` em `atom N(+1)`.
- **Número real:** reconhecido pela linguagem para representar valores numéricos com parte decimal, embora ainda não seja utilizado por nenhum comando.
- **Identificador de elemento:** representa o símbolo de um elemento químico, com uma letra maiúscula e, opcionalmente, uma minúscula, como `H`, `O`, `C`, `Na` ou `Cl`.
- **Nome de átomo:** identifica um átomo específico. Começa com letra minúscula e pode ter letras minúsculas, dígitos e `_`, como `c1`, `o1` ou `c_3`.

---

## 4. Comandos

Um programa contém uma única espécie. Dentro dela, os comandos `atom`, `bond`,
`ring` e `stereo` podem aparecer em qualquer ordem.

O cabeçalho recomendado é:

```text
species <tipo> "Nome" [charge +N|-N] [unpaired N] {
}
```

`charge` é obrigatório para `molecular_ion` e `monatomic_ion`. Os tipos
seguem a terminologia da IUPAC:

| Tipo | Entidade | Exemplo |
|---|---|---|
| `atom` | átomo isolado, neutro, sem ligações | `species atom "Argon" { atom Ar }` |
| `monatomic_ion` | íon de um átomo só | `species monatomic_ion "Chloride" charge -1 { atom Cl(-1) }` |
| `molecule` | molécula: entidade neutra com mais de um átomo | água, metano |
| `molecular_ion` | íon com mais de um átomo | amônio, hidróxido |
| `ionic_solid` | motivo de um sólido iônico | cloreto de sódio |
| `covalent_network` | motivo de uma rede covalente | diamante |
| `metallic_solid` | motivo de um sólido metálico, com `~` | sódio metálico |

Pelo Gold Book da IUPAC, molécula é uma entidade eletricamente neutra com
mais de um átomo. Por isso `molecule` ou `molecular_ion` com um átomo só
gera o aviso SPEC-003, e `atom` ou `monatomic_ion` com mais de um átomo ou
com ligações é erro (SPEC-001).
`unpaired` declara elétrons desemparelhados e permite validar a paridade da
contagem eletrônica. O cabeçalho antigo `molecule "Nome"` permanece como
compatibilidade e não ativa a conferência de carga total.

### `molecule`

Inicia a declaração de uma molécula, com o nome entre aspas.

```text
species molecule "Water" {
}
```

### `atom`

Declara um átomo dentro da molécula.

```text
atom O
```

Também é possível indicar uma quantidade, de 1 a 1000:

```text
4x atom H
```

Um átomo pode ter carga formal, sempre com sinal:

```text
atom N(+1)
atom O(-1)
```

Um átomo pode receber um nome com `as`, para ser citado nas ligações e nos anéis:

```text
atom C as c1
```

Com quantidade, o nome vira um prefixo numerado: `4x atom H as h` cria os átomos `h1`, `h2`, `h3` e `h4`.

### `bond`

Declara uma ligação entre dois átomos, citados pelo símbolo do elemento ou pelo nome.

Quando a molécula tem um só átomo do elemento citado, a ligação usa esse átomo. Quando tem vários, cada citação usa o próximo átomo desse elemento que ainda não foi citado, na ordem de declaração. Na água, `bond H-O` usa o primeiro H e `bond O-H` usa o segundo. Se todos já foram citados, é preciso usar nomes.

```text
bond H-O
bond c1=c2
```

Uma ligação também pode ser repetida, de 1 a 1000 vezes. A repetição precisa estar separada por espaço: em `bond C-Hx4`, o texto `Hx` seria lido como símbolo de elemento. Esse e os outros erros comuns de escrita do multiplicador e da repetição (`4 x`, `4 atom`, `x 4`, `x` sem número, `X` maiúsculo) têm mensagem própria, que mostra como escrever.

```text
bond C-H x4
```

Na repetição, pelo menos um dos lados precisa ser um elemento com vários átomos, para cada repetição ligar átomos diferentes. Por isso `bond c1-c2 x2` é um erro: para uma ligação dupla, use `bond c1=c2`.

### `ring`

Marca que os átomos citados, pelo nome, formam um anel. Um anel tem pelo menos três átomos.

Os átomos são citados na ordem em que aparecem no anel: cada um precisa estar ligado ao seguinte, e o último ao primeiro. Um átomo não pode aparecer duas vezes, e o mesmo anel não pode ser declarado duas vezes.

```text
ring c1 c2 c3
```

### `stereo`

Declara a configuração de um elemento estereogênico. Os átomos são citados
pelo nome (ou pelo símbolo, quando só há um átomo do elemento).

```text
stereo c2 R          // centro: R ou S; r ou s em centros pseudoassimétricos
stereo c2=c3 Z       // ligação dupla: E ou Z
stereo c3 Ra         // aleno, pelo átomo central: Ra ou Sa
stereo a1-b1 Ra      // eixo de biarila (atropisomeria)
stereo r1 r2 trans   // configuração relativa de dois centros do mesmo anel
```

A semântica confere se o elemento é estereogênico nesta constituição e nas
outras configurações declaradas (STEREO-001 a STEREO-005). Centros de anel
com dois ramos iguais pelo anel, como em 1,4-dimetilciclohexano, são
declarados por cis/trans.

---

## 5. Operadores e precedência

Operadores de ligação:

| Operador | Ligação | Exemplo |
|---|---|---|
| `-` | simples | `bond H-O` |
| `=` | dupla | `bond C=O` |
| `#` | tripla | `bond n1#n2` |
| `->` | coordenada, do doador para o receptor (a IUPAC considera “dativa” um sinônimo obsoleto) | `bond N->B` |
| `~` | metálica | `bond na1~na2` |

Quantificadores:

- `4x`, por exemplo, repete uma declaração de átomo.
- `x4`, por exemplo, repete uma ligação.

O sinal de uma carga é `+` ou `-`. O `-` é o mesmo símbolo da ligação simples, e o contexto decide o significado.

A linguagem não possui operadores aritméticos ou expressões compostas. Portanto, não há níveis de precedência entre operadores.

---

## 6. Comentários

Comentários de uma linha são iniciados por `//`.

Todo o conteúdo depois de `//`, até o final da linha, é considerado comentário e ignorado pelo analisador léxico.

```text
atom O // átomo de oxigênio
```

---

## 7. Palavras reservadas

As palavras `molecule`, `species`, `molecular_ion`, `monatomic_ion`, `ionic_solid`, `covalent_network`, `metallic_solid`, `charge`, `unpaired`, `atom`, `bond`, `as`, `ring` e `stereo` são reservadas e não podem ser usadas como nome de átomo.

Também ficam reservados os nomes formados por `x` seguido só de dígitos, como `x4`, porque são lidos como repetição de ligação.

---

## 8. Gramática

A gramática completa, em EBNF. Na implementação, ela está em `gramatica/MoleculeDSL.g4`, escrita para o ANTLR.

```ebnf
(* Regras sintáticas *)
programa      = molecula ;
molecula      = cabecalho , [ desemparelhados ] , "{" , { comando } , "}" ;
cabecalho     = "molecule" , texto
              | "species" , "molecule" , texto
              | "species" , "molecular_ion" , texto , carga_especie
              | "species" , "atom" , texto
              | "species" , "monatomic_ion" , texto , carga_especie
              | "species" , "ionic_solid" , texto
              | "species" , "covalent_network" , texto
              | "species" , "metallic_solid" , texto ;
carga_especie = "charge" , ( "+" | "-" ) , inteiro ;
desemparelhados = "unpaired" , inteiro ;
comando       = atomo | ligacao | anel | estereo ;
atomo         = [ multiplicador ] , "atom" , elemento , [ carga ] , [ "as" , nome ] ;
carga         = "(" , ( "+" | "-" ) , inteiro , ")" ;
ligacao       = "bond" , referencia , operador , referencia , [ repeticao ] ;
referencia    = elemento | nome ;
operador      = "-" | "=" | "#" | "->" | "~" ;
anel          = "ring" , nome , nome , nome , { nome } ;
estereo       = "stereo" , referencia , [ [ operador ] , referencia ] , descritor ;
descritor     = elemento | nome ;  (* R, S, E, Z, Ra, Sa, r, s, cis ou trans *)

(* Regras léxicas *)
multiplicador = digito , { digito } , "x" ;
repeticao     = "x" , digito , { digito } ;
inteiro       = digito , { digito } ;
real          = inteiro , "." , inteiro ;
texto         = '"' , { ? qualquer caractere exceto aspas e quebra de linha ? } , '"' ;
elemento      = maiuscula , [ minuscula ] ;
nome          = minuscula , { minuscula | digito | "_" } ;  (* exceto as palavras reservadas *)
comentario    = "//" , { ? qualquer caractere exceto quebra de linha ? } ;

digito        = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
maiuscula     = "A" | "B" | ... | "Z" ;
minuscula     = "a" | "b" | ... | "z" ;
```

Espaços, tabulações, quebras de linha e comentários podem aparecer entre quaisquer dois tokens e são ignorados.

O arquivo deve estar salvo em UTF-8. O BOM que alguns editores colocam no início do arquivo é ignorado, e um arquivo em outra codificação, como latin-1, gera um erro léxico na posição do primeiro caractere inválido.

A gramática só define se o programa está bem formado. Se a molécula é quimicamente válida, por exemplo se `Xx` é um elemento que existe ou se `c1` foi declarado, é decidido pela análise semântica (ver `plano_semantico.md`).

### 8.1 Modelo e classificação das ligações

Depois da AST, a análise semântica expande multiplicadores e repetições num
grafo de átomos e ligações. A opção `--modelo` exibe esse grafo.

Para ligações não metálicas, o modelo calcula a diferença absoluta de
eletronegatividade (`Δχ`) com os dados de `regras/elementos.json` e informa:

- `Δχ < 0,4`: covalente apolar;
- `0,4 ≤ Δχ ≤ 1,7`: covalente polar;
- `Δχ > 1,7`: iônica.

Esses limites são convenções configuráveis em
`regras/classificacao_ligacoes.json`, não uma separação química absoluta.
Se um dos elementos não tiver eletronegatividade na fonte, a ligação aparece
como `não classificada`. A implementação não presume que toda ligação entre
metal e ametal seja iônica.

No perfil Lewis introdutório, ligações múltiplas com H ou F geram erro
`BOND-001`. Para Cl, Br e I, uma ligação múltipla gera apenas `BOND-002`:
espécies hipervalentes e diferentes representações formais não permitem
tratar a ligação simples usual como teto físico universal.

Na ligação coordenada, `origem -> destino` mantém a direção do doador para o
receptor. O compilador confere, como aviso, se o doador tinha um par livre
antes da doação. Para H, He e os elementos do segundo período, também
confere se o receptor tinha espaço até o dueto ou octeto antes de receber o
par. Elementos de períodos posteriores geram aviso de dados insuficientes,
pois não é seguro inferir expansão de valência. Ligações metálicas são
identificadas no modelo como informação de referência, mas nesta iteração
não entram no
cálculo de valência nem na classificação por eletronegatividade. O aviso
Todo `~` produz `METAL-002`, informando que uma aresta do grafo molecular não
valida o comportamento coletivo de um sólido. `METAL-001` é acrescentado
quando algum participante pertence a um bloco não metálico. A aresta `~` não
recebe ordem de ligação, mas não desativa a conferência das demais ligações
do mesmo átomo.

O compilador não possui uma regra separada `OCT-001`: octeto e dueto já são
refletidos pelas valências dos elementos que possuem dados confirmados.
Criar uma segunda regra produziria diagnósticos duplicados; elementos sem
dados continuam sem validação química inventada.

Uma declaração `ring` identifica explicitamente um ciclo. Se o posto cíclico
do grafo indicar mais ciclos independentes do que anéis declarados, o
compilador produz o aviso `RING-004`, sem bloquear a análise.

### 8.2 Resolução automática

Com `--resolver`, uma entrada que contém apenas declarações `atom` pode ter
suas ligações inferidas. O solver:

- usa somente valências confirmadas;
- considera ordens simples, dupla e tripla;
- exige conectividade;
- aceita no máximo 40 átomos totais e 12 átomos pesados;
- só retorna quando existe uma única solução.

H₂O, CO₂, N₂ e NH₄⁺ são os casos de referência. No modo de solução única,
fórmulas com zero ou múltiplas soluções exigem ligações explícitas. C₆H₁₂ é
aceita no modo de enumeração, com resultado truncado pelo limite padrão.

O modo `--resolver-todas` enumera até dez soluções não equivalentes,
deduplicando permutações de átomos com o mesmo elemento e carga. Para
C₂H₄O, são exibidas três alternativas formais. O compilador não escolhe qual
delas representa a espécie desejada. Hidrogênios são distribuídos antes da
busca sobre a matriz dos átomos pesados.

`--max-solucoes=N` e `--tempo-limite=S` controlam a execução.
`--formato=json` devolve um documento completo; `jsonl` emite uma solução
por linha e termina com o sumário. Uma busca interrompida usa `TIMEOUT` ou
`CANCELLED`, preservando `complete=false` e unicidade desconhecida.

---

## 9. O que a linguagem deliberadamente não faz?

A versão atual da MoleculeDSL possui um escopo reduzido de propósito. Ela deliberadamente:

1. **Não permite definir manualmente coordenadas ou posições 3D dos átomos.**
   A linguagem descreve apenas quais átomos existem e como estão ligados. Uma possível
   visualização 3D é responsabilidade de uma etapa posterior, que poderá calcular
   automaticamente o posicionamento dos átomos.

2. **Não tem notação de aromaticidade.** Um anel aromático é escrito com ligações simples e duplas alternadas; a opção `--aromaticidade` aplica a regra de Hückel sobre essa forma.

3. **Não representa isótopos nem geometria 3D.** Por isso a quiralidade planar e as barreiras de rotação de biarilas não são decididas pelo compilador; um eixo de biarila só entra quando declarado com `stereo`.

4. **Não aceita mais de uma espécie por arquivo.**
