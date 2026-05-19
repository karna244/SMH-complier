"""
Mini-C Compiler – Main Driver
Stages: Lexical → Syntax → Semantic → IR Generation
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from lexer  import tokenize
from parser import parse
from semantic import SemanticAnalyser
from ir_gen   import IRGenerator


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              MINI-C COMPILER  (Front-End)                    ║
║   Stages: Lexical | Syntax | Semantic | IR Generation        ║
╚══════════════════════════════════════════════════════════════╝
"""


def compile_file(path: str):
    print(BANNER)

    # ── Read source ─────────────────────────
    try:
        with open(path) as f:
            source = f.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    print(f"  Source file : {path}")
    print(f"  Source size : {len(source)} bytes\n")

    # ══════════════════════════════════════════
    # STAGE 1 – LEXICAL ANALYSIS
    # ══════════════════════════════════════════
    print("─" * 65)
    print("  STAGE 1 — LEXICAL ANALYSIS")
    print("─" * 65)
    tokens = tokenize(source)
    print(f"  {len(tokens)} tokens found.\n")

    fmt = "  {:<5} {:<18} {:<30} {}"
    print(fmt.format("No.", "Token Type", "Value", "Line"))
    print("  " + "-" * 60)
    for i, (ttype, val, lineno) in enumerate(tokens, 1):
        print(fmt.format(i, ttype, repr(val), lineno))

    # ══════════════════════════════════════════
    # STAGE 2 – SYNTAX ANALYSIS (Parse → AST)
    # ══════════════════════════════════════════
    print("\n" + "─" * 65)
    print("  STAGE 2 — SYNTAX ANALYSIS")
    print("─" * 65)
    ast = parse(source)
    if ast is None:
        print("  [FATAL] Parsing failed. Cannot continue.")
        sys.exit(1)
    print(f"  AST root   : {type(ast).__name__}")
    print(f"  Top-level  : {len(ast.declarations)} declaration(s)")
    _print_ast(ast)

    # ══════════════════════════════════════════
    # STAGE 3 – SEMANTIC ANALYSIS
    # ══════════════════════════════════════════
    print("\n" + "─" * 65)
    print("  STAGE 3 — SEMANTIC ANALYSIS")
    print("─" * 65)
    sem = SemanticAnalyser()
    sem.analyse(ast)
    sem.table.print_table()

    if sem.table.errors:
        print("\n  SEMANTIC ERRORS:")
        for e in sem.table.errors:
            print(f"  {e}")
        print(f"\n  {len(sem.table.errors)} semantic error(s) found. IR generation may be incomplete.")
    else:
        print("\n  ✓  No semantic errors.")

    # ══════════════════════════════════════════
    # STAGE 4 – IR GENERATION (TAC)
    # ══════════════════════════════════════════
    print("\n" + "─" * 65)
    print("  STAGE 4 — INTERMEDIATE REPRESENTATION (TAC + Quadruples)")
    print("─" * 65)
    irgen = IRGenerator()
    irgen.generate(ast)
    irgen.print_tac()
    irgen.print_quadruples()

    # Save IR to file
    out_ir   = path.replace('.mc', '_ir.txt')
    irgen.save_ir(out_ir)
    print(f"\n  IR saved to : {out_ir}")

    # Final summary
    print("\n" + "═" * 65)
    print("  COMPILATION SUMMARY")
    print("═" * 65)
    print(f"  Tokens            : {len(tokens)}")
    print(f"  Symbols declared  : {len(sem.table.all_symbols)}")
    print(f"  TAC instructions  : {len(irgen.quads)}")
    print(f"  Semantic errors   : {len(sem.table.errors)}")
    status = "SUCCESS" if not sem.table.errors else "COMPLETED WITH ERRORS"
    print(f"  Status            : {status}")
    print("═" * 65 + "\n")


def _print_ast(ast, indent=0):
    """Minimal recursive AST pretty-printer."""
    lines = []

    def walk(node, depth):
        pad = "    " * depth
        if node is None:
            return
        cls = type(node).__name__
        if cls == 'Program':
            lines.append(f"{pad}Program")
            for d in node.declarations:
                walk(d, depth + 1)
        elif cls == 'FuncDecl':
            lines.append(f"{pad}FuncDecl  {node.ret_type} {node.name}()")
            walk(node.body, depth + 1)
        elif cls == 'VarDecl':
            init = f" = ..." if node.init else ""
            lines.append(f"{pad}VarDecl   {node.var_type} {node.name}{init}")
        elif cls == 'ArrayDecl':
            lines.append(f"{pad}ArrayDecl {node.var_type} {node.name}[{node.size}]")
        elif cls == 'Block':
            lines.append(f"{pad}Block ({len(node.stmts)} stmt(s))")
            for s in node.stmts:
                walk(s, depth + 1)
        elif cls == 'IfStmt':
            lines.append(f"{pad}IfStmt")
            lines.append(f"{pad}  cond:")
            walk(node.cond, depth + 2)
            lines.append(f"{pad}  then:")
            walk(node.then_block, depth + 2)
            if node.else_block:
                lines.append(f"{pad}  else:")
                walk(node.else_block, depth + 2)
        elif cls == 'WhileStmt':
            lines.append(f"{pad}WhileStmt")
        elif cls == 'ForStmt':
            lines.append(f"{pad}ForStmt")
        elif cls == 'AssignStmt':
            lines.append(f"{pad}Assign    {node.target} = ...")
        elif cls == 'PrintStmt':
            lines.append(f"{pad}PrintStmt")
        elif cls == 'ReturnStmt':
            lines.append(f"{pad}ReturnStmt")
        elif cls == 'BinOp':
            lines.append(f"{pad}BinOp({node.op})")
            walk(node.left,  depth + 1)
            walk(node.right, depth + 1)
        elif cls == 'ID':
            lines.append(f"{pad}ID({node.name})")
        elif cls == 'IntLiteral':
            lines.append(f"{pad}Int({node.value})")
        elif cls == 'FloatLiteral':
            lines.append(f"{pad}Float({node.value})")
        else:
            lines.append(f"{pad}{cls}")

    walk(ast, 1)
    # Print first 50 lines to keep output readable
    shown = lines[:50]
    for l in shown:
        print(l)
    if len(lines) > 50:
        print(f"    ... ({len(lines) - 50} more AST lines) ...")


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'test_program.mc'
    compile_file(src)
