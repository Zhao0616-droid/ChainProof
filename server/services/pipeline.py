"""分析编排(C 接 A+B,对应 A13/B14):CLI 契约驱动,不 import 引擎/AI 代码。

demo 说明:引擎在 server 进程内同步调用,任务队列化排期 W2。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TIMEOUT_SECONDS = 60


class PipelineError(Exception):
    pass


def run_analysis(source: str, filename: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src_path = tmp_path / filename
        src_path.write_text(source, encoding="utf-8")
        raw_path = tmp_path / "raw.json"
        out_path = tmp_path / "result.json"

        _run([sys.executable, "-m", "engine.cli.analyze", str(src_path), "-o", str(raw_path)])
        raw = json.loads(raw_path.read_text(encoding="utf-8"))

        try:
            _run([sys.executable, "-m", "ai.cli.enrich", str(raw_path), "-o", str(out_path), "--source", str(src_path)])
            return json.loads(out_path.read_text(encoding="utf-8"))
        except PipelineError:
            # 降级:AI 不可用时仍返回引擎结果(R8)
            return raw


def _run(cmd: list[str]) -> None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired as e:
        raise PipelineError(f"分析超时(>{TIMEOUT_SECONDS}s): {' '.join(cmd[:3])}") from e
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise PipelineError("; ".join(detail[-3:]) or f"退出码 {proc.returncode}")
