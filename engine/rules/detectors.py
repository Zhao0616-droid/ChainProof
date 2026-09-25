"""7 类漏洞模式库 v0(对齐 SWC Registry)。

demo 范围:纯 Python 源码级模式检测,不依赖编译器;完整规则库与 Slither
归一化见 A4/A8 后续任务。模式检测会误报,证据 kind=pattern。
"""
import re
from dataclasses import dataclass

SWC = {
    "reentrancy": "SWC-107",
    "unchecked-low-level-call": "SWC-104",
    "tx-origin": "SWC-115",
    "timestamp": "SWC-116",
    "unchecked-overflow": "SWC-101",
    "spec-violation": "SPEC",
    "spec-proved": "SPEC",
}

SEVERITY = {
    "reentrancy": "high",
    "unchecked-low-level-call": "medium",
    "tx-origin": "medium",
    "timestamp": "low",
    "unchecked-overflow": "high",
    "spec-violation": "high",
    "spec-proved": "info",
}

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2, "info": 3}

LOW_LEVEL_CALL_RE = re.compile(r"\.(call|send|transfer)\b")
STATE_VAR_RE = re.compile(
    r"^\s*(?:mapping\s*\([^)]*\)|u?int\d*|bool|address|string|bytes\d*)\s+"
    r"(?:public|private|internal|external|constant|immutable|payable|\s)*"
    r"\b([A-Za-z_]\w*)\b"
)
FUNCTION_START_RE = re.compile(r"\bfunction\s+(\w+)\s*\(")
CONSTRUCTOR_RE = re.compile(r"\bconstructor\s*\(")
UNCHECKED_RE = re.compile(r"\bunchecked\s*\{")
ARITH_RE = re.compile(r"([A-Za-z_]\w*|\d+)\s*([+\-*])\s*([A-Za-z_]\w*|\d+)")
BOOL_CAPTURE_RE = re.compile(r"\(\s*bool\s+(\w+)\s*,")


def strip_comments_and_strings(src: str) -> str:
    """把注释与字符串替换为等长空格,保持行号不变。"""
    out = list(src)
    n = len(src)
    i = 0
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n:
            if src[i + 1] == "/":
                j = src.find("\n", i)
                j = n if j == -1 else j
                for k in range(i, j):
                    out[k] = " "
                i = j
                continue
            if src[i + 1] == "*":
                j = src.find("*/", i + 2)
                j = n if j == -1 else j + 2
                for k in range(i, j):
                    if out[k] != "\n":
                        out[k] = " "
                i = j
                continue
        if c in ('"', "'"):
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\":
                    j += 1
                j += 1
            for k in range(i, min(j + 1, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = j + 1
            continue
        i += 1
    return "".join(out)


@dataclass
class Function:
    name: str
    start: int  # 签名行(1-based)
    body_start: int  # 第一个 { 所在行(1-based)
    end: int  # 匹配 } 所在行(1-based)

    def body_lines(self, lines: list[str]) -> list[tuple[int, str]]:
        return [(no, lines[no - 1]) for no in range(self.body_start, self.end + 1)]


@dataclass
class Finding:
    type: str
    line: int
    function: str
    detail: str = ""
    counterexample: list | None = None
    proof_ref: str | None = None
    formal: bool = False

    def to_schema(self, idx: int, filename: str) -> dict:
        if self.formal:
            evidence: dict = {"kind": "formal", "smt_status": "unsat"}
        else:
            evidence = {
                "kind": "counterexample" if self.counterexample else "pattern",
                "smt_status": "sat" if self.counterexample else "unknown",
            }
        if self.counterexample is not None:
            evidence["counterexample"] = self.counterexample
        if self.proof_ref:
            evidence["proof_ref"] = self.proof_ref
        return {
            "id": f"F{idx}",
            "swc": SWC[self.type],
            "type": self.type,
            "severity": SEVERITY[self.type],
            "location": {"file": filename, "line": self.line, "function": self.function},
            "evidence": evidence,
        }


@dataclass
class OverflowCandidate:
    expr: str
    line: int
    function: str


def extract_state_vars(cleaned: str) -> set[str]:
    """合约顶层(括号深度 1,即合约体内、函数外)声明的状态变量名。"""
    depth = 0
    names: set[str] = set()
    for raw in cleaned.splitlines():
        depth += raw.count("{") - raw.count("}")
        if depth == 1 and "{" not in raw:
            m = STATE_VAR_RE.match(raw)
            if m:
                names.add(m.group(1))
    return names


def extract_functions(cleaned: str) -> list[Function]:
    lines = cleaned.splitlines()
    functions: list[Function] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = FUNCTION_START_RE.search(line)
        if m:
            name = m.group(1)
        elif CONSTRUCTOR_RE.search(line):
            name = "constructor"
        else:
            i += 1
            continue
        brace_i = i
        while brace_i < len(lines) and "{" not in lines[brace_i]:
            brace_i += 1
        if brace_i >= len(lines):
            break
        depth = 1
        j = brace_i + 1
        while j < len(lines) and depth > 0:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
        functions.append(Function(name=name, start=i + 1, body_start=brace_i + 1, end=j))
        i = j
    return functions


def detect_patterns(fn: Function, state_vars: set[str], lines: list[str]) -> tuple[list[Finding], list[OverflowCandidate]]:
    """对单个函数做模式检测。返回 (findings, overflow_candidates)。"""
    findings: list[Finding] = []
    overflow: list[OverflowCandidate] = []
    body = fn.body_lines(lines)

    for no, text in body:
        if "tx.origin" in text:
            findings.append(Finding("tx-origin", no, fn.name, "权限判断使用了 tx.origin,可被钓鱼合约绕过。"))

    for no, text in body:
        if ("block.timestamp" in text or "block.number" in text) and re.search(r"\b(if|require|assert|return|while)\b", text):
            findings.append(Finding("timestamp", no, fn.name, "判断依赖区块时间戳/区块号,可被操纵。"))

    # 重入:低层级外部调用之后仍写状态变量(违反 CEI)
    if state_vars:
        state_write_re = re.compile(r"\b(" + "|".join(re.escape(v) for v in state_vars) + r")\b\s*(\+=|-=|=|\+\+|--)")
    else:
        state_write_re = None
    for no, text in body:
        if LOW_LEVEL_CALL_RE.search(text):
            written_after = []
            if state_write_re:
                for no2, text2 in body:
                    if no2 > no and state_write_re.search(text2):
                        written_after.append(state_write_re.search(text2).group(1))
            if written_after:
                findings.append(
                    Finding(
                        "reentrancy",
                        no,
                        fn.name,
                        f"外部调用之后仍写入状态变量 {sorted(set(written_after))},攻击者可在回调中重入。",
                    )
                )

    # 未检查的低层级调用返回值
    for no, text in body:
        if not re.search(r"\.(call|send)\s*(\{|\(|$)", text):
            continue
        m = BOOL_CAPTURE_RE.search(text)
        checked = False
        ok_var = m.group(1) if m else None
        if ok_var:
            for no2, text2 in body:
                if no2 > no and re.search(r"\b(require|assert|if)\b.*\b" + ok_var + r"\b", text2):
                    checked = True
                    break
        if not checked:
            detail = (
                f"低层级调用返回值变量 {ok_var} 未被检查,调用失败时交易不会回滚。"
                if ok_var
                else "低层级调用的返回值被完全忽略,调用失败时交易不会回滚。"
            )
            findings.append(Finding("unchecked-low-level-call", no, fn.name, detail))

    # unchecked 溢出候选(交给 Z3 求反例)
    for no, _ in body:
        if not UNCHECKED_RE.search(lines[no - 1]):
            continue
        depth = 1
        end_line = no
        for j in range(no + 1, fn.end + 1):
            depth += lines[j - 1].count("{") - lines[j - 1].count("}")
            if depth == 0:
                end_line = j
                break
        for j in range(no, end_line + 1):
            for am in ARITH_RE.finditer(lines[j - 1]):
                if am.group(2) in "+-*":
                    overflow.append(OverflowCandidate(am.group(0).replace(" ", ""), j, fn.name))

    return findings, overflow
