"""ChainProof API(Day 1 骨架):/healthz + mock 分析接口。

真实任务队列与引擎接入排期 W2(A13);当前 mock 供 C 假集成渲染 M1-M6。
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "analysis_result.json"

app = FastAPI(title="ChainProof API", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "chainproof-api"}


@app.get("/api/v1/mock/analysis_result")
def mock_analysis_result():
    return json.loads(EXAMPLES.read_text(encoding="utf-8"))


@app.post("/api/v1/analyze")
def analyze():
    raise HTTPException(status_code=501, detail="引擎接入排期 W2(A13)")
