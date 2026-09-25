"""规约 DSL → Z3 证明(A12 v0):havoc 模型(输入无约束)下判定不变量。

UNSAT → 不变量对任意输入成立(已证明);SAT → 存在违反不变量的输入,
模型即反例。DSL:变量/非负整数常量、+ - *、( ) 与 >= <= > < == !=。
Solidity uint 为无符号语义,比较用 UGE/ULE/UGT/ULT(Z3Py 的 >= 对 BitVec 是有符号的)。
"""
import re

BITWIDTH = 256
TOKEN_RE = re.compile(r"(\d+|[A-Za-z_]\w*|>=|<=|==|!=|[+\-*()<>])")


class _Parser:
    def __init__(self, tokens: list[str], z3):
        self.tokens = tokens
        self.pos = 0
        self.vars: list[str] = []
        self.z3 = z3

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        cond = self.term()
        op = self.peek()
        if cond is None or op not in (">=", "<=", ">", "<", "==", "!="):
            return None
        self.pos += 1
        rhs = self.term()
        if rhs is None or self.pos != len(self.tokens):
            return None
        z3 = self.z3
        return {
            ">=": z3.UGE(cond, rhs), "<=": z3.ULE(cond, rhs),
            ">": z3.UGT(cond, rhs), "<": z3.ULT(cond, rhs),
            "==": cond == rhs, "!=": cond != rhs,
        }[op]

    def term(self):
        v = self.atom()
        if v is None:
            return None
        while self.peek() in ("+", "-", "*"):
            op = self.peek()
            self.pos += 1
            rhs = self.atom()
            if rhs is None:
                return None
            v = v + rhs if op == "+" else v - rhs if op == "-" else v * rhs
        return v

    def atom(self):
        z3 = self.z3
        t = self.peek()
        if t == "(":
            self.pos += 1
            v = self.term()
            if self.peek() != ")":
                return None
            self.pos += 1
            return v
        if t is None:
            return None
        self.pos += 1
        if t.isdigit():
            return z3.BitVecVal(int(t), BITWIDTH)
        if t not in self.vars:
            self.vars.append(t)
        return z3.BitVec(t, BITWIDTH)


def prove_invariant(invariant: str, timeout_ms: int = 3000) -> dict | None:
    """返回 {"sat": bool|None, "counterexample": [...]|None, "proof_ref": str} 或 None(Z3 不可用/DSL 非法)。"""
    try:
        import z3
    except ImportError:
        return None

    tokens = TOKEN_RE.findall(invariant.replace(" ", ""))
    if not tokens:
        return None

    parser = _Parser(tokens, z3)
    cond = parser.parse()
    if cond is None:
        return None

    s = z3.Solver()
    s.set(timeout=timeout_ms)
    s.add(z3.Not(cond))
    result = s.check()
    proof_ref = f"z3:bv{BITWIDTH}:{invariant}"
    if result == z3.unsat:
        return {"sat": False, "counterexample": None, "proof_ref": proof_ref}
    if result != z3.sat:
        return {"sat": None, "counterexample": None, "proof_ref": proof_ref}

    model = s.model()
    state1 = {
        name: str(model.eval(z3.BitVec(name, BITWIDTH), model_completion=True).as_long())
        for name in parser.vars
    }
    return {
        "sat": True,
        "counterexample": [
            {"step": 1, "state": state1},
            {"step": 2, "state": {"invariant": "violated"}},
        ],
        "proof_ref": proof_ref,
    }
