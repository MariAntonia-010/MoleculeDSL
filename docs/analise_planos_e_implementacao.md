# Análise dos planos e da implementação (E3: análise sintática)

Data: 21/10/2026. Escopo: `plano_sintatico.md`, `plano_semantico.md`, a gramática em `gramatica/MoleculeDSL.g4` e o código de `src/`.
Tudo que está marcado como **verificado** foi rodado em `python testes/rodar_testes.py` (96 verificações).

## 1. Situação dos marcos do plano sintático

| Marco | Estado | Onde |
|---|---|---|
| S1 Estender o lexer | feito | `gramatica/MoleculeDSL.g4` |
| S2 Regras do parser | feito | idem; os 3 exemplos antigos continuam válidos sem mudança |
| S3 Geração e build | feito | `gerar.sh` agora usa `-visitor` e aceita `ANTLR_JAR=` |
| S4 Tratamento de erros | feito | `src/erros.py` (mensagens em português, linha e coluna) |
| S5 AST com posições | feito | `src/arvore.py` + `src/construtor_ast.py` |
| S6 CLI encadeada | feito | `src/main.py` com `--tokens`, `--ast`, `--arvore` |
| S7 Testes | feito | `testes/`, `exemplos/`, `invalidos*/` |
| S8 Documentação | feito | este arquivo, `especificacao.md`, `DIARIO.md`, README, vault Obsidian |

## 2. O que o plano sintático previu e a prática confirmou (verificado)

- `x4` casa com `REPETICAO_LIGACAO` e com `NOME` no mesmo tamanho, e vence a regra declarada primeiro. Nome `x4` fica reservado (`invalidos_sintaticos/nome_reservado_x4.mol`).
- `->` vence `-` por casamento mais longo, e `N(-1)` continua lido como `(`, `-`, `1`, `)`.
- `4x` vence `4` seguido de nome, e `as1` é um `NOME`, não a palavra-chave `as`.
- Palavras-chave antes de `NOME`: `atom`, `bond`, `as`, `ring`, `molecule` não servem de nome de átomo.

## 3. O que o plano não previu

### 3.1 `Hx4` é lido como o elemento `Hx` (achado novo)
`IDENT : [A-Z][a-z]?` aceita qualquer par maiúscula+minúscula. Quem escreve `bond C-Hx4` (sem espaço) obtém `IDENT 'Hx'` seguido de `INTEIRO 4`, e a mensagem do ANTLR sozinha seria confusa.
**Feito:** o parser detecta esse padrão e acrescenta uma dica (`invalidos_sintaticos/colado_hx4.mol`).
**Consequência:** o léxico nunca valida se o elemento existe (`Xx`, `Hx`); isso é do ELEM-001 na semântica. Já está no plano, só faltava dizer que o lexer não ajuda.

### 3.2 O lexer do ANTLR continua depois de um erro
Num caractere inválido (`@`), o ANTLR descarta o caractere e segue. Se só o parser fosse consultado, `atom O @` seria aceito como `atom O`.
**Feito:** `processar()` interrompe após qualquer erro léxico e nem chama o parser (também evita cascata). Teste: "cli: erro léxico interrompe antes do parser".

### 3.3 Cascata de erros sintáticos
O plano pede "coletar todos os erros possíveis". A recuperação do ANTLR às vezes produz um segundo erro que é só consequência do primeiro (`atom_sem_elemento.mol`, `nome_palavra_reservada.mol`, `bond_sem_origem.mol`).
**Feito:** a CLI avisa que o primeiro erro é o confiável. Alternativa, se a banca preferir: `BailErrorStrategy` (para no primeiro erro).

### 3.4 Coluna: base 0 ou base 1
O ANTLR numera colunas a partir de 0; editores, a partir de 1. O `lexico.py` antigo imprimia a base 0. **Mudei para base 1** em todas as etapas, e a saída do léxico mudou por isso.

### 3.5 Arquivos do Windows
Editores do Windows gravam BOM UTF-8, que o lexer rejeitaria como caractere inválido. `ler_arquivo()` lê com `utf-8-sig` (teste: `exemplos/com_bom_utf8.mol`).

### 3.6 Token sem uso
`REAL` existe no lexer, mas nenhuma regra do parser o consome. Qualquer número real vira erro sintático (`carga_real.mol`). Coerente com a especificação ("reconhecido, mas não usado"); só vale lembrar na defesa.

## 4. Problemas no plano semântico (a decidir antes de implementar)

Os exemplos que você adicionou (`amonio.mol`, `eteno.mol`, `etanol.mol`) expõem contradições entre o que o parser aceita e o que o plano semântico supõe.

### 4.1 `xN` com nomes: o plano se contradiz
`plano_sintatico.md` diz que `bond c1-c2 x2` é erro porque "repetição só vale para elementos, não para átomos com nome". Mas `amonio.mol` usa `bond n1-h x4` e `eteno.mol` usa `bond c1-h1 x2`, ambos com nomes. O parser aceita as duas formas, então a regra tem de ser decidida na semântica.
**Proposta:** `xN` é válido quando um dos lados é um **grupo** (prefixo de `Nx atom ... as p`) de tamanho N, e significa "ligar ao grupo inteiro". Em dois átomos simples (`c1-c2 x2`), `xN` é erro, porque duplicaria a aresta e concorreria com `=`. Esse caso já está em `invalidos_semanticos/repeticao_em_nome__A-DEFINIR.mol` e precisa de um ID de erro.

### 4.2 O mesmo nome pode ser átomo ou grupo
Em `acetileno.mol`, `h1` é um átomo único. Em `eteno.mol`, `2x atom H as h1` cria um grupo cujos membros seriam `h11` e `h12`, e `h1` passa a ser o prefixo. Pelo texto do plano, a expansão é "prefixo + índice", então `h1` + `1` = `h11`, que pode colidir com `atom H as h11` ou ser confundido com `h1`.
**Proposta:** a semântica classifica cada nome como ÁTOMO ou GRUPO, reporta colisão após expansão como STRUCT-002, e a documentação recomenda prefixo sem dígito (como no `amonio.mol`: `as h`).

### 4.3 Referência por símbolo é ambígua
Na água, `bond H-O` aparece duas vezes e há dois H. O plano não diz a qual H cada linha se refere. Sem política, o grafo muda conforme a implementação.
**Proposta:** referência por símbolo consome, na ordem de declaração, o primeiro átomo daquele elemento que ainda não participou de ligação com o outro lado; se não houver, STRUCT-001. `etanol.mol` (`bond c1-H x3`) testa esse caso misturando nome e símbolo.

### 4.4 Itens menores
- `plano_semantico.md` ainda cita o bloco `metal { ... }` no M1, mas a decisão 3 do plano sintático o descartou. **Ajustado nesta entrega.**
- Ligação coordenada: o plano diz que o doador precisa de par livre e o receptor de orbital vazio, mas não diz se `->` conta na valência do doador (N com 3 simples + 1 coordenada = 4). Isso define se `NH4+` é válido. Decidir no M5.
- Carga: `atom H(+3)`, `atom N(+0)` e `atom N(+99)` passam no parser; todos são CARGA-001.
- `molecule "" { }` é válido na sintaxe; decidir se nome vazio é erro semântico.

## 5. Estado do processo (importante para a entrega)
- O `DIARIO.md` registra que a ampliação da linguagem (`=`, `#`, `->`, `~`, carga, `as`, `ring`) **ainda não foi aprovada pelo grupo**, e o plano pede combinar com a Maria antes do PR. A implementação já contém tudo isso. Ver a pendência no diário.
- O enunciado e o prazo da disciplina continuam sem conferência.

## 6. Limitações desta entrega
- O jar do ANTLR usado aqui veio do pacote npm `antlr4ng-cli` (build `4.13.2-SNAPSHOT`), porque o ambiente não alcança o Maven. Não é o jar oficial do `antlr4-tools`. Regere na sua máquina com `sh gerar.sh` e rode `python testes/rodar_testes.py` para confirmar.
- `exemplos/coordenada.mol` e `exemplos/metalica.mol` chegaram **vazios** no upload (o RAR estava truncado nesses dois). Não os reescrevi; o manifesto de testes os ignora enquanto estiverem vazios e os valida normalmente quando tiverem conteúdo. No lugar, criei `coordenada_nh3_h.mol` e `metalica_sodio.mol`.
- A análise semântica **não** foi implementada, como pedido. `main.py` marca o ponto de entrada.

## Integração com a versão Main

Na integração, a versão Main permanece como base: a análise semântica e o modelo de molécula foram preservados. Posições de coluna na AST e nos diagnósticos seguem base 0. Exemplos que usavam um nome de grupo com multiplicador (por exemplo, `4x atom H as h`) foram adaptados para nomes individuais (`h1`, `h2`, etc.) e ligações explícitas, evitando introduzir uma semântica de prefixo de grupo que não existe na Main.

A CLI oferece `--arvore` para imprimir a árvore concreta do ANTLR, e `src/main.py` expõe `processar(texto)` para executar o pipeline em memória. A API retorna um objeto `Resultado` com AST, árvore concreta, lexer/parser, modelo e mensagens/erros.
