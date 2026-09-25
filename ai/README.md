# ai/ — AI 层(人 B)

> 一句话:让 AI 把证据补全。消费 A 的 `path_summary.json`,填 `analysis_result.json` 中 B 负责字段。

## 目录

| 目录 | 内容 | 对应任务 |
|---|---|---|
| llm/ | LLM 接入(API 优先 + 本地双通道) | B3 |
| spec/ | 规约生成 + 求解器反馈闭环 ⭐ | B4/B5 |
| rank/ | 路径优先级排序(suspicious_score) | B6 |
| explain/ | 反例 → 人话解释 | B7 |
| patch/ | 补丁生成 + 有效性验证 | B8 |
| dataset/ | 数据获取、清洗、规约样本整理 | B1/B9 |
| eval/ | 指标评测脚本(一键全指标) | B11 |
| train/ | (条件)QLoRA 微调 | B12 |
| cli/ | specgen 入口 | — |

## 运行(当前为 Day 1 骨架 stub)

```bash
cd ..   # 回到仓库根目录
uv run --project ai python -m ai.cli.specgen examples/contracts/VulnerableToken.sol -o specs.json
```

## 止损判据

rejection sampling 候选通过率 < 5% → 放弃训练,退回「API + 提示工程 + 人工确认」。

## 纪律

- 只在本树内加文件;契约以 `schemas/` 为准,不得改字段。
- 数据集只放拉取脚本,绝不入库(S11)。
- 提交信息格式:`[B] 模块: 做了什么`
