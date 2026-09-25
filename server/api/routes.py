"""分析相关接口:上传校验(S6)、分析编排、结果存取与删除、批量任务、报告导出、示例合约。"""
import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from services.pipeline import PipelineError, run_analysis
from services.report import build_report
from services.validation import validate_source
from storage import store
from taskqueue import tasks

router = APIRouter(prefix="/api/v1")

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "examples" / "contracts" / "VulnerableToken.sol"

ANALYSIS_ID_RE = re.compile(r"^[a-f0-9]{12}$")


class AnalyzeRequest(BaseModel):
    filename: str
    source: str


class BatchFile(BaseModel):
    filename: str
    source: str


class BatchRequest(BaseModel):
    files: list[BatchFile]


def _require_id(analysis_id: str) -> None:
    if not ANALYSIS_ID_RE.match(analysis_id):
        raise HTTPException(status_code=404, detail="分析记录不存在")


def _detail(payload: dict) -> dict:
    return {**store.meta(payload), "source": payload["source"], "result": payload["result"]}


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    validate_source(req.filename, req.source)
    try:
        result = run_analysis(req.source, req.filename)
    except PipelineError as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {e}") from e
    analysis_id = hashlib.sha256(req.source.encode("utf-8")).hexdigest()[:12]
    payload = store.save(analysis_id, Path(req.filename).stem, req.source, result)
    return _detail(payload)


@router.get("/analyses")
def list_analyses():
    return {"items": store.list_all()}


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    _require_id(analysis_id)
    payload = store.load(analysis_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return _detail(payload)


@router.delete("/analyses/{analysis_id}")
def delete_analysis(analysis_id: str):
    _require_id(analysis_id)
    if not store.delete(analysis_id):
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return {"deleted": analysis_id}


@router.get("/analyses/{analysis_id}/report")
def download_report(analysis_id: str):
    _require_id(analysis_id)
    payload = store.load(analysis_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    md = build_report(payload)
    filename = f"{payload['name']}-审计报告.md"
    from urllib.parse import quote

    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.post("/batch")
def batch_analyze(req: BatchRequest):
    if not req.files:
        raise HTTPException(status_code=400, detail="文件列表为空")
    if len(req.files) > tasks.MAX_FILES:
        raise HTTPException(status_code=400, detail=f"单批最多 {tasks.MAX_FILES} 个文件")
    task_id = tasks.create([f.model_dump() for f in req.files])
    return {"task_id": task_id}


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/sample")
def sample_contract():
    return {"filename": SAMPLE_PATH.name, "source": SAMPLE_PATH.read_text(encoding="utf-8")}
