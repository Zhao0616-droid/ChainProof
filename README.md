# ChainProof《链证》智能合约可验证安全审计平台

> 上传 Solidity 合约 → 输出漏洞报告 + **形式化证明** + 修复建议
> 2026 第八届全球校园人工智能算法精英大赛 · 算法创新赛 · 赛题 2:AI+软件创新

## 仓库结构(三棵树 + 唯一共享面)

| 目录 | 归属 | 内容 | 独立产物 |
|---|---|---|---|
| [engine/](engine/) | A | 编译/沙箱/符号执行/求解器/反例解析 | `analyze x.sol → result.json` |
| [ai/](ai/) | B | 规约生成 + 求解器反馈闭环/解释/补丁/评测 | `specgen x.sol → specs.json` |
| [server/](server/) [web/](web/) [deploy/](deploy/) | C | API/队列/存储 ／ M1-M6 前端 ／ 部署 | Web 喂 mock JSON 全流程可点 |
| [schemas/](schemas/) | 共享 | **两个 JSON 契约(冻结,禁止单方改动)** | 契约校验器 |
| [examples/](examples/) | 共享 | 三份样例 + 统一测试合约 VulnerableToken.sol | — |
| [docs/](docs/) | 共享 | 方案/分工/品质清单(另含 api/ops/user-guide 交付文档位) | — |

两个契约:`schemas/path_summary.json`(A 产 → B 用)、`schemas/analysis_result.json`(最终产物,A+B 填、C 只读渲染)。

## 快速开始(各树独立,互不依赖)

```bash
# A 引擎(当前 Day 1 骨架)
uv run --project engine python -m engine.cli.analyze examples/contracts/VulnerableToken.sol -o result.json
uv run --project engine python -m engine.cli.analyze --mock -o result.json

# B AI(当前 Day 1 骨架)
uv run --project ai python -m ai.cli.specgen examples/contracts/VulnerableToken.sol -o specs.json

# C 后端
cd server && uv sync && uv run uvicorn app.main:app --port 8000

# C 前端
cd web && npm install && npm run dev

# 契约自检(三方共用,M8)
uv run schemas/validate.py examples/path_summary.json examples/analysis_result.json result.json
```

## 纪律(来自《链证-分工与集成手册》第 6 章)

- ❌ 改 `schemas/` 字段名/类型;❌ 在别人目录加文件;❌ 复制别人代码改;❌ 口头约定接口
- 提交信息格式:`[A|B|C] 模块: 做了什么`;每次提交必须通过自己的测试
- 主干保护 + 每人一条 feature 分支;每日 18:00 前推送到自己的分支
- 数据集只给运行时拉取脚本,绝不入库(S11);密钥不进仓库(S8)
