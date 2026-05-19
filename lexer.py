"""
Mini-C Lexer (Lexical Analysis)
Uses PLY (Python Lex-Yacc) to tokenize Mini-C source code.
"""

import ply.lex as lex

# ─────────────────────────────────────────────
# Reserved keywords
# ─────────────────────────────────────────────
reserved = {
    'int':    'INT',
    'float':  'FLOAT',
    'if':     'IF',
    'else':   'ELSE',
    'while':  'WHILE',
    'for':    'FOR',
    'return': 'RETURN',
    'print':  'PRINT',
    'main':   'MAIN',
}

# ─────────────────────────────────────────────
# Token list
# ─────────────────────────────────────────────
tokens = [
    # Literals
    'INT_LITERAL', 'FLOAT_LITERAL',
    # Identifiers
    'ID',
    # Operators
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    # Relational
    'LT', 'GT', 'LE', 'GE', 'EQ', 'NEQ',
    # Assignment
    'ASSIGN',
    # Delimiters
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'SEMI', 'COMMA',
] + list(reserved.values())

# ─────────────────────────────────────────────
# Simple token rules
# ─────────────────────────────────────────────
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_LT        = r'<'
t_GT        = r'>'
t_LE        = r'<='
t_GE        = r'>='
t_EQ        = r'=='
t_NEQ       = r'!='
t_ASSIGN    = r'='
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMI      = r';'
t_COMMA     = r','

# Ignored whitespace
t_ignore = ' \t'

# ─────────────────────────────────────────────
# Complex token rules
# ─────────────────────────────────────────────
def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_COMMENT(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_LINE_COMMENT(t):
    r'//.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"[LEXER ERROR] Line {t.lineno}: Invalid character '{t.value[0]}'")
    t.lexer.skip(1)

# ─────────────────────────────────────────────
# Build the lexer
# ─────────────────────────────────────────────
lexer = lex.lex()


def tokenize(source: str) -> list:
    """Return list of (type, value, line) tuples for the source."""
    lexer.input(source)
    lexer.lineno = 1
    token_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        token_list.append((tok.type, tok.value, tok.lineno))
    return token_list
