# Diário de Desenvolvimento — MoleculeDSL

Este documento registra as principais decisões, alterações e dificuldades encontradas durante o desenvolvimento da MoleculeDSL.

## 09/09/2026 — Definição da linguagem

### O que foi feito

- Escolha do domínio da linguagem.
- Definição da proposta da MoleculeDSL.
- Definição do objetivo e do escopo inicial do projeto.
- Definição das principais construções da linguagem, como `molecule`, `atom` e `bond`.
- Definição inicial dos tokens e da forma de representação de moléculas.
- Elaboração da documentação inicial do projeto.

### Decisões tomadas

Foi decidido criar uma linguagem de domínio específico voltada à descrição de estruturas moleculares simples.

A linguagem foi planejada para permitir a declaração de moléculas, átomos e ligações de forma textual e legível, mantendo um escopo reduzido para facilitar a implementação durante as etapas do projeto.

Também foi definido que a linguagem descreve principalmente a topologia da molécula. A geração de uma representação visual, incluindo uma possível visualização 3D, fica para uma etapa posterior do projeto.

---

## 16/09/2026 — Organização da E2 e repositório

### O que foi feito

- Organização da estrutura do repositório para a etapa E2.
- Criação das pastas `docs`, `gramatica`, `src`, `exemplos` e `invalidos`.
- Criação dos arquivos iniciais necessários para o projeto.
- Envio da estrutura inicial para o repositório Git.
- Adaptação da documentação inicial para o formato de especificação solicitado na E2.
- Organização do arquivo `especificacao.md` seguindo os requisitos da atividade.

### Configuração do ANTLR

Durante a configuração do ANTLR no Windows, a ferramenta inicialmente não conseguiu
identificar automaticamente a versão disponível. Foi definida manualmente a versão
4.13.2, compatível com o runtime Python instalado.

---

## 14/10/2026 — Planejamento da sintaxe e da semântica, e levantamento de química

### O que foi feito

- Correção do `gerar.sh`: final de linha Unix, versão 4.13.2 do ANTLR fixada e `-Xexact-output-dir`, para o lexer ser gerado direto em `gerado/`. O comando do Windows no README recebeu a mesma opção.
- Escrita do plano de análise sintática (`docs/plano_sintatico.md`), já pensando na entrada da semântica: a AST deve guardar linha e coluna de cada nó.
- Escrita do plano de análise semântica (`docs/plano_semantico.md`), em marcos de M1 a M8.
- Levantamento das regras de química (`docs/levantamento_quimica.md`), com a fonte e o status de cada regra: FONTE, CONVENÇÃO, DERIVADA ou PENDENTE.
- Geração de `regras/elementos.json` com os 118 elementos, a partir da tabela periódica da PubChem.
- Abertura do pull request #2 com essas mudanças.

### Decisões tomadas

- A gramática responde se a estrutura é válida na linguagem. As regras químicas ficam na análise semântica, e não na gramática.
- As regras químicas ficam em arquivos de dados (`regras/`), e não escritas direto no código.
- Aromaticidade e visualização 3D ficam fora do escopo.
- Os limites de eletronegatividade que separam ligação apolar, polar e iônica variam entre as fontes. Eles devem ser parâmetros configuráveis, e o resultado é só informativo.
- Valência e estado de oxidação são conceitos diferentes. A coluna de estados de oxidação da PubChem não é usada como valência.

### Propostas que ainda não foram aprovadas

Os planos propõem ampliar a linguagem com ligações duplas (`=`), triplas (`#`), coordenada (`->`) e metálica (`~`), carga formal, átomos com nome e anéis. Isso reverte a exclusão de ligações duplas e triplas da especificação atual. Nada disso foi implementado, e é preciso combinar com o grupo antes.

### Dificuldades encontradas

- O `gerar.sh` do repositório falhava no macOS por causa do final de linha do Windows e da consulta à versão mais recente do ANTLR, que retornava erro HTTP 400.
- Parte das fontes do levantamento de química é didática, e não primária. Os itens que dependem delas precisam ser conferidos num livro-texto.
- Não achei no IUPAC Gold Book uma definição de ligação metálica, então esse ponto ficou pendente.

### Pendências

- A Maria vai fazer o plano de testes.
- Confirmar as valências e as regras marcadas como PENDENTE no levantamento de química.
- Decidir se S e P podem fazer ligação dupla e tripla, como tratar ligação metálica e o que fazer com metais de transição.
- Aprovar ou ajustar a ampliação da linguagem proposta nos planos.
