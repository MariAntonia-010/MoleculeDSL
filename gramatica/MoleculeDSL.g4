lexer grammar MoleculeDSL;

// Palavras-chave
MOLECULE : 'molecule' ;
ATOM     : 'atom' ;
BOND     : 'bond' ;

// Quantificadores
MULTIPLICADOR_ATOMO
    : [0-9]+ 'x'
    ;

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

// Operador e delimitadores
LIGACAO     : '-' ;
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