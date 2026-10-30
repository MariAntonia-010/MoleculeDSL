"""Lições do guia de uso da MoleculeDSL.

Cada exemplo é compilado pelo compilador real quando a página é gerada.
"saida" é o código de saída esperado (0 sem erro, 1 léxico ou sintático,
2 semântico); se o compilador discordar, a geração falha, então o guia
nunca mostra um exemplo que não funciona do jeito descrito.
"""

LICOES = [
    {
        "id": "construir_atomo",
        "titulo": "Construindo um átomo, passo a passo",
        "texto": [
            "A estrutura mais simples que a linguagem descreve é um átomo sozinho. "
            "Ela já usa as três partes de todo programa: o cabeçalho da espécie, as chaves e uma declaração.",
            "Pela IUPAC, um átomo isolado não é molécula. Por isso o tipo é species atom (ou species monatomic_ion, se tiver carga), e não species molecule.",
        ],
        "passos": [
            {"titulo": "Escolha o tipo da espécie", "texto": "Para um átomo neutro, species atom. Para um átomo com carga, species monatomic_ion, que exige charge no cabeçalho.", "codigo": "species atom"},
            {"titulo": "Dê um nome à espécie", "texto": "Entre aspas, logo depois do tipo. É o nome da espécie inteira, não do átomo.", "codigo": 'species atom "Carbon"'},
            {"titulo": "Abra e feche as chaves", "texto": "Tudo o que compõe a espécie fica entre { e }.", "codigo": 'species atom "Carbon" {\n}'},
            {"titulo": "Declare o átomo", "texto": "atom seguido do símbolo do elemento: primeira letra maiúscula e, se houver, a segunda minúscula (C, Na, Cl). Um átomo isolado não tem ligações, então não há bond.", "codigo": 'species atom "Carbon" {\n    atom C\n}'},
            {"titulo": "O que o compilador monta", "texto": "O átomo não nasce do nada nem vazio. 'atom C' monta um átomo completo: 6 prótons (Z do carbono); 6 nêutrons, do isótopo natural mais abundante (¹²C, pela CIAAW), porque nenhum número de massa foi dado; e 6 elétrons, porque sem carga declarada o átomo é neutro (elétrons = Z − carga), distribuídos no estado fundamental 1s2 2s2 2p2. O --modelo mostra tudo isso: p=6 n=6 (12C, mais abundante) e=6 [He] 2s2 2p2.", "codigo": "C#1 carga=+0 p=6 n=6 (12C, mais abundante) e=6 [He] 2s2 2p2"},
            {"titulo": "Mude o padrão quando precisar", "texto": "Cada parte do átomo tem um jeito de ser declarada. Número de massa: atom 13C troca os 6 nêutrons por 7. Carga: atom C(-1) acrescenta um elétron (7), e atom Na(+1) tira um. Elétrons em outro arranjo: configuration (estado excitado gera aviso ATOM-004).", "codigo": "atom 13C        // 6 p, 7 n, 6 e\natom C(-1)      // 6 p, 6 n, 7 e\natom Na(+1)     // 11 p, 12 n, 10 e"},
            {"titulo": "Compile", "texto": "O compilador confere que há um único átomo, sem ligações, e que o elemento existe. Sem erro, sai com código 0. No playground, a aba Átomos mostra o núcleo e a eletrosfera de cada átomo declarado.", "codigo": "python3 src/main.py --ast --modelo carbono.mol"},
            {"titulo": "Opcional: núcleo e eletrosfera", "texto": "O número de massa antes do símbolo escolhe o isótopo, e configuration declara a configuração eletrônica; o compilador confere as duas (lição seguinte).", "codigo": 'species atom "Carbon-13" unpaired 2 {\n    atom 13C as c\n    configuration c [He] 2s2 2p2\n}'},
            {"titulo": "Veja o átomo", "texto": "No playground, uma espécie de um átomo só é desenhada pelo modelo de Bohr, com as camadas de elétrons da configuração e a contagem de prótons e nêutrons. python3 src/main.py --estrutura-atomica mostra o diagrama de orbitais.", "codigo": ""},
        ],
        "anatomia": {
            "codigo": "atom 23Na(+1) as na1",
            "partes": [
                ["atom", "palavra-chave: declara um átomo (token ATOM)"],
                ["23", "número de massa, opcional: prótons + nêutrons (notação de nuclídeo); sem ele, composição natural"],
                ["Na", "símbolo do elemento (token IDENT, [A-Z][a-z]?)"],
                ["(+1)", "carga formal, opcional; o sinal é obrigatório"],
                ["as na1", "nome do átomo, opcional; sem ele o nome automático é Na#1"],
            ],
        },
        "exemplos": [
            {
                "titulo": "O átomo de carbono completo",
                "explicacao": "A AST mostra a espécie e um AtomoDecl com o nome automático C#1; o modelo tem um átomo e nenhuma ligação.",
                "codigo": 'species atom "Carbon" {\n    atom C\n}\n',
                "opcoes": ["--ast", "--modelo"],
                "saida": 0,
                "bohr": "C",
            },
            {
                "titulo": "Variação: com nome",
                "explicacao": "as c dá um nome ao átomo; numa espécie de um átomo só ele é opcional, mas é o mesmo recurso usado depois para citar átomos nas ligações.",
                "codigo": 'species atom "Carbon" {\n    atom C as c\n}\n',
                "opcoes": ["--ast"],
                "saida": 0,
                "bohr": "C",
            },
            {
                "titulo": "Variação: íon monoatômico",
                "explicacao": "Com carga, o tipo passa a monatomic_ion e o cabeçalho declara charge; a carga do átomo precisa bater com ela. Na⁺ perde o elétron da camada externa.",
                "codigo": 'species monatomic_ion "Sodium(1+)" charge +1 {\n    atom Na(+1)\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
                "bohr": "Na",
                "carga": 1,
            },
            {
                "titulo": "Erro comum: símbolo em minúsculas",
                "explicacao": "na começa com minúscula, então é lido como nome, não como elemento: erro de sintaxe (código 1).",
                "codigo": 'species atom "Sodium" {\n    atom na\n}\n',
                "opcoes": [],
                "saida": 1,
            },
            {
                "titulo": "Erro comum: elemento que não existe",
                "explicacao": "Xx tem a forma de um símbolo, mas não está na tabela periódica: erro semântico ELEM-001.",
                "codigo": 'species atom "Unknown" {\n    atom Xx\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Erro comum: átomo com carga declarado como atom",
                "explicacao": "species atom é neutro e não declara charge; com carga, use species monatomic_ion.",
                "codigo": 'species atom "Sodium" {\n    atom Na(+1)\n}\n',
                "opcoes": [],
                "saida": 2,
            },
        ],
    },
    {
        "id": "nucleo_eletrosfera",
        "titulo": "Núcleo e eletrosfera: isótopos e configuração eletrônica",
        "texto": [
            "O núcleo tem Z prótons e N nêutrons; o número de massa é A = Z + N. Como na notação de nuclídeo da IUPAC (¹³C), "
            "o número de massa vem antes do símbolo: atom 13C. Sem número, vale a composição isotópica natural. "
            "O compilador confere que A ≥ Z e avisa quando o isótopo não está entre os naturais da CIAAW.",
            "A eletrosfera segue três regras. Pauli: a subcamada l comporta 2(2l+1) elétrons (s2, p6, d10, f14), e na camada n só "
            "existem l de 0 a n−1. Aufbau (Madelung): a ordem de preenchimento 1s, 2s, 2p, 3s, 3p, 4s, 3d..., com exceções reais "
            "como o Cr (3d5 4s1). Hund: em orbitais de mesma energia, um elétron em cada antes de formar pares.",
            "configuration declara a configuração de um átomo isolado ou íon monoatômico, com um núcleo de gás nobre opcional "
            "([He], [Ne], [Ar]...). O compilador confere Pauli, o total de elétrons (Z − carga) e compara com o estado fundamental "
            "medido; o unpaired precisa bater com a regra de Hund. Cátions de metais de transição perdem os elétrons 4s antes dos 3d.",
            "O relatório --estrutura-atomica também dá o termo fundamental (2S+1)L_J pelas regras de Hund: ³P₀ no carbono, ⁵D₄ no ferro. "
            "E o número de massa entra na estereoquímica: pela regra CIP 2, com números atômicos empatados, o isótopo mais pesado "
            "tem prioridade (²H > H), então um deutério pode criar um centro quiral.",
        ],
        "anatomia": {
            "codigo": "configuration fe [Ar] 3d6",
            "partes": [
                ["configuration", "palavra-chave: configuração eletrônica (token CONFIGURATION)"],
                ["fe", "o átomo descrito (referência por nome ou símbolo)"],
                ["[Ar]", "núcleo de gás nobre, opcional: os 18 elétrons do argônio"],
                ["3d6", "subcamada: camada 3, tipo d, 6 elétrons (token SUBCAMADA)"],
            ],
        },
        "exemplos": [
            {
                "titulo": "Carbono-13 com configuração e relatório",
                "explicacao": "6 prótons, 7 nêutrons, 1s2 2s2 2p2 e dois elétrons desemparelhados pela regra de Hund, como declara unpaired 2.",
                "codigo": 'species atom "Carbon-13" unpaired 2 {\n    atom 13C as c\n    configuration c [He] 2s2 2p2\n}\n',
                "opcoes": ["--estrutura-atomica"],
                "saida": 0,
                "bohr": "C",
            },
            {
                "titulo": "Isótopos numa molécula: água pesada",
                "explicacao": "O número de massa também vale dentro de moléculas: D₂O usa dois deutérios (2H). Já a configuration não: numa molécula os elétrons ocupam orbitais moleculares.",
                "codigo": 'species molecule "Heavy water" {\n    atom O as o\n    2x atom 2H as d\n    bond o-d1\n    bond o-d2\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Íon com o núcleo sozinho: Na⁺ = [Ne]",
                "explicacao": "O Na⁺ perdeu o 3s1 e ficou com os 10 elétrons do neônio. A notação química é só o núcleo, e a linguagem aceita configuration na [Ne] sem subcamadas.",
                "codigo": 'species monatomic_ion "Sodium(1+)" charge +1 {\n    atom Na(+1) as na\n    configuration na [Ne]\n}\n',
                "opcoes": ["--estrutura-atomica"],
                "saida": 0,
            },
            {
                "titulo": "Ferro-56 e o termo fundamental",
                "explicacao": "26 prótons e 30 nêutrons; 3d6 tem quatro elétrons desemparelhados (Hund), e o termo de menor energia é ⁵D₄: S = 2, L = 2 e, com a subcamada d mais que meio cheia, J = L + S = 4.",
                "codigo": 'species atom "Iron-56" unpaired 4 {\n    atom 56Fe as fe\n    configuration fe [Ar] 3d6 4s2\n}\n',
                "opcoes": ["--estrutura-atomica"],
                "saida": 0,
                "bohr": "Fe",
            },
            {
                "titulo": "Elemento sem isótopo natural: tecnécio",
                "explicacao": "O tecnécio não tem isótopo estável; a CIAAW não lista composição natural para ele. Qualquer número de massa gera o aviso ATOM-005.",
                "codigo": 'species atom "Technetium-99" unpaired 5 {\n    atom 99Tc\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Regra CIP 2: o deutério cria um centro",
                "explicacao": "No etanol o C1 tem dois H iguais e não é centro. Trocando um H por ²H, os números atômicos empatam entre D e H, e a regra 2 decide pelo número de massa: O > C > ²H > H, configuração R.",
                "codigo": 'species molecule "(1R)-(1-2H1)ethan-1-ol" {\n    atom C as c1\n    atom C as c2\n    atom O as o\n    atom 2H as d\n    5x atom H as h\n    bond c1-c2\n    bond c1-o\n    bond c1-d\n    bond c1-h1\n    bond o-h2\n    bond c2-h3\n    bond c2-h4\n    bond c2-h5\n    stereo c1 R\n}\n',
                "opcoes": ["--estereo"],
                "saida": 0,
            },
            {
                "titulo": "Exceção real ao Aufbau: crômio",
                "explicacao": "A regra de Madelung preveria 3d4 4s2; o estado medido é 3d5 4s1, com seis elétrons desemparelhados. O compilador usa os dados medidos como referência.",
                "codigo": 'species atom "Chromium" unpaired 6 {\n    atom Cr as cr\n    configuration cr [Ar] 3d5 4s1\n}\n',
                "opcoes": ["--estrutura-atomica"],
                "saida": 0,
                "bohr": "Cr",
            },
            {
                "titulo": "Íon de metal de transição: Fe²⁺",
                "explicacao": "Fe é [Ar] 3d6 4s2; ao formar o cátion, saem primeiro os dois elétrons 4s: [Ar] 3d6, com quatro desemparelhados.",
                "codigo": 'species monatomic_ion "Iron(2+)" charge +2 unpaired 4 {\n    atom Fe(+2) as fe\n    configuration fe [Ar] 3d6\n}\n',
                "opcoes": ["--estrutura-atomica"],
                "saida": 0,
                "bohr": "Fe",
                "carga": 2,
            },
            {
                "titulo": "Erro: subcamada acima do limite de Pauli",
                "explicacao": "2p comporta no máximo 6 elétrons.",
                "codigo": 'species atom "Neon" {\n    atom Ne as ne\n    configuration ne 1s2 2s1 2p7\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Erro: subcamada que não existe",
                "explicacao": "Na camada 2 só existem s (l = 0) e p (l = 1); 2d é impossível.",
                "codigo": 'species atom "Carbon" {\n    atom C as c\n    configuration c 1s2 2s2 2d2\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Erro: número de elétrons errado",
                "explicacao": "O carbono neutro tem 6 elétrons, e a configuração soma 7.",
                "codigo": 'species atom "Carbon" {\n    atom C as c\n    configuration c 1s2 2s2 2p3\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Erro: número de massa menor que Z",
                "explicacao": "5C teria 6 prótons e −1 nêutron.",
                "codigo": 'species atom "Carbon" {\n    atom 5C\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Aviso: estado excitado",
                "explicacao": "Um elétron do 2s foi para o 2p: possível, mas não é o estado fundamental.",
                "codigo": 'species atom "Carbon" {\n    atom C as c\n    configuration c 1s2 2s1 2p3\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Aviso: isótopo radioativo",
                "explicacao": "14C não está entre os isótopos naturais estáveis da CIAAW (12C e 13C).",
                "codigo": 'species atom "Carbon-14" {\n    atom 14C\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Aviso: unpaired contra a regra de Hund",
                "explicacao": "O oxigênio (2p4) tem dois elétrons desemparelhados, não zero.",
                "codigo": 'species atom "Oxygen" unpaired 0 {\n    atom O\n}\n',
                "opcoes": [],
                "saida": 0,
                "bohr": "O",
            },
        ],
    },
    {
        "id": "primeiro",
        "titulo": "Primeiro programa",
        "texto": [
            "Cada bloco descreve uma espécie química. O cabeçalho diz o tipo e o nome; "
            "entre chaves vêm os átomos e as ligações, em qualquer ordem. Um arquivo pode ter vários blocos (lição seguinte).",
            "O compilador lê o texto, monta a árvore, constrói o grafo da molécula e confere a química. "
            "Sem erro, ele responde que a análise foi concluída e sai com código 0.",
        ],
        "exemplos": [
            {
                "titulo": "Água com cabeçalho completo",
                "explicacao": "species molecule declara uma molécula neutra; o compilador confere que a soma das cargas é zero.",
                "codigo": 'species molecule "Water" {\n    atom O\n    atom H\n    atom H\n\n    bond H-O\n    bond O-H\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Variação: cabeçalho legado",
                "explicacao": "molecule \"Nome\" continua aceito, mas não ativa a conferência da carga total.",
                "codigo": 'molecule "Water" {\n    atom O\n    atom H\n    atom H\n    bond H-O\n    bond O-H\n}\n',
                "opcoes": [],
                "saida": 0,
            },
        ],
    },
    {
        "id": "blocos",
        "titulo": "Vários blocos: declare os átomos, depois as moléculas",
        "texto": [
            "Um arquivo pode ter vários blocos species, um depois do outro. O compilador analisa cada bloco na ordem e "
            "mostra o resultado de cada um; um bloco com erro não impede a análise dos outros.",
            "Um átomo declarado num bloco species atom ou species monatomic_ion pode ser reaproveitado depois: "
            "atom \"Nome do bloco\" traz o elemento, o número de massa e a carga daquele bloco. Assim o deutério ou o "
            "carbono-13 são declarados uma vez e usados em várias moléculas.",
            "O bloco citado precisa vir antes (BLOCK-001), ter um átomo só (BLOCK-002) e um nome que nenhum outro bloco "
            "use (BLOCK-003). A configuração eletrônica não é herdada: dentro da molécula os elétrons ocupam orbitais "
            "moleculares.",
        ],
        "anatomia": {
            "codigo": '2x atom "Deuterio" as d',
            "partes": [
                ["2x", "quantidade, como em qualquer atom"],
                ["atom", "palavra-chave da declaração de átomo"],
                ['"Deuterio"', "nome de um bloco anterior, entre aspas: o átomo vem de lá (2H)"],
                ["as d", "nome dos átomos nesta molécula: d1 e d2"],
            ],
        },
        "exemplos": [
            {
                "titulo": "Carbono-13 declarado e reaproveitado",
                "explicacao": "O bloco 1 declara o carbono-13 com a configuração; o bloco 2 usa atom \"Carbono-13\", e o modelo mostra A=13 e 7 nêutrons no carbono do metano.",
                "codigo": 'species atom "Carbono-13" unpaired 2 {\n    atom 13C as c\n    configuration c [He] 2s2 2p2\n}\n\nspecies molecule "Metano-13C" {\n    atom "Carbono-13" as c\n    4x atom H as h\n    bond c-h1\n    bond c-h2\n    bond c-h3\n    bond c-h4\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Um átomo, duas moléculas",
                "explicacao": "O deutério é declarado uma vez e usado na água pesada e no hidróxido deuterado.",
                "codigo": 'species atom "Deuterio" unpaired 1 {\n    atom 2H\n}\n\nspecies molecule "Agua pesada" {\n    atom O as o\n    2x atom "Deuterio" as d\n    bond o-d1\n    bond o-d2\n}\n\nspecies molecular_ion "Hidroxido deuterado" charge -1 {\n    atom O(-1) as o\n    atom "Deuterio" as d\n    bond o-d\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Erro: o bloco vem depois",
                "explicacao": "A molécula cita o deutério antes de ele ser declarado. Os blocos são lidos na ordem do arquivo.",
                "codigo": 'species molecule "Agua pesada" {\n    atom O as o\n    2x atom "Deuterio" as d\n    bond o-d1\n    bond o-d2\n}\n\nspecies atom "Deuterio" unpaired 1 {\n    atom 2H\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Erro: o bloco citado não é um átomo",
                "explicacao": "atom \"Nome\" reaproveita um átomo; um bloco de molécula tem vários átomos e não pode ser citado assim.",
                "codigo": 'species molecule "Agua" {\n    atom O as o\n    2x atom H as h\n    bond o-h1\n    bond o-h2\n}\n\nspecies molecule "Dimero" {\n    2x atom "Agua" as a\n    bond a1-a2\n}\n',
                "opcoes": [],
                "saida": 2,
            },
        ],
    },
    {
        "id": "atomos",
        "titulo": "Átomos: nomes, quantidade e carga",
        "texto": [
            "atom declara um átomo pelo símbolo do elemento (primeira letra maiúscula). as dá um nome a ele.",
            "Um multiplicador como 4x cria vários átomos de uma vez. Com nome, o nome vira prefixo: "
            "4x atom H as h cria h1, h2, h3 e h4.",
            "A carga formal fica entre parênteses logo depois do elemento: atom N(+1), atom O(-1).",
        ],
        "exemplos": [
            {
                "titulo": "Metano com nomes",
                "explicacao": "Cada H tem um nome próprio, então cada ligação aponta exatamente para um átomo.",
                "codigo": 'species molecule "Methane" {\n    atom C as c\n    4x atom H as h\n\n    bond c-h1\n    bond c-h2\n    bond c-h3\n    bond c-h4\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Variação: o mesmo metano em três linhas",
                "explicacao": "Sem nomes, bond C-H x4 repete a ligação usando, a cada vez, o próximo H ainda não citado.",
                "codigo": 'species molecule "Methane" {\n    atom C\n    4x atom H\n    bond C-H x4\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
        ],
    },
    {
        "id": "ligacoes",
        "titulo": "Ligações simples, duplas e triplas",
        "texto": [
            "O operador diz quantos pares de elétrons os dois átomos compartilham: - simples, = dupla, # tripla.",
            "A soma das ordens das ligações de cada átomo precisa bater com a valência do elemento: "
            "C faz 4, N faz 3, O faz 2, H faz 1.",
        ],
        "exemplos": [
            {
                "titulo": "Dióxido de carbono: duas duplas",
                "explicacao": "O carbono soma 2 + 2 = 4; cada oxigênio soma 2.",
                "codigo": 'species molecule "Carbon dioxide" {\n    atom C\n    atom O as o1\n    atom O as o2\n\n    bond o1=C\n    bond C=o2\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Nitrogênio: uma tripla",
                "explicacao": "Cada N soma 3 com uma única ligação tripla.",
                "codigo": 'species molecule "Nitrogen" {\n    atom N as n1\n    atom N as n2\n    bond n1#n2\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Eteno: dupla entre carbonos",
                "explicacao": "Cada carbono soma 2 (a dupla) + 1 + 1 (dois H) = 4.",
                "codigo": 'species molecule "Ethene" {\n    atom C as c1\n    atom C as c2\n    4x atom H as h\n\n    bond c1=c2\n    bond c1-h1\n    bond c1-h2\n    bond c2-h3\n    bond c2-h4\n}\n',
                "opcoes": [],
                "saida": 0,
            },
        ],
    },
    {
        "id": "atomicas",
        "titulo": "Átomos isolados e íons monoatômicos",
        "texto": [
            "Pela IUPAC, molécula é uma entidade eletricamente neutra com mais de um átomo. "
            "Um átomo sozinho é um átomo; com carga, é um íon monoatômico.",
            "Para isso há dois tipos de espécie: species atom (um átomo neutro, sem ligações) e "
            "species monatomic_ion, que exige charge. Declarar um átomo só como molecule gera o aviso SPEC-003.",
        ],
        "exemplos": [
            {
                "titulo": "Átomo isolado de argônio",
                "explicacao": "Gases nobres existem como átomos isolados. No playground, uma espécie de um átomo só é desenhada pelo modelo de Bohr.",
                "codigo": 'species atom "Argon" {\n    atom Ar\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Íon monoatômico: cloreto",
                "explicacao": "Cl com um elétron a mais: carga -1 no átomo e no cabeçalho.",
                "codigo": 'species monatomic_ion "Chloride" charge -1 {\n    atom Cl(-1)\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Aviso: um átomo só declarado como molécula",
                "explicacao": "Compila, mas o compilador lembra a definição da IUPAC e sugere species atom.",
                "codigo": 'species molecule "Neon" {\n    atom Ne\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Erro: species atom com dois átomos",
                "explicacao": "Dois átomos ligados formam uma molécula (di-hidrogênio), não um átomo.",
                "codigo": 'species atom "Dihydrogen" {\n    2x atom H\n    bond H-H\n}\n',
                "opcoes": [],
                "saida": 2,
            },
        ],
    },
    {
        "id": "tipos_ligacao",
        "titulo": "Tipos de ligação: covalente, iônica, coordenada e metálica",
        "texto": [
            "O operador descreve a ordem da ligação (- = #), a coordenação (->) ou a ligação metálica (~). "
            "O tipo químico — covalente apolar, covalente polar ou iônica — o compilador deduz pela diferença de "
            "eletronegatividade (Δχ) entre os dois átomos e mostra em --modelo.",
            "Os limites são os da convenção didática de Pauling: Δχ < 0,4 apolar, até 1,7 polar, acima de 1,7 iônica. "
            "É uma escala contínua, não uma fronteira rígida, e os limites ficam em regras/classificacao_ligacoes.json.",
            "Na ligação coordenada o par vem de um só átomo; a IUPAC considera “dativa” um sinônimo obsoleto. "
            "Ela também recebe a classificação por Δχ.",
        ],
        "exemplos": [
            {
                "titulo": "Covalente apolar: di-hidrogênio",
                "explicacao": "Átomos iguais: Δχ = 0.",
                "codigo": 'species molecule "Dihydrogen" {\n    2x atom H\n    bond H-H\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Covalente polar: cloreto de hidrogênio",
                "explicacao": "Δχ = 0,96: o Cl atrai mais o par compartilhado.",
                "codigo": 'species molecule "Hydrogen chloride" {\n    atom H\n    atom Cl\n    bond H-Cl\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Iônica: cloreto de sódio",
                "explicacao": "Δχ = 2,23, acima de 1,7: caráter predominantemente iônico. O tipo ionic_solid indica que o grafo é o motivo de um cristal.",
                "codigo": 'species ionic_solid "Sodium chloride" {\n    atom Na\n    atom Cl\n    bond Na-Cl\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Metálica: sódio metálico",
                "explicacao": "~ marca a ligação metálica, sempre com o aviso METAL-002.",
                "codigo": 'species metallic_solid "Sodium" {\n    atom Na as na1\n    atom Na as na2\n    bond na1~na2\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
        ],
    },
    {
        "id": "cargas",
        "titulo": "Cargas e íons",
        "texto": [
            "Um íon molecular declara a carga total no cabeçalho: species molecular_ion \"Nome\" charge +1.",
            "O compilador soma as cargas formais dos átomos e confere com a carga total (CARGA-002). "
            "A carga também muda a valência aceita: N(+1) faz 4 ligações, O(-1) faz 1.",
        ],
        "exemplos": [
            {
                "titulo": "Amônio: N com carga +1",
                "explicacao": "Com carga +1, o nitrogênio aceita quatro ligações.",
                "codigo": 'species molecular_ion "Ammonium" charge +1 {\n    atom N(+1)\n    4x atom H\n    bond N-H x4\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Erro: carga total que não bate",
                "explicacao": "O cabeçalho promete +1, mas nenhum átomo tem carga: a soma das cargas formais é 0.",
                "codigo": 'species molecular_ion "Wrong" charge +1 {\n    atom N\n    3x atom H\n    bond N-H x3\n}\n',
                "opcoes": [],
                "saida": 2,
            },
        ],
    },
    {
        "id": "coordenada",
        "titulo": "Ligação coordenada",
        "texto": [
            "Na ligação coordenada (->) os dois elétrons do par vêm do mesmo átomo, o doador. "
            "A seta vai do doador para o receptor.",
            "O compilador confere se o doador tem par livre e se o receptor tem espaço eletrônico.",
        ],
        "exemplos": [
            {
                "titulo": "Amônia doando o par ao trifluoreto de boro",
                "explicacao": "N (com par livre) doa para B (com orbital vazio); as cargas formais registram a doação.",
                "codigo": 'species molecule "Ammonia borane trifluoride" {\n    atom N(+1)\n    atom B(-1)\n    3x atom H as h\n    3x atom F as f\n\n    bond N-h1\n    bond N-h2\n    bond N-h3\n    bond B-f1\n    bond B-f2\n    bond B-f3\n    bond N->B\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
        ],
    },
    {
        "id": "aneis",
        "titulo": "Anéis",
        "texto": [
            "ring lista, na ordem do ciclo, os nomes dos átomos de um anel (pelo menos três).",
            "Se o grafo tem um ciclo que não foi declarado, o compilador avisa (RING-004), mas compila.",
        ],
        "exemplos": [
            {
                "titulo": "Ciclopropano declarado",
                "explicacao": "Os três carbonos formam o ciclo c1 → c2 → c3 → c1.",
                "codigo": 'species molecule "Cyclopropane" {\n    3x atom C as c\n    6x atom H as h\n\n    bond c1-c2\n    bond c2-c3\n    bond c3-c1\n    bond c1-h1\n    bond c1-h2\n    bond c2-h3\n    bond c2-h4\n    bond c3-h5\n    bond c3-h6\n\n    ring c1 c2 c3\n}\n',
                "opcoes": [],
                "saida": 0,
            },
            {
                "titulo": "Variação: ciclo sem ring gera aviso",
                "explicacao": "A molécula é válida, mas o ciclo não foi declarado: aparece o aviso RING-004 e a saída continua 0.",
                "codigo": 'species molecule "Cyclopropane" {\n    3x atom C as c\n    6x atom H as h\n\n    bond c1-c2\n    bond c2-c3\n    bond c3-c1\n    bond c1-h1\n    bond c1-h2\n    bond c2-h3\n    bond c2-h4\n    bond c3-h5\n    bond c3-h6\n}\n',
                "opcoes": [],
                "saida": 0,
            },
        ],
    },
    {
        "id": "radicais",
        "titulo": "Radicais",
        "texto": [
            "unpaired N, logo depois do nome, declara elétrons desemparelhados. "
            "Sem a declaração, uma contagem ímpar de elétrons gera aviso (RAD-001).",
        ],
        "exemplos": [
            {
                "titulo": "Óxido nítrico: um elétron desemparelhado",
                "explicacao": "NO tem 11 elétrons de valência; unpaired 1 declara o radical. O N fica com só duas ligações, e o elétron desemparelhado explica a ligação que falta: por isso não há aviso VAL-002. Sem o unpaired, o compilador avisaria RAD-001 e VAL-002.",
                "codigo": 'species molecule "Nitric oxide" unpaired 1 {\n    atom N\n    atom O\n    bond N=O\n}\n',
                "opcoes": [],
                "saida": 0,
            },
        ],
    },
    {
        "id": "estereo",
        "titulo": "Configuração espacial (stereo)",
        "texto": [
            "stereo declara a configuração de um elemento estereogênico: R ou S num centro, E ou Z numa dupla, "
            "Ra ou Sa num aleno e cis ou trans entre dois átomos de um anel.",
            "A semântica confere se o átomo ou a ligação é de fato estereogênico. Declarar R num carbono comum é erro.",
        ],
        "exemplos": [
            {
                "titulo": "(E)-1,2-dicloroeteno",
                "explicacao": "Os dois Cl ficam em lados opostos da dupla.",
                "codigo": 'species molecule "(E)-1,2-Dichloroethene" {\n    atom C as c1\n    atom C as c2\n    atom Cl as cl1\n    atom Cl as cl2\n    2x atom H as h\n\n    bond c1=c2\n    bond c1-cl1\n    bond c2-cl2\n    bond c1-h1\n    bond c2-h2\n\n    stereo c1=c2 E\n}\n',
                "opcoes": ["--estereo"],
                "saida": 0,
            },
            {
                "titulo": "Erro: R num carbono que não é estereogênico",
                "explicacao": "O carbono central do propano tem dois H iguais: não há configuração a declarar.",
                "codigo": 'species molecule "Propane" {\n    atom C as c1\n    atom C as c2\n    atom C as c3\n    8x atom H as h\n\n    bond c1-c2\n    bond c2-c3\n    bond c1-h1\n    bond c1-h2\n    bond c1-h3\n    bond c2-h4\n    bond c2-h5\n    bond c3-h6\n    bond c3-h7\n    bond c3-h8\n\n    stereo c2 R\n}\n',
                "opcoes": [],
                "saida": 2,
            },
        ],
    },
    {
        "id": "erros",
        "titulo": "Erros semânticos",
        "texto": [
            "A semântica é o centro da linguagem: um programa pode estar perfeitamente escrito e ainda assim "
            "descrever uma molécula impossível. Nesses casos o compilador para com código 2 e aponta linha, coluna e motivo.",
        ],
        "exemplos": [
            {
                "titulo": "Valência excedida",
                "explicacao": "Cinco ligações no carbono: a soma das ordens passa do máximo 4 (VAL-001). O aviso RAD-001 vem junto porque a contagem de elétrons ficou ímpar.",
                "codigo": 'species molecule "Impossible" {\n    atom C as c\n    5x atom H as h\n    bond c-h1\n    bond c-h2\n    bond c-h3\n    bond c-h4\n    bond c-h5\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Átomo não declarado",
                "explicacao": "A ligação cita h3, mas só h1 e h2 existem.",
                "codigo": 'species molecule "Water" {\n    atom O as o\n    2x atom H as h\n    bond o-h1\n    bond o-h3\n}\n',
                "opcoes": [],
                "saida": 2,
            },
            {
                "titulo": "Partes desconectadas",
                "explicacao": "Duas moléculas de H2 no mesmo bloco não formam uma entidade única.",
                "codigo": 'species molecule "Two hydrogens" {\n    4x atom H as h\n    bond h1-h2\n    bond h3-h4\n}\n',
                "opcoes": [],
                "saida": 2,
            },
        ],
    },
    {
        "id": "solidos",
        "titulo": "Sólidos e ligação metálica",
        "texto": [
            "ionic_solid e metallic_solid descrevem o motivo de uma estrutura estendida. "
            "A ligação metálica usa ~ e sempre traz o aviso METAL-002: uma aresta não valida o comportamento coletivo do metal.",
        ],
        "exemplos": [
            {
                "titulo": "Cloreto de sódio",
                "explicacao": "A ligação Na-Cl é classificada como iônica pela diferença de eletronegatividade (Δχ = 2,23, acima da convenção de 1,7). O aviso SPEC-002 lembra que o grafo é só um motivo do cristal.",
                "codigo": 'species ionic_solid "Sodium chloride" {\n    atom Na\n    atom Cl\n    bond Na-Cl\n}\n',
                "opcoes": ["--modelo"],
                "saida": 0,
            },
        ],
    },
    {
        "id": "resolver",
        "titulo": "Deixar o compilador ligar os átomos",
        "texto": [
            "Com --resolver, basta declarar os átomos: o solver procura a estrutura que satisfaz as valências. "
            "Se houver mais de uma, ele recusa e pede as ligações (ou use --resolver-todas para listar).",
        ],
        "exemplos": [
            {
                "titulo": "Água só com átomos",
                "explicacao": "Só existe uma forma de ligar um O e dois H respeitando as valências.",
                "codigo": 'species molecule "Water" {\n    atom O\n    2x atom H\n}\n',
                "opcoes": ["--resolver", "--modelo"],
                "saida": 0,
            },
            {
                "titulo": "Fórmula ambígua",
                "explicacao": "C2H6O pode ser etanol ou éter dimetílico: o solver não escolhe por você.",
                "codigo": 'species molecule "C2H6O" {\n    2x atom C\n    atom O\n    6x atom H\n}\n',
                "opcoes": ["--resolver"],
                "saida": 2,
            },
        ],
    },
]
