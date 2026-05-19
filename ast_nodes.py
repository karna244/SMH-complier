"""
AST Node definitions for the Mini-C compiler.
Each node class represents a construct in the grammar.
"""

class Node:
    """Base AST node."""
    pass


# ── Program ─────────────────────────────────
class Program(Node):
    def __init__(self, declarations):
        self.declarations = declarations   # list of top-level decls / functions

    def __repr__(self):
        return f"Program({self.declarations})"


# ── Declarations ────────────────────────────
class VarDecl(Node):
    def __init__(self, var_type, name, init=None, lineno=0):
        self.var_type = var_type   # 'int' | 'float'
        self.name     = name
        self.init     = init       # expression or None
        self.lineno   = lineno

    def __repr__(self):
        return f"VarDecl({self.var_type}, {self.name}, init={self.init})"


class ArrayDecl(Node):
    def __init__(self, var_type, name, size, lineno=0):
        self.var_type = var_type
        self.name     = name
        self.size     = size    # integer literal
        self.lineno   = lineno

    def __repr__(self):
        return f"ArrayDecl({self.var_type}, {self.name}[{self.size}])"


class FuncDecl(Node):
    def __init__(self, ret_type, name, params, body, lineno=0):
        self.ret_type = ret_type
        self.name     = name
        self.params   = params   # list of VarDecl
        self.body     = body     # Block
        self.lineno   = lineno

    def __repr__(self):
        return f"FuncDecl({self.ret_type}, {self.name}, {self.body})"


# ── Statements ───────────────────────────────
class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts

    def __repr__(self):
        return f"Block({self.stmts})"


class AssignStmt(Node):
    def __init__(self, target, expr, lineno=0):
        self.target = target   # ID string or ArrayAccess
        self.expr   = expr
        self.lineno = lineno

    def __repr__(self):
        return f"Assign({self.target} = {self.expr})"


class IfStmt(Node):
    def __init__(self, cond, then_block, else_block=None, lineno=0):
        self.cond       = cond
        self.then_block = then_block
        self.else_block = else_block
        self.lineno     = lineno

    def __repr__(self):
        return f"If({self.cond}, {self.then_block}, {self.else_block})"


class WhileStmt(Node):
    def __init__(self, cond, body, lineno=0):
        self.cond   = cond
        self.body   = body
        self.lineno = lineno

    def __repr__(self):
        return f"While({self.cond}, {self.body})"


class ForStmt(Node):
    def __init__(self, init, cond, update, body, lineno=0):
        self.init   = init
        self.cond   = cond
        self.update = update
        self.body   = body
        self.lineno = lineno

    def __repr__(self):
        return f"For({self.init}; {self.cond}; {self.update})"


class ReturnStmt(Node):
    def __init__(self, expr=None, lineno=0):
        self.expr   = expr
        self.lineno = lineno

    def __repr__(self):
        return f"Return({self.expr})"


class PrintStmt(Node):
    def __init__(self, expr, lineno=0):
        self.expr   = expr
        self.lineno = lineno

    def __repr__(self):
        return f"Print({self.expr})"


# ── Expressions ──────────────────────────────
class BinOp(Node):
    def __init__(self, op, left, right, lineno=0):
        self.op     = op
        self.left   = left
        self.right  = right
        self.lineno = lineno

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class UnaryOp(Node):
    def __init__(self, op, operand, lineno=0):
        self.op      = op
        self.operand = operand
        self.lineno  = lineno

    def __repr__(self):
        return f"UnaryOp({self.op}{self.operand})"


class ID(Node):
    def __init__(self, name, lineno=0):
        self.name   = name
        self.lineno = lineno

    def __repr__(self):
        return f"ID({self.name})"


class ArrayAccess(Node):
    def __init__(self, name, index, lineno=0):
        self.name   = name
        self.index  = index
        self.lineno = lineno

    def __repr__(self):
        return f"ArrayAccess({self.name}[{self.index}])"


class IntLiteral(Node):
    def __init__(self, value, lineno=0):
        self.value  = value
        self.lineno = lineno

    def __repr__(self):
        return f"Int({self.value})"


class FloatLiteral(Node):
    def __init__(self, value, lineno=0):
        self.value  = value
        self.lineno = lineno

    def __repr__(self):
        return f"Float({self.value})"
