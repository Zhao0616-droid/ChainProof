# server/ — 产品层后端(人 C)

> 一句话:把证据变成产品。前端换真引擎时一行不改(验收标准 C-②)。

## 目录

| 目录 | 内容 | 对应任务 |
|---|---|---|
| app/ | FastAPI 入口与路由 | C2 |
| api/ | 业务接口(分析/项目/规约库/知识库) | C2/C5/C6/C7 |
| taskqueue/ | 任务队列(排队/进度/重试) | C2 |
| storage/ | 持久化(结果/项目/用户数据) | C2 |
| auth/ | 用户与权限 | W2 |
| obs/ | 日志/指标/健康检查 | C12 |

## 运行

```bash
cd server
uv sync
uv run uvicorn app.main:app --port 8000
# 接口:/healthz、POST /api/v1/analyze(一次请求返完整详情)、
#       GET /api/v1/analyses[/{id}]、DELETE /api/v1/analyses/{id}、
#       GET /api/v1/analyses/{id}/report(Markdown 审计报告下载)、
#       POST /api/v1/batch + GET /api/v1/tasks/{task_id}(批量,内存队列)、
#       GET /api/v1/sample(示例合约)
```

分析链路:specgen(B,LLM 规约,超时 150s)→ engine analyze(A,检测+规约证明)→ enrich(B,解释/补丁)。
LLM 凭证读环境变量(LLM_API_KEY/LLM_BASE_URL/LLM_MODEL,兼容 OPENAI_*/ANTHROPIC_*),未配置时 specgen 离线降级为空规约,不阻塞分析。

## 纪律

- 只在本树内加文件;契约以 `schemas/` 为准,前端只读渲染。
- 提交信息格式:`[C] 模块: 做了什么`
