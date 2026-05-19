"""
Mini-C Parser (Syntax Analysis)
Builds an AST using PLY (Python Lex-Yacc).
"""

import ply.yacc as yacc
from lexer import tokens, lexer
from ast_nodes import *

# ─────────────────────────────────────────────
# Operator precedence (lowest → highest)
# ─────────────────────────────────────────────
precedence = (
    ('left',  'EQ',  'NEQ'),
    ('left',  'LT',  'GT',  'LE',  'GE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

# ─────────────────────────────────────────────
# Grammar rules
# ─────────────────────────────────────────────

# Program: sequence of top-level items
def p_program(p):
    '''program : decl_list'''
    p[0] = Program(p[1])

def p_decl_list_many(p):
    '''decl_list : decl_list decl'''
    p[0] = p[1] + [p[2]]

def p_decl_list_one(p):
    '''decl_list : decl'''
    p[0] = [p[1]]

def p_decl(p):
    '''decl : var_decl
            | array_decl
            | func_decl'''
    p[0] = p[1]

# ── Variable declaration ─────────────────────
def p_var_decl_init(p):
    '''var_decl : type ID ASSIGN expr SEMI'''
    p[0] = VarDecl(p[1], p[2], init=p[4], lineno=p.lineno(2))

def p_var_decl_noinit(p):
    '''var_decl : type ID SEMI'''
    p[0] = VarDecl(p[1], p[2], lineno=p.lineno(2))

def p_array_decl(p):
    '''array_decl : type ID LBRACKET INT_LITERAL RBRACKET SEMI'''
    p[0] = ArrayDecl(p[1], p[2], p[4], lineno=p.lineno(2))

def p_type(p):
    '''type : INT
            | FLOAT'''
    p[0] = p[1]

# ── Function declaration ─────────────────────
def p_func_decl(p):
    '''func_decl : type MAIN LPAREN RPAREN block
                 | type ID LPAREN param_list RPAREN block
                 | type ID LPAREN RPAREN block'''
    if p[2] == 'main':
        p[0] = FuncDecl(p[1], 'main', [], p[5], lineno=p.lineno(2))
    elif len(p) == 7:
        p[0] = FuncDecl(p[1], p[2], p[4], p[6], lineno=p.lineno(2))
    else:
        p[0] = FuncDecl(p[1], p[2], [], p[5], lineno=p.lineno(2))

def p_param_list_many(p):
    '''param_list : param_list COMMA param'''
    p[0] = p[1] + [p[3]]

def p_param_list_one(p):
    '''param_list : param'''
    p[0] = [p[1]]

def p_param(p):
    '''param : type ID'''
    p[0] = VarDecl(p[1], p[2], lineno=p.lineno(2))

# ── Block ────────────────────────────────────
def p_block(p):
    '''block : LBRACE stmt_list RBRACE'''
    p[0] = Block(p[2])

def p_block_empty(p):
    '''block : LBRACE RBRACE'''
    p[0] = Block([])

def p_stmt_list_many(p):
    '''stmt_list : stmt_list stmt'''
    p[0] = p[1] + [p[2]]

def p_stmt_list_one(p):
    '''stmt_list : stmt'''
    p[0] = [p[1]]

# ── Statements ───────────────────────────────
def p_stmt(p):
    '''stmt : var_decl
            | array_decl
            | assign_stmt
            | if_stmt
            | while_stmt
            | for_stmt
            | return_stmt
            | print_stmt'''
    p[0] = p[1]

def p_assign_stmt_id(p):
    '''assign_stmt : ID ASSIGN expr SEMI'''
    p[0] = AssignStmt(p[1], p[3], lineno=p.lineno(1))

def p_assign_stmt_array(p):
    '''assign_stmt : ID LBRACKET expr RBRACKET ASSIGN expr SEMI'''
    p[0] = AssignStmt(ArrayAccess(p[1], p[3], lineno=p.lineno(1)), p[6], lineno=p.lineno(1))

def p_if_stmt_else(p):
    '''if_stmt : IF LPAREN expr RPAREN block ELSE block'''
    p[0] = IfStmt(p[3], p[5], p[7], lineno=p.lineno(1))

def p_if_stmt_noelse(p):
    '''if_stmt : IF LPAREN expr RPAREN block'''
    p[0] = IfStmt(p[3], p[5], lineno=p.lineno(1))

def p_while_stmt(p):
    '''while_stmt : WHILE LPAREN expr RPAREN block'''
    p[0] = WhileStmt(p[3], p[5], lineno=p.lineno(1))

def p_for_stmt(p):
    '''for_stmt : FOR LPAREN for_init SEMI expr SEMI for_update RPAREN block'''
    p[0] = ForStmt(p[3], p[5], p[7], p[9], lineno=p.lineno(1))

def p_for_init_var(p):
    '''for_init : type ID ASSIGN expr'''
    p[0] = VarDecl(p[1], p[2], init=p[4], lineno=p.lineno(2))

def p_for_init_assign(p):
    '''for_init : ID ASSIGN expr'''
    p[0] = AssignStmt(p[1], p[3], lineno=p.lineno(1))

def p_for_update(p):
    '''for_update : ID ASSIGN expr'''
    p[0] = AssignStmt(p[1], p[3], lineno=p.lineno(1))

def p_return_stmt(p):
    '''return_stmt : RETURN expr SEMI
                   | RETURN SEMI'''
    if len(p) == 4:
        p[0] = ReturnStmt(p[2], lineno=p.lineno(1))
    else:
        p[0] = ReturnStmt(lineno=p.lineno(1))

def p_print_stmt(p):
    '''print_stmt : PRINT LPAREN expr RPAREN SEMI'''
    p[0] = PrintStmt(p[3], lineno=p.lineno(1))

# ── Expressions ──────────────────────────────
def p_expr_binop(p):
    '''expr : expr PLUS   expr
            | expr MINUS  expr
            | expr TIMES  expr
            | expr DIVIDE expr
            | expr LT     expr
            | expr GT     expr
            | expr LE     expr
            | expr GE     expr
            | expr EQ     expr
            | expr NEQ    expr'''
    p[0] = BinOp(p[2], p[1], p[3], lineno=p.lineno(2))

def p_expr_uminus(p):
    '''expr : MINUS expr %prec UMINUS'''
    p[0] = UnaryOp('-', p[2], lineno=p.lineno(1))

def p_expr_paren(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]

def p_expr_id(p):
    '''expr : ID'''
    p[0] = ID(p[1], lineno=p.lineno(1))

def p_expr_array_access(p):
    '''expr : ID LBRACKET expr RBRACKET'''
    p[0] = ArrayAccess(p[1], p[3], lineno=p.lineno(1))

def p_expr_int(p):
    '''expr : INT_LITERAL'''
    p[0] = IntLiteral(p[1], lineno=p.lineno(1))

def p_expr_float(p):
    '''expr : FLOAT_LITERAL'''
    p[0] = FloatLiteral(p[1], lineno=p.lineno(1))

# ── Error recovery ───────────────────────────
def p_error(p):
    if p:
        print(f"[SYNTAX ERROR] Line {p.lineno}: Unexpected token '{p.value}' (type={p.type})")
    else:
        print("[SYNTAX ERROR] Unexpected end of input")

# ─────────────────────────────────────────────
# Build the parser
# ─────────────────────────────────────────────
parser = yacc.yacc(debug=False, write_tables=False)


def parse(source: str):
    """Parse source code and return the AST root (Program node)."""
    lexer.lineno = 1
    return parser.parse(source, lexer=lexer)
