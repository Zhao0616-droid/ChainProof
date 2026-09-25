"""分析相关接口:上传校验(S6)、分析编排、结果存取与删除、示例合约。"""
import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.pipeline import PipelineError, run_analysis
from storage import store

router = APIRouter(prefix="/api/v1")

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "examples" / "contracts" / "VulnerableToken.sol"

MAX_SOURCE_CHARS = 100_000
PRAGMA_RE = re.compile(r"pragma\s+solidity")
ANALYSIS_ID_RE = re.compile(r"^[a-f0-9]{12}$")


class AnalyzeRequest(BaseModel):
    filename: str
    source: str


def _validate_source(filename: str, source: str) -> None:
    if not filename.lower().endswith(".sol"):
        raise HTTPException(status_code=400, detail="仅支持 .sol 文件")
    if len(source) > MAX_SOURCE_CHARS:
        raise HTTPException(status_code=413, detail=f"文件过大(>{MAX_SOURCE_CHARS} 字符)")
    if "\x00" in source:
        raise HTTPException(status_code=400, detail="二进制文件不允许上传")
    if "contract " not in source and not PRAGMA_RE.search(source):
        raise HTTPException(status_code=400, detail="文件内容不像 Solidity 合约(缺少 contract 声明或 pragma)")


def _require_id(analysis_id: str) -> None:
    if not ANALYSIS_ID_RE.match(analysis_id):
        raise HTTPException(status_code=404, detail="分析记录不存在")


def _detail(payload: dict) -> dict:
    return {**store.meta(payload), "source": payload["source"], "result": payload["result"]}


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    _validate_source(req.filename, req.source)
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


@router.get("/sample")
def sample_contract():
    return {"filename": SAMPLE_PATH.name, "source": SAMPLE_PATH.read_text(encoding="utf-8")}
