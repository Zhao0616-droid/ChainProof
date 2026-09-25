"""ChainProof AI 层 CLI(Day 1 骨架):specgen <contract.sol> [-o specs.json]

规约生成 v0 于 D4(B4)接入;产出示例见 examples/specs.json。
"""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_SOLC = "0.8.20"


def build_stub_specs(contract_path: Path) -> dict:
    return {
        "contract": {
            "name": contract_path.stem,
            "file": str(contract_path),
            "solc": DEFAULT_SOLC,
        },
        "source": {"path_summary": None, "model": "specgen-v0-stub"},
        "specs": [],
        "note": "Day 1 骨架占位:规约生成 v0 于 D4 接入",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="specgen", description="ChainProof 规约生成 CLI")
    parser.add_argument("contract", help="Solidity 合约文件路径")
    parser.add_argument("-o", "--output", default="specs.json", help="规约输出路径")
    args = parser.parse_args(argv)

    contract_path = Path(args.contract)
    if not contract_path.is_file():
        print(f"错误: 找不到合约文件 {contract_path}", file=sys.stderr)
        return 1

    specs = build_stub_specs(contract_path)
    out = Path(args.output)
    out.write_text(json.dumps(specs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
