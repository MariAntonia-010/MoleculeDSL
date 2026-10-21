# Especificação da MoleculeDSL

## 1. Para que serve a linguagem?

A MoleculeDSL é uma linguagem de domínio específico criada para descrever moléculas simples por meio da declaração de átomos e das ligações existentes entre eles.

Seu objetivo é permitir que estruturas moleculares sejam representadas de forma textual, simples e legível, sem exigir a definição manual de coordenadas espaciais.

---

## 2. Programa de exemplo

O exemplo abaixo representa uma molécula de água (H₂O):

```text
molecule "Water" {   // Inicia a definição da molécula chamada Water
    atom O           // Declara um átomo de oxigênio
    atom H           // Declara um átomo de hidrogênio
    atom H           // Declara outro átomo de hidrogênio

    bond H-O         // Declara uma ligação entre hidrogênio e oxigênio
    bond O-H         // Declara a segunda ligação entre oxigênio e hidrogênio
}                    // Encerra a definição da molécula
```

Um exemplo com átomos com nome, ligação dupla e anel (ciclopropeno, C₃H₄):

```text
molecule "Cyclopropene" {
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

Um programa contém uma única molécula. Dentro dela, os comandos `atom`, `bond` e `ring` podem aparecer em qualquer ordem.

### `molecule`

Inicia a declaração de uma molécula, com o nome entre aspas.

```text
molecule "Water" {
}
```

### `atom`

Declara um átomo dentro da molécula.

```text
atom O
```

Também é possível indicar uma quantidade:

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

Uma ligação também pode ser repetida. A repetição precisa estar separada por espaço: em `bond C-Hx4`, o texto `Hx` seria lido como símbolo de elemento.

```text
bond C-H x4
```

Na repetição, pelo menos um dos lados precisa ser um elemento com vários átomos, para cada repetição ligar átomos diferentes. Por isso `bond c1-c2 x2` é um erro: para uma ligação dupla, use `bond c1=c2`.

### `ring`

Marca que os átomos citados, pelo nome, formam um anel. Um anel tem pelo menos três átomos.

```text
ring c1 c2 c3
```

---

## 5. Operadores e precedência

Operadores de ligação:

| Operador | Ligação | Exemplo |
|---|---|---|
| `-` | simples | `bond H-O` |
| `=` | dupla | `bond C=O` |
| `#` | tripla | `bond n1#n2` |
| `->` | coordenada (dativa), do doador para o receptor | `bond N->B` |
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

As palavras `molecule`, `atom`, `bond`, `as` e `ring` são reservadas e não podem ser usadas como nome de átomo.

Também ficam reservados os nomes formados por `x` seguido só de dígitos, como `x4`, porque são lidos como repetição de ligação.

---

## 8. Gramática

A gramática completa, em EBNF. Na implementação, ela está em `gramatica/MoleculeDSL.g4`, escrita para o ANTLR.

```ebnf
(* Regras sintáticas *)
programa      = molecula ;
molecula      = "molecule" , texto , "{" , { comando } , "}" ;
comando       = atomo | ligacao | anel ;
atomo         = [ multiplicador ] , "atom" , elemento , [ carga ] , [ "as" , nome ] ;
carga         = "(" , ( "+" | "-" ) , inteiro , ")" ;
ligacao       = "bond" , referencia , operador , referencia , [ repeticao ] ;
referencia    = elemento | nome ;
operador      = "-" | "=" | "#" | "->" | "~" ;
anel          = "ring" , nome , nome , nome , { nome } ;

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

A gramática só define se o programa está bem formado. Se a molécula é quimicamente válida, por exemplo se `Xx` é um elemento que existe ou se `c1` foi declarado, é decidido pela análise semântica (ver `plano_semantico.md`).

---

## 9. O que a linguagem deliberadamente não faz?

A versão atual da MoleculeDSL possui um escopo reduzido de propósito. Ela deliberadamente:

1. **Não permite definir manualmente coordenadas ou posições 3D dos átomos.**
   A linguagem descreve apenas quais átomos existem e como estão ligados. Uma possível
   visualização 3D é responsabilidade de uma etapa posterior, que poderá calcular
   automaticamente o posicionamento dos átomos.

2. **Não representa aromaticidade.** Um anel aromático precisa ser escrito com ligações simples e duplas alternadas.

3. **Não representa propriedades químicas avançadas**, como isótopos e estereoquímica.

4. **Não aceita mais de uma molécula por arquivo.**
