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
- `--modelo`: mostra o modelo da molécula, com cada átomo e cada ligação já resolvidos.

```bash
python src/main.py --tokens --ast exemplos/agua.mol
```

Se a pasta `gerado/` não existir, o programa pede para rodar o `sh gerar.sh`.

O programa sai com código 0 se não houver erros, 1 se houver erro léxico ou sintático e 2 se houver erro semântico.

Cada etapa também pode ser executada sozinha:

```bash
python src/lexico.py exemplos/agua.mol          # só os tokens
python src/sintatico.py exemplos/agua.mol       # árvore sintática do ANTLR
python src/construtor_ast.py exemplos/agua.mol  # AST
```

## Fase atual do projeto

As análises léxica e sintática estão implementadas:

- O lexer reconhece palavras-chave, símbolos de elementos, nomes de átomos, textos, números inteiros e reais, quantificadores, operadores de ligação, sinais de carga, delimitadores e comentários.
- O lexer e o parser informam os erros em português, com linha e coluna. Os erros de espaço mais comuns, como `bond C-Hx4`, têm mensagem própria.
- O arquivo deve estar em UTF-8 (com ou sem BOM).
- A AST guarda a posição de cada comando, para ser usada pela análise semântica.

A análise semântica está em andamento (ver [docs/plano_semantico.md](docs/plano_semantico.md)). Ela já monta o modelo da molécula e confere:

- as regras estruturais: elemento desconhecido, átomo ou nome inexistente, nome duplicado, átomo sem ligação, ligação de um átomo com ele mesmo, ligação repetida e anéis;
- as regras químicas que têm fonte no [levantamento de química](docs/levantamento_quimica.md): valência, carga formal e elementos que só fazem ligação simples. Os dados estão em `regras/valencias.json`, e elemento sem dado não é conferido.

Erros semânticos impedem a compilação. Avisos, como uma valência incompleta, só são mostrados.

## Testes

Para rodar todos os testes:

```bash
python testar.py
```

O script analisa todos os arquivos de:

- `exemplos/`: programas válidos, que devem passar sem erros;
- `invalidos/`: programas com erros léxicos;
- `invalidos_sintaticos/`: programas com erros sintáticos;
- `invalidos_semanticos/`: programas com erros semânticos;
- `avisos_semanticos/`: programas válidos que geram avisos.

Cada arquivo inválido ou com aviso começa com uma ou mais linhas `// esperado: ...`, com o início da mensagem esperada, incluindo a linha e a coluna. O script confere se aparecem exatamente essas mensagens, na ordem, e o código de saída.
