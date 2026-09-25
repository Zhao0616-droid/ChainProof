"""Z3 溢出反例生成(A5 v0)。

对 unchecked 块内的算术表达式,构造"运算不回绕"性质交给 Z3 判定:
SAT → 存在使结果回绕的输入,模型即反例;UNSAT → 该表达式不会回绕。
"""
BITWIDTH = 256


def analyze_overflow(expr: str, timeout_ms: int = 3000) -> dict | None:
    """返回 {"sat": bool, "counterexample": [...] | None, "proof_ref": str} 或 None(Z3 不可用)。"""
    try:
        import z3
    except ImportError:
        return None

    parsed = _parse(expr)
    if parsed is None:
        return None
    lhs, op, rhs = parsed

    a = z3.BitVec(lhs, BITWIDTH) if lhs.isidentifier() else z3.BitVecVal(int(lhs), BITWIDTH)
    b = z3.BitVec(rhs, BITWIDTH) if rhs.isidentifier() else z3.BitVecVal(int(rhs), BITWIDTH)

    s = z3.Solver()
    s.set(timeout=timeout_ms)
    if op == "+":
        s.add(z3.ULT(a + b, a))  # 无符号回绕:a+b < a 当且仅当发生上溢
    elif op == "-":
        s.add(z3.UGT(a - b, a))  # 无符号回绕:a-b > a 当且仅当发生下溢
    elif op == "*":
        s.add(b != 0, z3.UDiv(a * b, b) != a)
    else:
        return None

    result = s.check()
    proof_ref = f"z3:bv{BITWIDTH}:{expr}"
    if result != z3.sat:
        return {"sat": False, "counterexample": None, "proof_ref": proof_ref}

    model = s.model()
    ma = model.eval(a, model_completion=True).as_long()
    mb = model.eval(b, model_completion=True).as_long()
    mod = 1 << BITWIDTH
    if op == "+":
        wrapped = (ma + mb) % mod
    elif op == "-":
        wrapped = (ma - mb) % mod
    else:
        wrapped = (ma * mb) % mod

    state1 = {lhs: str(ma)}
    if rhs.isidentifier():
        state1[rhs] = str(mb)
    return {
        "sat": True,
        "counterexample": [
            {"step": 1, "state": state1},
            {"step": 2, "state": {expr: str(wrapped)}},
        ],
        "proof_ref": proof_ref,
    }


def _parse(expr: str) -> tuple[str, str, str] | None:
    for op in "+-*":
        idx = expr.find(op)
        if idx > 0:
            return expr[:idx].strip(), op, expr[idx + 1 :].strip()
    return None
