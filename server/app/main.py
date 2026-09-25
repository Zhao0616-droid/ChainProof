"""ChainProof API(demo v0):健康检查 + 分析接口。"""
from fastapi import FastAPI

from api.routes import router

app = FastAPI(title="ChainProof API", version="0.1.0")
app.include_router(router)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "chainproof-api"}
