"""结果存储(C2 v0):JSON 文件落盘 data/results/,demo 阶段无数据库。"""
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "results"

SEVERITIES = ["high", "medium", "low", "info"]


def save(analysis_id: str, name: str, source: str, result: dict) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": analysis_id,
        "name": name,
        "created_at": time.time(),
        "source": source,
        "result": result,
    }
    (DATA_DIR / f"{analysis_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def load(analysis_id: str) -> dict | None:
    path = DATA_DIR / f"{analysis_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete(analysis_id: str) -> bool:
    path = DATA_DIR / f"{analysis_id}.json"
    if not path.is_file():
        return False
    path.unlink()
    return True


def list_all() -> list[dict]:
    if not DATA_DIR.is_dir():
        return []
    items = []
    for path in DATA_DIR.glob("*.json"):
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    items.sort(key=lambda p: p.get("created_at", 0), reverse=True)
    return [meta(p) for p in items[:50]]


def meta(payload: dict) -> dict:
    findings = payload["result"].get("findings", [])
    counts = {sev: sum(1 for f in findings if f["severity"] == sev) for sev in SEVERITIES}
    return {
        "id": payload["id"],
        "name": payload["name"],
        "created_at": payload["created_at"],
        "status": payload["result"]["analysis"]["status"],
        "duration_ms": payload["result"]["analysis"]["duration_ms"],
        "findings_total": len(findings),
        "counts": counts,
    }
