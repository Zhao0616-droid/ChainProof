"""ChainProof 引擎 CLI:analyze <contract.sol> [-o result.json] [--specs specs.json] [--mock]

demo v0 流程:源码模式检测(规则库)→ Z3 溢出反例 → 规约不变量证明(可选)
→ 产出符合 schemas/analysis_result.json 的结果。完整符号执行见 A3/A12。
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from engine.rules.detectors import (
    SEVERITY,
    SEVERITY_RANK,
    Finding,
    extract_functions,
    extract_state_vars,
    strip_comments_and_strings,
    detect_patterns,
)
from engine.solver.overflow import analyze_overflow
from engine.prove.specs import prove_invariant

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "analysis_result.json"

DEMO_UNVERIFIED = [
    {
        "reason": "demo v0:符号执行与完整规则库未接入;规约证明为 havoc 模型(输入无约束),"
        "LLM 规约离线时降级为无规约;pattern 证据未证明,需人工复核",
        "scope": "all",
    }
]


def analyze_source(source: str, filename: str, specs: dict | None = None) -> dict:
    t0 = time.perf_counter()
    cleaned = strip_comments_and_strings(source)
    lines = cleaned.splitlines()
    state_vars = extract_state_vars(cleaned)
    functions = extract_functions(cleaned)

    findings: list[Finding] = []
    overflow_candidates = []
    for fn in functions:
        fnd, cands = detect_patterns(fn, state_vars, lines)
        findings.extend(fnd)
        overflow_candidates.extend(cands)

    overflow_checks = 0
    overflow_proved = 0
    for cand in overflow_candidates:
        res = analyze_overflow(cand.expr)
        if res is None:
            findings.append(
                Finding(
                    "unchecked-overflow",
                    cand.line,
                    cand.function,
                    f"unchecked 块内的算术表达式 {cand.expr} 可能回绕(Z3 未安装,无法生成反例)。",
                )
            )
            continue
        overflow_checks += 1
        if res["sat"]:
            findings.append(
                Finding(
                    "unchecked-overflow",
                    cand.line,
                    cand.function,
                    f"Z3 证明 {cand.expr} 存在回绕输入:见反例轨迹。",
                    counterexample=res["counterexample"],
                    proof_ref=res["proof_ref"],
                )
            )
        else:
            overflow_proved += 1

    spec_checks = 0
    spec_proved = 0
    if specs:
        for spec in specs.get("specs", []):
            inv = spec.get("invariant")
            if not inv:
                continue
            res = prove_invariant(inv)
            if res is None:
                continue
            spec_checks += 1
            fn_name = spec.get("function", "")
            fn_line = next((f.start for f in functions if f.name == fn_name), 1)
            if res["sat"] is False:
                spec_proved += 1
                findings.append(
                    Finding(
                        "spec-proved",
                        fn_line,
                        fn_name,
                        f"不变量经 Z3 证明成立(havoc 模型): {inv}",
                        proof_ref=res["proof_ref"],
                        formal=True,
                    )
                )
            elif res["sat"] is True:
                findings.append(
                    Finding(
                        "spec-violation",
                        fn_line,
                        fn_name,
                        f"不变量存在反例(Z3 SAT): {inv},该性质可能对应安全缺陷。",
                        counterexample=res["counterexample"],
                        proof_ref=res["proof_ref"],
                    )
                )

    findings.sort(key=lambda f: (SEVERITY_RANK[SEVERITY[f.type]], f.line))
    schema_findings = [f.to_schema(i + 1, filename) for i, f in enumerate(findings)]

    content = source.encode("utf-8")
    result = {
        "contract": {
            "name": Path(filename).stem,
            "hash": "sha256:" + hashlib.sha256(content).hexdigest(),
            "compiler": "source-pattern-v0 (solc 未接入)",
        },
        "analysis": {
            "status": "done",
            "coverage": {
                "proved": overflow_proved + spec_proved,
                "total": overflow_checks + spec_checks + _rule_checks(functions),
            },
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        },
        "findings": schema_findings,
        "unverified": DEMO_UNVERIFIED,
    }
    return result


def _rule_checks(functions) -> int:
    # 每个函数执行 4 类模式检测(tx.origin/时间戳/重入/未检查返回值)
    return len(functions) * 4


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="analyze", description="ChainProof 引擎 CLI")
    parser.add_argument("contract", nargs="?", help="Solidity 合约文件路径(--mock 时省略)")
    parser.add_argument("-o", "--output", default="result.json", help="结果输出路径")
    parser.add_argument("--specs", help="规约文件路径(ai.cli.specgen 产出)")
    parser.add_argument("--mock", action="store_true", help="直接输出 examples/analysis_result.json 样例")
    args = parser.parse_args(argv)

    if args.mock:
        result = json.loads(EXAMPLES.read_text(encoding="utf-8"))
    else:
        if not args.contract:
            parser.error("需要合约文件路径,或使用 --mock")
        contract_path = Path(args.contract)
        if not contract_path.is_file():
            print(f"错误: 找不到合约文件 {contract_path}", file=sys.stderr)
            return 1
        source = contract_path.read_text(encoding="utf-8")
        specs = None
        if args.specs:
            specs_path = Path(args.specs)
            if not specs_path.is_file():
                print(f"警告: 找不到规约文件 {specs_path},跳过规约证明", file=sys.stderr)
            else:
                specs = json.loads(specs_path.read_text(encoding="utf-8"))
        result = analyze_source(source, contract_path.name, specs=specs)

    out = Path(args.output)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out} ({len(result['findings'])} 条发现)")
    print(f"契约校验: uv run schemas/validate.py {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
