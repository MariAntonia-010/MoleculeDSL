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

---

## 3. Tipos de dados

A MoleculeDSL trabalha com os seguintes tipos de dados:

- **Texto:** utilizado para representar o nome de uma molécula. Os textos são escritos entre aspas duplas, como `"Water"`.
- **Número inteiro:** utilizado para indicar quantidades e repetições, como `4` em uma declaração de múltiplos átomos.
- **Número real:** reconhecido pela linguagem para representar valores numéricos com parte decimal, embora ainda não seja utilizado pelos comandos definidos nesta etapa.
- **Identificador de elemento:** representa o símbolo de um elemento químico, como `H`, `O`, `C`, `Na` ou `Cl`.

---

## 4. Comandos

A MoleculeDSL possui três comandos principais:

### `molecule`

Inicia a declaração de uma molécula.

Exemplo:

```text
molecule "Water" {
}
```

### `atom`

Declara um átomo dentro da molécula.

Exemplo:

```text
atom O
```

Também é possível indicar uma quantidade:

```text
4x atom H
```

### `bond`

Declara uma ligação simples entre dois elementos.

Exemplo:

```text
bond H-O
```

Uma ligação também pode ser repetida:

```text
bond C-H x4
```

---

## 5. Operadores e precedência

A MoleculeDSL utiliza os seguintes operadores:

- `-` representa uma ligação entre dois elementos, como em `H-O`.
- `4x`, por exemplo, representa a repetição de uma declaração de átomo.
- `x4`, por exemplo, representa a repetição de uma ligação.

A linguagem não possui operadores aritméticos ou expressões compostas. Portanto, nesta versão não há níveis de precedência entre operadores.

---

## 6. Comentários

Comentários de uma linha são iniciados por `//`.

Todo o conteúdo depois de `//`, até o final da linha, é considerado comentário e ignorado pelo analisador léxico.

Exemplo:

```text
atom O // átomo de oxigênio
```

---

## 7. O que a linguagem deliberadamente não faz?

A versão atual da MoleculeDSL possui um escopo reduzido de propósito. Ela deliberadamente:

1. **Não permite definir manualmente coordenadas ou posições 3D dos átomos.**
   A linguagem descreve apenas quais átomos existem e como estão ligados. Uma possível
   visualização 3D é responsabilidade de uma etapa posterior, que poderá calcular
   automaticamente o posicionamento dos átomos.

2. **Não diferencia ligações simples, duplas ou triplas.** Nesta versão, todas as ligações são representadas pelo operador `-`.

3. **Não representa propriedades químicas avançadas**, como cargas elétricas e isótopos.