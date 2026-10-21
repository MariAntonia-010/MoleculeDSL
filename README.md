# MoleculeDSL

A MoleculeDSL é uma linguagem de domínio específico criada para representar moléculas simples por meio da declaração de átomos e ligações.

Exemplo:

```text
molecule "Water" {
    atom O
    atom H
    atom H

    bond H-O
    bond O-H
}
```

A linguagem também tem ligações dupla (`=`), tripla (`#`), coordenada (`->`) e metálica (`~`), carga formal (`atom N(+1)`), átomos com nome (`atom C as c1`) e anéis (`ring c1 c2 c3`). A descrição completa e a gramática estão em [docs/especificacao.md](docs/especificacao.md).

## Instalação e execução

O projeto utiliza Python 3.10 ou mais recente e ANTLR 4.13.2.

Instale as dependências:

```bash
pip install antlr4-tools antlr4-python3-runtime
```

Gere o lexer e o parser:

```bash
sh gerar.sh
```

No Windows, o mesmo comando de geração pode ser executado diretamente:

```powershell
antlr4 -Dlanguage=Python3 -visitor -Xexact-output-dir -o gerado gramatica/MoleculeDSL.g4
```

Para analisar um programa:

```bash
python src/main.py exemplos/agua.mol
```

Opções:

- `--tokens`: mostra os tokens reconhecidos.
- `--ast`: mostra a AST (árvore sintática abstrata) construída.

```bash
python src/main.py --tokens --ast exemplos/agua.mol
```

O programa sai com código 0 se não houver erros e 1 se houver erro léxico ou sintático. O código 2 fica reservado para os erros semânticos.

Cada etapa também pode ser executada sozinha:

```bash
python src/lexico.py exemplos/agua.mol          # só os tokens
python src/sintatico.py exemplos/agua.mol       # árvore sintática do ANTLR
python src/construtor_ast.py exemplos/agua.mol  # AST
```

## Fase atual do projeto

As análises léxica e sintática estão implementadas:

- O lexer reconhece palavras-chave, símbolos de elementos, nomes de átomos, textos, números inteiros e reais, quantificadores, operadores de ligação, sinais de carga, delimitadores e comentários.
- O parser confere a estrutura do programa e informa os erros em português, com linha e coluna.
- A AST guarda a posição de cada comando, para ser usada pela análise semântica.

A análise semântica, que confere se a molécula é quimicamente válida, será desenvolvida na próxima etapa (ver [docs/plano_semantico.md](docs/plano_semantico.md)).

## Testes

Para rodar todos os testes:

```bash
python testar.py
```

O script analisa todos os arquivos de:

- `exemplos/`: programas válidos, que devem passar sem erros;
- `invalidos/`: programas com erros léxicos;
- `invalidos_sintaticos/`: programas com erros sintáticos.

Cada arquivo inválido começa com uma ou mais linhas `// esperado: ...`, com o início da mensagem de erro esperada, incluindo a linha e a coluna. O script confere se aparecem exatamente esses erros, na ordem.
