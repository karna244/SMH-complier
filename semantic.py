"""
Mini-C Semantic Analysis
- Symbol Table management (with scoping)
- Type checking
"""

from ast_nodes import *


# ─────────────────────────────────────────────
# Symbol Table
# ─────────────────────────────────────────────
class Symbol:
    def __init__(self, name, sym_type, scope, lineno=0, is_array=False, array_size=None):
        self.name       = name
        self.sym_type   = sym_type    # 'int' | 'float'
        self.scope      = scope       # scope name string
        self.lineno     = lineno
        self.is_array   = is_array
        self.array_size = array_size

    def __repr__(self):
        arr = f"[{self.array_size}]" if self.is_array else ""
        return f"Symbol({self.name}{arr}: {self.sym_type}, scope={self.scope}, line={self.lineno})"


class SymbolTable:
    def __init__(self):
        # List of scope dicts; last entry = current (innermost) scope
        self.scopes: list[dict] = [{}]      # global scope first
        self.scope_names: list[str] = ['global']
        self.all_symbols: list[Symbol] = []  # flat list for reporting
        self.errors: list[str] = []

    # ── Scope management ────────────────────
    def push_scope(self, name: str):
        self.scopes.append({})
        self.scope_names.append(name)

    def pop_scope(self):
        self.scopes.pop()
        self.scope_names.pop()

    @property
    def current_scope(self) -> str:
        return self.scope_names[-1]

    # ── Symbol operations ───────────────────
    def declare(self, name: str, sym_type: str, lineno=0,
                is_array=False, array_size=None) -> bool:
        if name in self.scopes[-1]:
            self.errors.append(
                f"[SEMANTIC ERROR] Line {lineno}: '{name}' already declared in scope '{self.current_scope}'"
            )
            return False
        sym = Symbol(name, sym_type, self.current_scope, lineno, is_array, array_size)
        self.scopes[-1][name] = sym
        self.all_symbols.append(sym)
        return True

    def lookup(self, name: str) -> Symbol | None:
        # Walk inward → outward
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_type(self, name: str, lineno=0) -> str | None:
        sym = self.lookup(name)
        if sym is None:
            self.errors.append(
                f"[SEMANTIC ERROR] Line {lineno}: Undeclared identifier '{name}'"
            )
            return None
        return sym.sym_type

    # ── Pretty print ────────────────────────
    def print_table(self):
        print("\n" + "═" * 65)
        print("  SYMBOL TABLE")
        print("═" * 65)
        fmt = "  {:<20} {:<10} {:<12} {:<8} {}"
        print(fmt.format("Name", "Type", "Scope", "Line", "Array"))
        print("─" * 65)
        for sym in self.all_symbols:
            arr_info = f"[{sym.array_size}]" if sym.is_array else "-"
            print(fmt.format(sym.name, sym.sym_type, sym.scope, sym.lineno, arr_info))
        print("═" * 65)

    def print_errors(self):
        if self.errors:
            print("\n" + "─" * 65)
            for e in self.errors:
                print(e)


# ─────────────────────────────────────────────
# Semantic Analyser
# ─────────────────────────────────────────────
class SemanticAnalyser:
    def __init__(self):
        self.table = SymbolTable()
        self._errors = self.table.errors   # alias

    def analyse(self, ast: Program):
        self._visit_program(ast)

    # ── Visitors ────────────────────────────
    def _visit_program(self, node: Program):
        for decl in node.declarations:
            self._visit_decl(decl)

    def _visit_decl(self, node):
        if isinstance(node, VarDecl):
            self._visit_var_decl(node)
        elif isinstance(node, ArrayDecl):
            self._visit_array_decl(node)
        elif isinstance(node, FuncDecl):
            self._visit_func_decl(node)

    def _visit_var_decl(self, node: VarDecl):
        self.table.declare(node.name, node.var_type, node.lineno)
        if node.init is not None:
            init_type = self._expr_type(node.init)
            if init_type and init_type != node.var_type:
                # Allow int→float implicit coercion
                if not (node.var_type == 'float' and init_type == 'int'):
                    self._errors.append(
                        f"[SEMANTIC ERROR] Line {node.lineno}: Type mismatch in initialization of "
                        f"'{node.name}': expected {node.var_type}, got {init_type}"
                    )

    def _visit_array_decl(self, node: ArrayDecl):
        self.table.declare(node.name, node.var_type, node.lineno,
                           is_array=True, array_size=node.size)

    def _visit_func_decl(self, node: FuncDecl):
        self.table.declare(node.name, node.ret_type, node.lineno)
        self.table.push_scope(node.name)
        for param in node.params:
            self.table.declare(param.name, param.var_type, param.lineno)
        self._visit_block(node.body)
        self.table.pop_scope()

    def _visit_block(self, node: Block):
        self.table.push_scope(f"{self.table.current_scope}::block")
        for stmt in node.stmts:
            self._visit_stmt(stmt)
        self.table.pop_scope()

    def _visit_stmt(self, node):
        if isinstance(node, VarDecl):
            self._visit_var_decl(node)
        elif isinstance(node, ArrayDecl):
            self._visit_array_decl(node)
        elif isinstance(node, AssignStmt):
            self._visit_assign(node)
        elif isinstance(node, IfStmt):
            self._visit_if(node)
        elif isinstance(node, WhileStmt):
            self._visit_while(node)
        elif isinstance(node, ForStmt):
            self._visit_for(node)
        elif isinstance(node, PrintStmt):
            self._expr_type(node.expr)
        elif isinstance(node, ReturnStmt):
            if node.expr:
                self._expr_type(node.expr)

    def _visit_assign(self, node: AssignStmt):
        rhs_type = self._expr_type(node.expr)
        if isinstance(node.target, str):
            lhs_type = self.table.lookup_type(node.target, node.lineno)
            if lhs_type and rhs_type and lhs_type != rhs_type:
                if not (lhs_type == 'float' and rhs_type == 'int'):
                    self._errors.append(
                        f"[SEMANTIC ERROR] Line {node.lineno}: Type mismatch in assignment to "
                        f"'{node.target}': expected {lhs_type}, got {rhs_type}"
                    )
        elif isinstance(node.target, ArrayAccess):
            self.table.lookup_type(node.target.name, node.lineno)
            self._expr_type(node.target.index)

    def _visit_if(self, node: IfStmt):
        self._expr_type(node.cond)
        self._visit_block(node.then_block)
        if node.else_block:
            self._visit_block(node.else_block)

    def _visit_while(self, node: WhileStmt):
        self._expr_type(node.cond)
        self._visit_block(node.body)

    def _visit_for(self, node: ForStmt):
        self.table.push_scope(f"{self.table.current_scope}::for")
        self._visit_stmt(node.init)
        self._expr_type(node.cond)
        self._visit_stmt(node.update)
        # visit body statements directly (avoid double scope push)
        for stmt in node.body.stmts:
            self._visit_stmt(stmt)
        self.table.pop_scope()

    # ── Type inference ───────────────────────
    def _expr_type(self, node) -> str | None:
        if isinstance(node, IntLiteral):
            return 'int'
        if isinstance(node, FloatLiteral):
            return 'float'
        if isinstance(node, ID):
            return self.table.lookup_type(node.name, node.lineno)
        if isinstance(node, ArrayAccess):
            base = self.table.lookup(node.name)
            if base is None:
                self._errors.append(
                    f"[SEMANTIC ERROR] Line {node.lineno}: Undeclared array '{node.name}'"
                )
                return None
            if not base.is_array:
                self._errors.append(
                    f"[SEMANTIC ERROR] Line {node.lineno}: '{node.name}' is not an array"
                )
            self._expr_type(node.index)
            return base.sym_type
        if isinstance(node, BinOp):
            lt = self._expr_type(node.left)
            rt = self._expr_type(node.right)
            if lt == 'float' or rt == 'float':
                return 'float'
            return 'int'
        if isinstance(node, UnaryOp):
            return self._expr_type(node.operand)
        return None
