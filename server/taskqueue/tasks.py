"""demo 内存任务队列:后台线程逐文件分析,单进程有效、重启即失(A13/W2 换真队列)。"""
import hashlib
import threading
import time
import uuid
from pathlib import Path

from fastapi import HTTPException

from services.pipeline import run_analysis
from services.validation import validate_source
from storage import store

_tasks: dict[str, dict] = {}
_lock = threading.Lock()

MAX_FILES = 50


def create(files: list[dict]) -> str:
    task_id = uuid.uuid4().hex[:12]
    task = {
        "id": task_id,
        "status": "queued",
        "total": len(files),
        "done": 0,
        "created_at": time.time(),
        "files": [
            {"filename": f["filename"], "status": "queued"}
            for f in files
        ],
    }
    with _lock:
        _tasks[task_id] = task
    threading.Thread(target=_run, args=(task_id, files), daemon=True).start()
    return task_id


def get(task_id: str) -> dict | None:
    with _lock:
        return _tasks.get(task_id)


def _run(task_id: str, files: list[dict]) -> None:
    task = _tasks[task_id]
    with _lock:
        task["status"] = "running"
        task["started_at"] = time.time()
    for idx, f in enumerate(files):
        item = task["files"][idx]
        try:
            validate_source(f["filename"], f["source"])
            result = run_analysis(f["source"], f["filename"])
            analysis_id = hashlib.sha256(f["source"].encode("utf-8")).hexdigest()[:12]
            store.save(analysis_id, Path(f["filename"]).stem, f["source"], result)
            item.update(status="done", id=analysis_id, name=Path(f["filename"]).stem)
        except HTTPException as e:
            item.update(status="failed", error=e.detail)
        except Exception as e:
            item.update(status="failed", error=f"分析失败: {e}")
        with _lock:
            task["done"] += 1
    with _lock:
        task["status"] = "done"
        task["finished_at"] = time.time()
