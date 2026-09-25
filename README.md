# ChainProof《链证》智能合约可验证安全审计平台

> 上传 Solidity 合约 → 输出漏洞报告 + **形式化证明** + 修复建议
> 2026 第八届全球校园人工智能算法精英大赛 · 算法创新赛 · 赛题 2:AI+软件创新

## 仓库结构(三棵树 + 唯一共享面)

| 目录 | 归属 | 内容 | 独立产物 |
|---|---|---|---|
| [engine/](engine/) | A | 编译/沙箱/符号执行/求解器/反例解析 | `analyze x.sol → result.json` |
| [ai/](ai/) | B | 规约生成 + 求解器反馈闭环/解释/补丁/评测 | `specgen x.sol → specs.json` |
| [server/](server/) [web/](web/) [deploy/](deploy/) | C | API/队列/存储 ／ M1-M6 前端 ／ 部署 | 上传→分析→结果页真实全流程可点 |
| [schemas/](schemas/) | 共享 | **两个 JSON 契约(冻结,禁止单方改动)** | 契约校验器 |
| [examples/](examples/) | 共享 | 三份样例 + 统一测试合约 VulnerableToken.sol | — |
| [docs/](docs/) | 共享 | 方案/分工/品质清单(另含 api/ops/user-guide 交付文档位) | — |

两个契约:`schemas/path_summary.json`(A 产 → B 用)、`schemas/analysis_result.json`(最终产物,A+B 填、C 只读渲染)。

## 快速开始(各树独立,互不依赖)

```bash
# A 引擎(当前 Day 1 骨架)
uv run --project engine python -m engine.cli.analyze examples/contracts/VulnerableToken.sol -o result.json
uv run --project engine python -m engine.cli.analyze --mock -o result.json

# B AI(LLM 规约生成;未配置密钥时自动降级输出空规约,不阻塞)
uv run --project ai python -m ai.cli.specgen examples/contracts/VulnerableToken.sol -o specs.json
# 可选:--offline 强制离线降级

# LLM 配置(环境变量,支持 Anthropic Messages 与 OpenAI 兼容两种协议,密钥不入仓库)
#   LLM_API_KEY / LLM_BASE_URL / LLM_MODEL(优先)
#   兼容 OPENAI_API_KEY/OPENAI_BASE_URL、ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN/ANTHROPIC_BASE_URL/ANTHROPIC_MODEL

# C 后端
cd server && uv sync && uv run uvicorn app.main:app --port 8000

# C 前端
cd web && npm install && npm run dev

# 契约自检(三方共用,M8)
uv run schemas/validate.py examples/path_summary.json examples/analysis_result.json result.json
```

## Docker 一键部署(演示版)

```bash
cd deploy/compose
docker compose up -d --build
# 访问 http://localhost:8080(nginx 代理 /api → api:8000,分析记录持久化在 ./data)
```

可选:仓库根目录放 `.env`(已在 .gitignore,不入库)写 LLM 凭证,compose 会透传给 api 容器启用 LLM 规约生成;不配置则容器内自动走离线降级(仅模式检测 + Z3 溢出证明)。

镜像说明(demo 单环境布局):`api` 镜像内含 engine/ai/server 三树代码与同一套 Python 依赖(引擎以 `sys.executable` 子进程运行,`ai` 当前纯 stdlib),独立部署后按树拆分。
