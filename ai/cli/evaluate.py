"""评测 CLI(B12 v0):数据集上批量跑引擎,输出精度/召回/F1 与证明率。

demo 说明:引擎以子进程调用(CLI 契约);z3 需在引擎 venv(优先)或当前环境。
结果写 datasets/eval_metrics.json(gitignored)。
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"
DEFAULT_LABELS = DATASETS / "labels.json"

DETECTED_SWC = {"SWC-101", "SWC-104", "SWC-107", "SWC-115", "SWC-116"}
PARTIAL_NOTE = {
    "SWC-101": "数据集为 0.4.x 代码,无 unchecked 块,检测器 v0 覆盖面受限",
    "SWC-115": "access_control 类别仅部分合约使用 tx.origin",
}


def _engine_python() -> str:
    cand = REPO_ROOT / "engine" / ".venv" / "Scripts" / "python.exe"
    if cand.is_file():
        return str(cand)
    return sys.executable


def analyze_one(args: tuple[str, Path]) -> tuple[str, set[str], dict]:
    rel, sol = args
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        try:
            proc = subprocess.run(
                [_engine_python(), "-m", "engine.cli.analyze", str(sol), "-o", str(out)],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
                encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired:
            return rel, set(), {"error": "timeout"}
        if proc.returncode != 0 or not out.is_file():
            return rel, set(), {"error": (proc.stderr or "no output").strip()[:120]}
        result = json.loads(out.read_text(encoding="utf-8"))
        swcs = {f["swc"] for f in result["findings"]}
        cov = result["analysis"]["coverage"]
        return rel, swcs, {"coverage": cov, "findings": len(result["findings"])}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="evaluate", description="数据集评测(B12 v0)")
    parser.add_argument("--labels", default=str(DEFAULT_LABELS), help="labels.json 路径")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 个(冒烟测试)")
    args = parser.parse_args(argv)

    labels_path = Path(args.labels)
    if not labels_path.is_file():
        print(f"错误: 找不到标注文件 {labels_path},先运行 datasets/fetch_smartbugs.py", file=sys.stderr)
        return 1
    labels: dict[str, list[str]] = json.loads(labels_path.read_text(encoding="utf-8"))
    items = [(rel, DATASETS / rel) for rel in labels]
    if args.limit:
        items = items[: args.limit]

    print(f"评测 {len(items)} 个合约(workers={args.workers})...")
    t0 = time.perf_counter()
    coverage_sum = [0, 0]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        raw_results = list(pool.map(analyze_one, items))
    results = {rel: (swcs, meta) for rel, swcs, meta in raw_results}

    detected: dict[str, set[str]] = {}
    for rel, (swcs, meta) in results.items():
        detected[rel] = swcs & DETECTED_SWC
        cov = meta.get("coverage")
        if cov:
            coverage_sum[0] += cov["proved"]
            coverage_sum[1] += cov["total"]

    rows = []
    for swc in sorted(DETECTED_SWC):
        tp = fp = fn = 0
        for rel, expected in labels.items():
            if rel not in detected:
                continue
            has_label = swc in expected
            has_detect = swc in detected[rel]
            if has_label and has_detect:
                tp += 1
            elif has_detect:
                fp += 1
            elif has_label:
                fn += 1
        if tp + fp + fn == 0:
            continue
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append({
            "swc": swc,
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "note": PARTIAL_NOTE.get(swc, ""),
        })

    total_tp = sum(r["tp"] for r in rows)
    total_fp = sum(r["fp"] for r in rows)
    total_fn = sum(r["fn"] for r in rows)
    micro_p = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    micro_r = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if micro_p + micro_r else 0.0

    print(f"\n{'SWC':<10}{'TP':>4}{'FP':>5}{'FN':>5}{'精确率':>8}{'召回率':>8}{'F1':>7}  说明")
    for r in rows:
        note = f"  ({r['note']})" if r["note"] else ""
        print(f"{r['swc']:<10}{r['tp']:>4}{r['fp']:>5}{r['fn']:>5}"
              f"{r['precision']:>8}{r['recall']:>8}{r['f1']:>7}{note}")
    print(f"\n总体(micro):P={micro_p:.3f} R={micro_r:.3f} F1={micro_f1:.3f}")
    if coverage_sum[1]:
        print(f"证明率:proved/total = {coverage_sum[0]}/{coverage_sum[1]} ({coverage_sum[0] / coverage_sum[1]:.1%})")
    print(f"耗时 {time.perf_counter() - t0:.1f}s")

    metrics = {
        "dataset": labels_path.name,
        "contracts": len(items),
        "per_swc": rows,
        "micro": {"precision": round(micro_p, 3), "recall": round(micro_r, 3), "f1": round(micro_f1, 3)},
        "coverage": {"proved": coverage_sum[0], "total": coverage_sum[1]},
    }
    out = DATASETS / "eval_metrics.json"
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"指标已写 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
