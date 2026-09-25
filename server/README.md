# server/ — 产品层后端(人 C)

> 一句话:把证据变成产品。前端换真引擎时一行不改(验收标准 C-②)。

## 目录

| 目录 | 内容 | 对应任务 |
|---|---|---|
| app/ | FastAPI 入口与路由 | C2 |
| api/ | 业务接口(分析/项目/规约库/知识库) | C2/C5/C6/C7 |
| queue/ | 任务队列(排队/进度/重试) | C2 |
| storage/ | 持久化(结果/项目/用户数据) | C2 |
| auth/ | 用户与权限 | W2 |
| obs/ | 日志/指标/健康检查 | C12 |

## 运行(当前为 Day 1 骨架)

```bash
cd server
uv sync
uv run uvicorn app.main:app --port 8000
# 然后:curl http://127.0.0.1:8000/healthz
#      curl http://127.0.0.1:8000/api/v1/mock/analysis_result
```

## 纪律

- 只在本树内加文件;契约以 `schemas/` 为准,前端只读渲染。
- 提交信息格式:`[C] 模块: 做了什么`
