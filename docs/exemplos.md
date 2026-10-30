# Onde ficam os exemplos

O projeto guarda exemplos em dois lugares, com papéis diferentes. Os dois
são testados pelo `testar.py`, com as mesmas regras.

| | Exemplos curados | Corpus gerado |
|---|---|---|
| Onde | `exemplos/`, `invalidos/`, `invalidos_sintaticos/`, `invalidos_semanticos/`, `avisos_semanticos/` e `resolver/` | `corpus/`, com as mesmas cinco subpastas (sem `resolver/`) |
| Quem escreve | pessoas, um arquivo por vez | `corpus/gerar_corpus.py` |
| Para quê | ensinar e documentar: cada arquivo tem um comentário dizendo o que mostra | cobertura em quantidade: muitos elementos, moléculas e variações de cada erro |
| Usado pela página | sim: playground, guia, laboratório, tabela e demonstrações | não |
| Pode editar à mão | sim | não: regenerar o corpus apaga e recria a pasta inteira |

Os dois lugares ficam separados de propósito. Assim, regenerar o corpus
nunca apaga um exemplo escrito à mão, e a lista da página não fica com
centenas de itens repetitivos.

## Pastas e o que o teste confere

A mesma regra vale para a pasta curada e para a sua versão em `corpus/`:

| Pasta | Código de saída esperado | O que o arquivo precisa ter |
|---|---|---|
| `exemplos/` | 0 | nenhuma mensagem; se tiver aviso, ele é declarado em `// esperado:` |
| `invalidos/` | 1 | erro léxico, declarado em `// esperado:` |
| `invalidos_sintaticos/` | 1 | erro sintático, declarado em `// esperado:` |
| `invalidos_semanticos/` | 2 | erro semântico, declarado em `// esperado:` |
| `avisos_semanticos/` | 0 | só avisos, declarados em `// esperado:` |
| `resolver/` | 0 ou 2 | entrada só com átomos; a saída do `--resolver --modelo` fica em `.saida.txt`, e a enumeração em `.todas.txt` |

A comparação com `// esperado:` é exata: código, linha, coluna e texto.

Os exemplos curados também alimentam outros testes: os snapshots
`exemplos/*.ast.txt` e `exemplos/*.modelo.txt`, a AST de todos os
exemplos, os desenhos das árvores e os relatórios químicos.

## Exemplos curados

Para acrescentar um exemplo:

1. Escreva o `.mol` na pasta do tipo dele, com um comentário na primeira
   linha dizendo o que ele mostra.
2. Se ele deve dar erro ou aviso, rode `python3 src/main.py arquivo.mol` e
   copie cada mensagem para uma linha `// esperado:` no topo do arquivo.
   As linhas novas deslocam o código: rode de novo e confira os números de
   linha.
3. Para aparecer na página, acrescente o nome em `GRUPOS_EXEMPLOS`
   (`docs/apresentacao/gerar_apresentacao.py`) e o título em português em
   `docs/apresentacao/nomes_pt.py`.
4. Rode `python3 testar.py` e regenere a página.

## Corpus gerado

`corpus/gerar_corpus.py` gera 1000 arquivos:

| Grupo | Quantidade | Como é gerado |
|---|---|---|
| átomos | 86 | Z = 1 a 86, cada um com a configuração de referência abreviada por gás nobre, o `unpaired` pela regra de Hund e o termo fundamental no comentário |
| isótopos | 80 | os isótopos naturais (CIAAW) dos elementos com mais de um, até o Kr |
| íons monoatômicos | 40 | cátions e ânions comuns, inclusive de metais de transição e do bloco p (Fe²⁺, Cu²⁺, Co³⁺, Sn²⁺...), com a configuração do íon |
| moléculas | 360 | 110 escritas em SMILES e 250 de nomenclatura de classe funcional: 18 grupos R (metila a alila) com 15 grupos X (haletos, cianeto, álcool, amina, éter, sulfeto, cetona, acetato, formiato, hidroperóxido, isocianato, isotiocianato); a mesma estrutura com outro nome entra uma vez só |
| erros de átomo | 150 | elétrons a menos (ATOM-003), Pauli (ATOM-002), massa menor que Z (ATOM-001) e carga maior que Z (ATOM-008) |
| avisos de átomo | 100 | isótopo não natural (ATOM-005), estado excitado (ATOM-004) e `unpaired` contra Hund (ATOM-007) |
| erros em moléculas | 160 | quinta ligação no carbono (VAL-001), nome inexistente (STRUCT-001), ligação repetida (STRUCT-006) e átomo solto (STRUCT-003) |
| sintaxe e léxico | 54 | `}` faltando, ligação sem operador, `bnd`, nome sem aspas e caracteres fora do alfabeto |

Cada arquivo passa pelo compilador real antes de entrar:

- um válido só entra se o compilador não emitir nenhuma mensagem;
- um inválido só entra se o compilador emitir a regra planejada.

O que não passa é descartado e listado no fim da execução. As linhas
`// esperado:` vêm da saída do compilador e servem de regressão: se uma
mudança no compilador alterar uma mensagem, o teste do corpus falha.

Para regenerar (leva alguns minutos):

```bash
python3 corpus/gerar_corpus.py
```

Para mudar o corpus, edite o gerador (as listas `MOLECULAS`, `RADICAIS`,
`GRUPOS`, `IONS` e as cotas em `QUANTIDADES`) e regenere. Não edite os
arquivos de `corpus/` à mão.
