"""ChainProof 引擎 CLI(Day 1 骨架):analyze <contract.sol> [-o result.json] [--mock]

真实实现按分工手册 A1-A16 逐步替换本 stub;产出必须符合 schemas/analysis_result.json。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "analysis_result.json"
DEFAULT_SOLC = "0.8.20"


def build_stub_result(contract_path: Path) -> dict:
    content = contract_path.read_bytes()
    return {
        "contract": {
            "name": contract_path.stem,
            "hash": "sha256:" + hashlib.sha256(content).hexdigest(),
            "compiler": DEFAULT_SOLC,
        },
        "analysis": {
            "status": "partial",
            "coverage": {"proved": 0, "total": 0},
            "duration_ms": 0,
        },
        "findings": [],
        "unverified": [{"reason": "engine stub (Day 1 骨架)", "scope": "all"}],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="analyze", description="ChainProof 引擎 CLI")
    parser.add_argument("contract", nargs="?", help="Solidity 合约文件路径(--mock 时省略)")
    parser.add_argument("-o", "--output", default="result.json", help="结果输出路径")
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
        result = build_stub_result(contract_path)

    out = Path(args.output)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out}")
    print(f"契约校验: uv run schemas/validate.py {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
