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