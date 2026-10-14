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

## Instalação e execução

O projeto utiliza Python 3 e ANTLR 4.13.2.

Instale as dependências:

```bash
pip install antlr4-tools antlr4-python3-runtime
```

Gere o analisador léxico:

```bash
sh gerar.sh
```

No Windows, o mesmo comando de geração pode ser executado diretamente:

```powershell
antlr4 -Dlanguage=Python3 -o gerado gramatica/MoleculeDSL.g4
```

Para analisar um programa:

```bash
python src/lexico.py exemplos/agua.mol
```

## Fase atual do projeto

O projeto está na etapa E2, correspondente à especificação da linguagem e à implementação do analisador léxico.

Nesta etapa, o lexer reconhece palavras-chave, identificadores de elementos, textos, números inteiros e reais, quantificadores, operadores, delimitadores e comentários.

A análise sintática e a análise semântica serão desenvolvidas nas próximas etapas do projeto.

## Testes

Para testar os programas válidos:

```bash
python src/lexico.py exemplos/agua.mol
python src/lexico.py exemplos/metano.mol
python src/lexico.py exemplos/amonia.mol
```

Para testar os exemplos com erros léxicos:

```bash
python src/lexico.py invalidos/caractere_invalido.mol
python src/lexico.py invalidos/texto_sem_fechar.mol
python src/lexico.py invalidos/numero_malformado.mol
```

Nos exemplos inválidos, o analisador informa a linha e a coluna em que o erro léxico foi encontrado.
