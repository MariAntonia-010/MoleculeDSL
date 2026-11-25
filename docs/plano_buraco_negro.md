# Plano do buraco negro (`species black_hole`)

Estado: implementado na linguagem (gramática, AST, semântica e modelo) e no
playground da página (`docs/apresentacao/buraco_negro.js`).

O pedido era poder construir, com a química da própria linguagem, um buraco
negro que devora a tela inteira. Este plano registra a física que decide
quando a matéria colapsa, como o buraco é desenhado e o que é licença
didática.

## Na linguagem: colapso de uma espécie declarada

```text
species atom "Ferro-56" unpaired 4 {
    atom 56Fe as fe
    configuration fe [Ar] 3d6 4s2
}

species black_hole "Nucleo de ferro colapsado" {
    collapse 1.1e32 mol of "Ferro-56"
}
```

**Decisão.** Um tipo novo de espécie, `black_hole`, com um único comando,
`collapse N mol of "Bloco"`. A quantidade é em mol (aceita inteiro, real e
notação científica) e o bloco citado é uma espécie declarada antes, como em
`atom "Nome"`.

**Por quê.**

- Qualquer massa vira buraco negro se for comprimida abaixo do raio de
  Schwarzschild, `r_s = 2GM/c²`; mas a natureza só faz isso sozinha acima
  de certos limites. Pôr esses limites na semântica faz a química decidir:
  a mesma linguagem que confere valência e carga confere se a matéria
  colapsa.
- A massa sai do que a linguagem já sabe: `M = N · N_A · m_partícula`, com a
  massa atômica de `regras/elementos.json` ou o número de massa do isótopo
  declarado (erro abaixo de 0,1%).
- Mol é a unidade da química. Uma estrela de nêutrons tem perto de 10³²
  mol de ferro; por isso a gramática ganhou a notação científica.

## As regras HOLE

A ordem é a da física: primeiro a química fecha, depois a gravidade decide.

| Regra | Condição | Por quê |
|---|---|---|
| HOLE-001 | `collapse` fora de `species black_hole` | o comando só tem sentido no bloco do colapso |
| HOLE-002 | o bloco citado tem erro semântico | não há espécie válida para juntar |
| HOLE-003 | quantidade zero, negativa ou infinita | não há matéria |
| HOLE-004 | carga líquida diferente de zero | Reissner-Nordström exige `Q ≤ M·√(4πε₀G)`; um mol de íons passa disso por ~10¹⁶ vezes, e a repulsão desfaz a matéria antes |
| HOLE-005 | `M` < 1,44 M☉ | limite de Chandrasekhar: a degenerescência dos elétrons segura uma anã branca |
| HOLE-006 | `M` ≤ 2,16 M☉ | limite de Tolman-Oppenheimer-Volkoff (Rezzolla et al., 2018): os nêutrons seguram |

As mensagens de HOLE-005 e HOLE-006 dizem quantos mols faltam. A
referência a outro buraco negro é BLOCK-002, e um bloco `black_hole` com
`charge`, átomos ou mais de um `collapse` é SPEC-001.

Os limites são aproximações conhecidas: Chandrasekhar vale para 2 núcleons
por elétron, e o TOV depende da equação de estado da matéria nuclear
(2,16 +0,17 −0,15 M☉). A linguagem usa os valores centrais.

## O modelo

| Grandeza | Fórmula |
|---|---|
| massa | `M = N · N_A · m_partícula`, também em M☉ |
| raio de Schwarzschild (horizonte) | `r_s = 2GM/c²` |
| esfera de fótons | `1,5 r_s` |
| raio da sombra visto de longe | `(√27 / 2) r_s ≈ 2,6 r_s` |
| temperatura de Hawking | `T = ħc³ / (8πGMk_B)` |
| tempo de evaporação (só fótons) | `t = 5120πG²M³ / (ħc⁴)` |

Pelo teorema da calvície, o buraco não guarda qual espécie o formou: só
massa, carga e rotação. O modelo diz isso e mostra só a fórmula de origem.

## No playground: o buraco devora a tela

Compilar um `black_hole` válido troca a cena 3D pelo buraco negro calculado
e, pouco mais de um segundo depois, o buraco devora a tela sozinho, com a
massa e o horizonte na legenda. Compilar o mesmo texto de novo não repete a
animação; um texto diferente, sim. Um programa com erro não mostra nada.

## Como: imagem calculada por traçado de raios

A referência visual são as imagens calculadas, não ilustrações:
Luminet (1979) foi o primeiro a calcular a aparência de um buraco negro
com disco fino; a equipe de *Interstellar* (James, von Tunzelmann,
Franklin e Thorne, 2015) refez o cálculo para o filme e publicou o método;
o Event Horizon Telescope (2019) confirmou o anel com diâmetro próximo de
`5,2 r_s` em M87*.

**Decisão.** Um fragment shader WebGL, sem biblioteca, traça um raio por
pixel, de trás para a frente, na métrica de Schwarzschild. Cada raio fica
num plano e obedece à equação de Binet dos fótons,
`d²u/dφ² + u = 3Mu²` com `u = 1/r` (unidades `G = c = 1`), integrada com
Runge-Kutta de 4ª ordem. O raio termina de um de quatro jeitos:

1. cruza o horizonte (`r < 2M`): preto, é a sombra;
2. bate no disco de acreção: cor do disco;
3. bate na folha da página, atrás do buraco: a página distorcida;
4. escapa: céu estrelado.

Saem do próprio cálculo, sem desenho à mão: a sombra, o anel de fótons, o
anel de Einstein da página, a parte de trás do disco erguida por cima da
sombra e a imagem secundária do lado de baixo do disco.

**Disco de acreção.** Fino, opaco, no plano equatorial, de `6M` (ISCO) a
`20M`, visto 8° acima do plano, como na figura de Luminet. Temperatura
pelo perfil do disco fino, `T ∝ r^(-3/4) (1 − √(r_in/r))^(1/4)`.
Cada ponto é deslocado em frequência pelo fator
`g = √(1 − 3M/r) / (1 − Ω L_z)`, que junta o redshift gravitacional e o
Doppler da órbita (`Ω = √(M/r³)`); o brilho cai com `g⁴`. Por isso um lado
do disco é mais claro e azulado (vem na nossa direção) e o outro é mais
escuro e avermelhado.

**Devorar a tela.** A página é fotografada (SVG `foreignObject`, com os
canvas da cena trocados por imagens) e vira a folha atrás do buraco. Com a
massa crescendo, o buraco começa do tamanho de um ponto onde a pessoa
está o buraco na cena, a página se curva num anel de Einstein, o disco se acende e a
sombra cresce. No fim o observador está dentro da esfera de fótons
(`r < 3M`): para um observador parado ali, a sombra ocupa mais da metade do
céu, então a tela inteira, que olha para o buraco, fica preta. Não é um
efeito inventado: é o que a métrica dá.

## O que é licença didática

- **A espiral da página.** Lente gravitacional sozinha não arrasta nada: a
  página atrás do buraco só se curva. A espiral que enrola a página em
  direção ao disco representa matéria caindo e não sai da métrica.
- **Escurecer e avermelhar o que cai.** Um observador distante vê o que
  cai no buraco ficar mais lento, mais vermelho e mais escuro, e nunca o vê
  cruzar o horizonte. A animação aplica esse avermelhamento à página que
  espirala, de forma aproximada.
- **Cor do disco.** Um disco real é quente demais para o visível (raios X
  num buraco estelar, ultravioleta num supermassivo). A temperatura de cor
  é rebaixada para o disco aparecer branco-alaranjado.
- **Sem rotação.** O buraco é de Schwarzschild. Um buraco de Kerr achataria
  um lado da sombra e arrastaria o espaço, o que exigiria integrar a
  geodésica completa, mais cara do que cabe num shader de página.
- **O disco some no fim.** Com a massa crescendo, o disco (de `6M` a `20M`)
  chegaria até o observador; ele se apaga quando o observador está a menos
  de `34M`, e o fim mostra só a sombra.
- **A massa cresce.** Na animação, o observador fica parado e a massa
  cresce; é o mesmo que o observador se aproximar, porque a imagem só
  depende de `r/M`.

## Acessibilidade e queda de desempenho

- A animação só começa porque a pessoa compilou um `black_hole`: é uma
  resposta à ação dela. Com `prefers-reduced-motion: reduce`, aparece um
  quadro estático e um botão para ver a animação mesmo assim (WCAG 2.3.3,
  técnicas C39 e SCR40).
- `Esc` ou **Voltar** encerram a qualquer momento; o foco volta ao editor
  do playground. A fase atual é anunciada numa região `aria-live`.
- O shader roda em resolução reduzida e baixa mais se o quadro passar de
  ~40 ms.
- Sem WebGL, o modelo continua no painel e a cena explica que a animação
  precisa de WebGL. Se a foto da página falhar, a folha vira a cor de fundo
  da página e o resto da animação segue.

## Fontes

- J.-P. Luminet, *Image of a spherical black hole with thin accretion
  disk*, A&A 75, 228 (1979). <https://ui.adsabs.harvard.edu/abs/1979A&A....75..228L/abstract>
- O. James, E. von Tunzelmann, P. Franklin, K. S. Thorne, *Gravitational
  lensing by spinning black holes in astrophysics, and in the movie
  Interstellar*, CQG 32, 065001 (2015). <https://arxiv.org/abs/1502.03808>
- Event Horizon Telescope Collaboration, *First M87 Event Horizon Telescope
  Results* (2019); diâmetro do anel de 4,8 a 5,2 `r_s`.
  <https://www.arxiv.org/pdf/1906.11241>
- S. Gralla, D. Holz, R. Wald, *Black hole shadows, photon rings, and
  lensing rings*, PRD 100, 024018 (2019). <https://arxiv.org/abs/1906.00873>
- Observador distante e objeto em queda (fica vermelho, escurece, não cruza):
  <https://www.astronomy.com/science/ask-astro-can-an-observer-ever-see-something-fall-into-a-black-hole/>
- Espaguetificação e maré no horizonte:
  <https://en.wikipedia.org/wiki/Spaghettification>
- Traçado de raios de Schwarzschild em WebGL (referência de método):
  <https://oseiskar.github.io/black-hole/README>
- WCAG 2.3.3, Animation from Interactions:
  <https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions>
- S. Chandrasekhar, *The maximum mass of ideal white dwarfs*, ApJ 74, 81
  (1931).
- L. Rezzolla, E. Most, L. Weih, *Using gravitational-wave observations and
  quasi-universal relations to constrain the maximum mass of neutron
  stars*, ApJL 852, L25 (2018). <https://arxiv.org/abs/1711.00314>
- Limite de carga de Reissner-Nordström e teorema da calvície:
  <https://en.wikipedia.org/wiki/Reissner%E2%80%93Nordstr%C3%B6m_metric>
- Constantes: CODATA 2018 (`G`, `ħ`, `k_B`, `u`); massa solar nominal da
  IAU 2015 (`GM☉ = 1,3271244×10²⁰ m³/s²`); Sgr A* `4,3×10⁶ M☉` (GRAVITY
  2022); M87* `6,5×10⁹ M☉` (EHT 2019).
