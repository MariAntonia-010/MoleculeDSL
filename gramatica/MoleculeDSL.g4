grammar MoleculeDSL;

// ---------- PARSER ----------

programa
    : molecula EOF
    ;

molecula
    : cabecalho desemparelhados? ABRE_CHAVE comando* FECHA_CHAVE
    ;

cabecalho
    : MOLECULE TEXTO
    | SPECIES MOLECULE TEXTO
    | SPECIES MOLECULAR_ION TEXTO cargaEspecie
    | SPECIES ATOM TEXTO
    | SPECIES MONATOMIC_ION TEXTO cargaEspecie
    | SPECIES IONIC_SOLID TEXTO
    | SPECIES COVALENT_NETWORK TEXTO
    | SPECIES METALLIC_SOLID TEXTO
    ;

cargaEspecie
    : CHARGE sinal INTEIRO
    ;

desemparelhados
    : UNPAIRED INTEIRO
    ;

comando
    : atomo
    | ligacao
    | anel
    | estereo
    | configuracao
    ;

// Ex.: atom O, 4x atom H, atom N(+1), atom C as c1, atom 13C (número de
// massa antes do símbolo, como na notação de nuclídeo da IUPAC)
atomo
    : MULTIPLICADOR_ATOMO? ATOM INTEIRO? IDENT carga? (AS NOME)?
    ;

// O sinal negativo reaproveita o token LIGACAO
carga
    : ABRE_PAREN sinal INTEIRO FECHA_PAREN
    ;

sinal
    : MAIS
    | LIGACAO
    ;

// Ex.: bond H-O, bond C-H x4, bond c1=c2, bond N->B
ligacao
    : BOND referencia operador referencia REPETICAO_LIGACAO?
    ;

// Símbolo de elemento ou nome de átomo
referencia
    : IDENT
    | NOME
    ;

operador
    : LIGACAO
    | DUPLA
    | TRIPLA
    | COORDENADA
    | METALICA
    ;

// Um anel precisa de pelo menos três átomos
anel
    : RING NOME NOME NOME+
    ;

// Configuração: stereo c2 R, stereo c2=c3 Z, stereo c2 Sa (aleno, pelo
// átomo central), stereo c1-c7 Ra (eixo de biarila), stereo c1 c4 trans
estereo
    : STEREO referencia (operador? referencia)? descritor
    ;

// R, S, E, Z, Ra, Sa são IDENT; r, s, cis, trans são NOME
descritor
    : IDENT
    | NOME
    ;

// Configuração eletrônica de um átomo isolado ou íon monoatômico:
// configuration c [He] 2s2 2p2. O núcleo sozinho também vale, como no
// Na+ isoeletrônico do neônio: configuration na [Ne]
configuracao
    : CONFIGURATION referencia (nucleo SUBCAMADA* | SUBCAMADA+)
    ;

// Núcleo de gás nobre: [He], [Ne], [Ar], [Kr], [Xe], [Rn]
nucleo
    : ABRE_COLCHETE IDENT FECHA_COLCHETE
    ;

// ---------- LEXER ----------

// Palavras-chave (antes de NOME, para vencer no empate)
MOLECULE : 'molecule' ;
SPECIES  : 'species' ;
MOLECULAR_ION    : 'molecular_ion' ;
MONATOMIC_ION    : 'monatomic_ion' ;
IONIC_SOLID      : 'ionic_solid' ;
COVALENT_NETWORK : 'covalent_network' ;
METALLIC_SOLID   : 'metallic_solid' ;
CHARGE    : 'charge' ;
UNPAIRED  : 'unpaired' ;
ATOM     : 'atom' ;
BOND     : 'bond' ;
AS       : 'as' ;
RING     : 'ring' ;
STEREO   : 'stereo' ;
CONFIGURATION : 'configuration' ;

// Quantificadores
MULTIPLICADOR_ATOMO
    : [0-9]+ 'x'
    ;

// Antes de NOME: x4 é sempre repetição
REPETICAO_LIGACAO
    : 'x' [0-9]+
    ;

// Subcamada ocupada: camada (1 a 7), tipo (s, p, d, f) e elétrons, como 2p4
SUBCAMADA
    : [1-7] [spdf] [0-9]+
    ;

// Números
REAL
    : [0-9]+ '.' [0-9]+
    ;

INTEIRO
    : [0-9]+
    ;

// Texto
TEXTO
    : '"' ~["\r\n]* '"'
    ;

// Identificadores de elementos
IDENT
    : [A-Z] [a-z]?
    ;

// Nomes de átomos
NOME
    : [a-z] [a-z0-9_]*
    ;

// Operadores de ligação (-> vence - por maior casamento)
COORDENADA : '->' ;
LIGACAO    : '-' ;
DUPLA      : '=' ;
TRIPLA     : '#' ;
METALICA   : '~' ;

// Sinal de carga e delimitadores
MAIS        : '+' ;
ABRE_PAREN  : '(' ;
FECHA_PAREN : ')' ;
ABRE_CHAVE  : '{' ;
ABRE_COLCHETE  : '[' ;
FECHA_COLCHETE : ']' ;
FECHA_CHAVE : '}' ;

// Comentários
COMENTARIO
    : '//' ~[\r\n]* -> skip
    ;

// Espaços em branco
ESPACO
    : [ \t\r\n]+ -> skip
    ;
