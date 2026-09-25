# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.23"]
# ///
"""ChainProof 契约校验器(三方共用,对应 M8 契约测试)。

用法:
    uv run schemas/validate.py <data.json> [<data2.json> ...]

对每个文件依次尝试两个契约 schema,报告匹配结果;任一文件不匹配则以非零码退出。
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent
SCHEMAS = {
    "analysis_result": SCHEMA_DIR / "analysis_result.json",
    "path_summary": SCHEMA_DIR / "path_summary.json",
}


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    files = [Path(a) for a in sys.argv[1:]]
    if not files:
        print("用法: uv run schemas/validate.py <data.json> ...")
        return 2

    failed = False
    for path in files:
        data = load_json(path)
        matched = None
        errors = {}
        for name, schema_path in SCHEMAS.items():
            schema = load_json(schema_path)
            errs = list(Draft202012Validator(schema).iter_errors(data))
            errors[name] = errs
            if not errs:
                matched = name
        if matched:
            print(f"PASS  {path.name}  符合 schema: {matched}")
        else:
            failed = True
            print(f"FAIL  {path.name}  不符合任一 schema")
            for name, errs in errors.items():
                for e in errs[:5]:
                    print(f"      [{name}] {e.json_path}: {e.message}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
