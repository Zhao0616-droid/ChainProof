"""分析编排(C 接 A+B,对应 A13/B14):CLI 契约驱动,不 import 引擎/AI 代码。

流程:specgen(B,LLM 规约生成,可降级)→ engine analyze(A,检测+规约证明)
→ enrich(B,解释/补丁/模型版本)。demo 说明:引擎在 server 进程内同步调用,
任务队列化排期 W2(批量入口已用内存队列)。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TIMEOUT_SECONDS = 60
SPECGEN_TIMEOUT_SECONDS = 150  # LLM 网关含 thinking 实测约 100s,需放宽


class PipelineError(Exception):
    pass


def run_analysis(source: str, filename: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src_path = tmp_path / filename
        src_path.write_text(source, encoding="utf-8")
        raw_path = tmp_path / "raw.json"
        specs_path = tmp_path / "specs.json"
        out_path = tmp_path / "result.json"

        specs = _run_specgen(src_path, specs_path)
        _run(
            [sys.executable, "-m", "engine.cli.analyze", str(src_path), "-o", str(raw_path)]
            + (["--specs", str(specs_path)] if specs.get("specs") else [])
        )
        raw = json.loads(raw_path.read_text(encoding="utf-8"))

        try:
            cmd = [sys.executable, "-m", "ai.cli.enrich", str(raw_path), "-o", str(out_path), "--source", str(src_path)]
            if specs_path.is_file():
                cmd += ["--specs", str(specs_path)]
            _run(cmd)
            return json.loads(out_path.read_text(encoding="utf-8"))
        except PipelineError:
            # 降级:AI 不可用时仍返回引擎结果(R8)
            return raw


def _run_specgen(src_path: Path, specs_path: Path) -> dict:
    try:
        _run(
            [sys.executable, "-m", "ai.cli.specgen", str(src_path), "-o", str(specs_path)],
            timeout=SPECGEN_TIMEOUT_SECONDS,
        )
    except PipelineError:
        return {"specs": []}
    if specs_path.is_file():
        return json.loads(specs_path.read_text(encoding="utf-8"))
    return {"specs": []}


def _run(cmd: list[str], timeout: int = TIMEOUT_SECONDS) -> None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired as e:
        raise PipelineError(f"分析超时(>{timeout}s): {' '.join(cmd[:3])}") from e
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise PipelineError("; ".join(detail[-3:]) or f"退出码 {proc.returncode}")
