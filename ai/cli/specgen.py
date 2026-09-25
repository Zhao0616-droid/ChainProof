"""ChainProof AI 层 CLI:specgen <contract.sol> [-o specs.json] [--offline]

规约生成 v0(D4/B4):LLM 生成函数级不变量(受限 DSL,供引擎 Z3 证明)。
无密钥或调用失败时降级为空规约(不阻塞分析链路)。
"""
import argparse
import json
import sys
from pathlib import Path

from ai.specgen.llm import generate_specs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="specgen", description="ChainProof 规约生成 CLI")
    parser.add_argument("contract", help="Solidity 合约文件路径")
    parser.add_argument("-o", "--output", default="specs.json", help="规约输出路径")
    parser.add_argument("--offline", action="store_true", help="跳过 LLM,输出空规约(降级测试)")
    args = parser.parse_args(argv)

    contract_path = Path(args.contract)
    if not contract_path.is_file():
        print(f"错误: 找不到合约文件 {contract_path}", file=sys.stderr)
        return 1

    source = contract_path.read_text(encoding="utf-8")
    specs = generate_specs(source, contract_path.name, force_offline=args.offline)
    out = Path(args.output)
    out.write_text(json.dumps(specs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out} ({len(specs['specs'])} 条规约, model={specs['model_version']})")
    if specs.get("note"):
        print(f"注: {specs['note']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
