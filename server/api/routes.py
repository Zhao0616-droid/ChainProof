"""分析相关接口:上传校验(S6)、分析编排、结果存取、示例合约。"""
import hashlib
import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.pipeline import PipelineError, run_analysis
from storage import store

router = APIRouter(prefix="/api/v1")

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "examples" / "contracts" / "VulnerableToken.sol"
MOCK_PATH = REPO_ROOT / "examples" / "analysis_result.json"

MAX_SOURCE_CHARS = 100_000
PRAGMA_RE = re.compile(r"pragma\s+solidity")


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


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    _validate_source(req.filename, req.source)
    try:
        result = run_analysis(req.source, req.filename)
    except PipelineError as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {e}") from e
    analysis_id = hashlib.sha256(req.source.encode("utf-8")).hexdigest()[:12]
    store.save(analysis_id, Path(req.filename).stem, req.source, result)
    return {"id": analysis_id, "result": result}


@router.get("/analyses")
def list_analyses():
    return {"items": store.list_all()}


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    payload = store.load(analysis_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return {**store.meta(payload), "source": payload["source"], "result": payload["result"]}


@router.get("/sample")
def sample_contract():
    return {"filename": SAMPLE_PATH.name, "source": SAMPLE_PATH.read_text(encoding="utf-8")}


@router.get("/mock/analysis_result")
def mock_analysis_result():
    return json.loads(MOCK_PATH.read_text(encoding="utf-8"))
