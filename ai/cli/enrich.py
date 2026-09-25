"""ChainProof AI 层 CLI:enrich <result.json> [-o out.json] [--source x.sol] [--specs specs.json]

把 B 负责字段(explanation/patch/model_version)填进引擎产出的结果。
model_version 优先取规约文件(LLM 生成时),否则用默认值。
"""
import argparse
import json
import sys
from pathlib import Path

from ai.explain.templates import explain
from ai.patch.templates import build_patch

DEFAULT_MODEL_VERSION = "specgen-v0-demo"


def enrich(result: dict, source_lines: list[str] | None, model_version: str | None = None) -> dict:
    lines = source_lines or []
    for f in result.get("findings", []):
        f["explanation"] = explain(f, lines)
        f["patch"] = build_patch(f, lines)
    result["analysis"]["model_version"] = model_version or DEFAULT_MODEL_VERSION
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="enrich", description="ChainProof 结果补全 CLI(B)")
    parser.add_argument("result", help="引擎产出的 result.json 路径")
    parser.add_argument("-o", "--output", help="输出路径(默认覆盖原文件)")
    parser.add_argument("--source", help="合约源码路径(用于解释与补丁的代码引用)")
    parser.add_argument("--specs", help="规约文件路径(取其 model_version)")
    args = parser.parse_args(argv)

    result_path = Path(args.result)
    if not result_path.is_file():
        print(f"错误: 找不到结果文件 {result_path}", file=sys.stderr)
        return 1
    result = json.loads(result_path.read_text(encoding="utf-8"))

    source_lines = None
    if args.source:
        source_path = Path(args.source)
        if not source_path.is_file():
            print(f"警告: 找不到源码 {source_path},仅生成通用解释", file=sys.stderr)
        else:
            source_lines = source_path.read_text(encoding="utf-8").splitlines()

    model_version = None
    if args.specs:
        specs_path = Path(args.specs)
        if specs_path.is_file():
            specs = json.loads(specs_path.read_text(encoding="utf-8"))
            model_version = specs.get("model_version")

    result = enrich(result, source_lines, model_version)
    out = Path(args.output) if args.output else result_path
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out} (model_version={result['analysis']['model_version']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
