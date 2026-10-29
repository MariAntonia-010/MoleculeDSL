grammar MoleculeDSL;

// ---------- PARSER ----------

programa
    : molecula EOF
    ;

molecula
    : MOLECULE TEXTO ABRE_CHAVE comando* FECHA_CHAVE
    ;

comando
    : atomo
    | ligacao
    | anel
    ;

// Ex.: atom O, 4x atom H, atom N(+1), atom C as c1
atomo
    : MULTIPLICADOR_ATOMO? ATOM IDENT carga? (AS NOME)?
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

// ---------- LEXER ----------

// Palavras-chave (antes de NOME, para vencer no empate)
MOLECULE : 'molecule' ;
ATOM     : 'atom' ;
BOND     : 'bond' ;
AS       : 'as' ;
RING     : 'ring' ;

// Quantificadores
MULTIPLICADOR_ATOMO
    : [0-9]+ 'x'
    ;

// Antes de NOME: x4 é sempre repetição
REPETICAO_LIGACAO
    : 'x' [0-9]+
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
FECHA_CHAVE : '}' ;

// Comentários
COMENTARIO
    : '//' ~[\r\n]* -> skip
    ;

// Espaços em branco
ESPACO
    : [ \t\r\n]+ -> skip
    ;
