"""
Mini-C Intermediate Representation (IR) Generator
Produces Three-Address Code (TAC) / Quadruples.
"""

from ast_nodes import *


# ─────────────────────────────────────────────
# Quadruple: (op, arg1, arg2, result)
# ─────────────────────────────────────────────
class Quad:
    def __init__(self, op, arg1='', arg2='', result=''):
        self.op     = op
        self.arg1   = arg1
        self.arg2   = arg2
        self.result = result

    def __repr__(self):
        return f"({self.op:<8}, {str(self.arg1):<12}, {str(self.arg2):<12}, {str(self.result)})"

    def tac_str(self) -> str:
        """Human-readable TAC."""
        op = self.op
        a1, a2, res = str(self.arg1), str(self.arg2), str(self.result)

        if op in ('+', '-', '*', '/'):
            return f"{res} = {a1} {op} {a2}"
        if op in ('<', '>', '<=', '>=', '==', '!='):
            return f"{res} = {a1} {op} {a2}"
        if op == '=':
            return f"{res} = {a1}"
        if op == 'UMINUS':
            return f"{res} = -{a1}"
        if op == 'ARRAY_LOAD':
            return f"{res} = {a1}[{a2}]"
        if op == 'ARRAY_STORE':
            return f"{res}[{a2}] = {a1}"
        if op == 'LABEL':
            return f"\n{res}:"
        if op == 'GOTO':
            return f"GOTO {res}"
        if op == 'IF_FALSE':
            return f"IF_FALSE {a1} GOTO {res}"
        if op == 'PRINT':
            return f"PRINT {a1}"
        if op == 'FUNC_BEGIN':
            return f"\n--- BEGIN FUNCTION {res} ---"
        if op == 'FUNC_END':
            return f"--- END FUNCTION {res} ---"
        if op == 'RETURN':
            return f"RETURN {a1}" if a1 else "RETURN"
        if op == 'PARAM':
            return f"PARAM {a1}"
        # fallback
        return repr(self)


# ─────────────────────────────────────────────
# IR Generator
# ─────────────────────────────────────────────
class IRGenerator:
    def __init__(self):
        self.quads:   list[Quad] = []
        self._tmp_cnt   = 0
        self._lbl_cnt   = 0

    # ── Helpers ─────────────────────────────
    def _new_temp(self) -> str:
        self._tmp_cnt += 1
        return f"t{self._tmp_cnt}"

    def _new_label(self) -> str:
        self._lbl_cnt += 1
        return f"L{self._lbl_cnt}"

    def _emit(self, op, arg1='', arg2='', result='') -> Quad:
        q = Quad(op, arg1, arg2, result)
        self.quads.append(q)
        return q

    # ── Top-level ────────────────────────────
    def generate(self, ast: Program):
        for node in ast.declarations:
            self._gen_decl(node)

    def _gen_decl(self, node):
        if isinstance(node, VarDecl):
            if node.init is not None:
                val = self._gen_expr(node.init)
                self._emit('=', val, '', node.name)
        elif isinstance(node, ArrayDecl):
            self._emit('ARRAY_DECL', node.var_type, node.size, node.name)
        elif isinstance(node, FuncDecl):
            self._emit('FUNC_BEGIN', '', '', node.name)
            for param in node.params:
                self._emit('PARAM', param.name)
            self._gen_block(node.body)
            self._emit('FUNC_END', '', '', node.name)

    # ── Block / Statements ───────────────────
    def _gen_block(self, node: Block):
        for stmt in node.stmts:
            self._gen_stmt(stmt)

    def _gen_stmt(self, node):
        if isinstance(node, VarDecl):
            if node.init is not None:
                val = self._gen_expr(node.init)
                self._emit('=', val, '', node.name)
        elif isinstance(node, ArrayDecl):
            self._emit('ARRAY_DECL', node.var_type, node.size, node.name)
        elif isinstance(node, AssignStmt):
            self._gen_assign(node)
        elif isinstance(node, IfStmt):
            self._gen_if(node)
        elif isinstance(node, WhileStmt):
            self._gen_while(node)
        elif isinstance(node, ForStmt):
            self._gen_for(node)
        elif isinstance(node, PrintStmt):
            val = self._gen_expr(node.expr)
            self._emit('PRINT', val)
        elif isinstance(node, ReturnStmt):
            if node.expr:
                val = self._gen_expr(node.expr)
                self._emit('RETURN', val)
            else:
                self._emit('RETURN')

    def _gen_assign(self, node: AssignStmt):
        rhs = self._gen_expr(node.expr)
        if isinstance(node.target, str):
            self._emit('=', rhs, '', node.target)
        elif isinstance(node.target, ArrayAccess):
            idx = self._gen_expr(node.target.index)
            self._emit('ARRAY_STORE', rhs, idx, node.target.name)

    def _gen_if(self, node: IfStmt):
        cond = self._gen_expr(node.cond)
        false_lbl = self._new_label()
        end_lbl   = self._new_label()

        self._emit('IF_FALSE', cond, '', false_lbl)
        self._gen_block(node.then_block)
        if node.else_block:
            self._emit('GOTO', '', '', end_lbl)
        self._emit('LABEL', '', '', false_lbl)
        if node.else_block:
            self._gen_block(node.else_block)
            self._emit('LABEL', '', '', end_lbl)

    def _gen_while(self, node: WhileStmt):
        start_lbl = self._new_label()
        end_lbl   = self._new_label()

        self._emit('LABEL', '', '', start_lbl)
        cond = self._gen_expr(node.cond)
        self._emit('IF_FALSE', cond, '', end_lbl)
        self._gen_block(node.body)
        self._emit('GOTO', '', '', start_lbl)
        self._emit('LABEL', '', '', end_lbl)

    def _gen_for(self, node: ForStmt):
        # Initializer
        self._gen_stmt(node.init)
        start_lbl = self._new_label()
        end_lbl   = self._new_label()

        self._emit('LABEL', '', '', start_lbl)
        cond = self._gen_expr(node.cond)
        self._emit('IF_FALSE', cond, '', end_lbl)
        self._gen_block(node.body)
        self._gen_stmt(node.update)
        self._emit('GOTO', '', '', start_lbl)
        self._emit('LABEL', '', '', end_lbl)

    # ── Expressions → return temp/name ───────
    def _gen_expr(self, node) -> str:
        if isinstance(node, IntLiteral):
            return str(node.value)
        if isinstance(node, FloatLiteral):
            return str(node.value)
        if isinstance(node, ID):
            return node.name
        if isinstance(node, ArrayAccess):
            idx = self._gen_expr(node.index)
            tmp = self._new_temp()
            self._emit('ARRAY_LOAD', node.name, idx, tmp)
            return tmp
        if isinstance(node, UnaryOp) and node.op == '-':
            val = self._gen_expr(node.operand)
            tmp = self._new_temp()
            self._emit('UMINUS', val, '', tmp)
            return tmp
        if isinstance(node, BinOp):
            left  = self._gen_expr(node.left)
            right = self._gen_expr(node.right)
            tmp   = self._new_temp()
            self._emit(node.op, left, right, tmp)
            return tmp
        return '??'

    # ── Output ───────────────────────────────
    def print_tac(self):
        print("\n" + "═" * 65)
        print("  INTERMEDIATE REPRESENTATION  (Three-Address Code / TAC)")
        print("═" * 65)
        for i, q in enumerate(self.quads):
            print(f"  {i+1:>3}:  {q.tac_str()}")
        print("═" * 65)

    def print_quadruples(self):
        print("\n" + "═" * 65)
        print("  QUADRUPLES  (op, arg1, arg2, result)")
        print("═" * 65)
        hdr = "  {:<5} {:<10} {:<14} {:<14} {}"
        print(hdr.format("No.", "OP", "ARG1", "ARG2", "RESULT"))
        print("─" * 65)
        for i, q in enumerate(self.quads):
            print(hdr.format(i+1, q.op, str(q.arg1), str(q.arg2), str(q.result)))
        print("═" * 65)

    def save_ir(self, path: str):
        with open(path, 'w') as f:
            f.write("THREE-ADDRESS CODE (TAC)\n")
            f.write("=" * 65 + "\n")
            for i, q in enumerate(self.quads):
                f.write(f"  {i+1:>3}:  {q.tac_str()}\n")
            f.write("\n" + "=" * 65 + "\n")
            f.write("QUADRUPLES (op, arg1, arg2, result)\n")
            f.write("=" * 65 + "\n")
            hdr = "  {:<5} {:<10} {:<14} {:<14} {}\n"
            f.write(hdr.format("No.", "OP", "ARG1", "ARG2", "RESULT"))
            f.write("-" * 65 + "\n")
            for i, q in enumerate(self.quads):
                f.write(hdr.format(i+1, q.op, str(q.arg1), str(q.arg2), str(q.result)))
