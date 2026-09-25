# engine/ — 引擎层(人 A)

> 一句话:合约进,证据出。产出 `path_summary.json` 与 `analysis_result.json`(A 负责字段)。

## 目录

| 目录 | 内容 | 对应任务 |
|---|---|---|
| compiler/ | 多版本 solc 编译(0.4-0.8) | A1 |
| sandbox/ | 沙箱执行封装(隔离/限额/禁网) | A2 |
| symbolic/ | 符号执行(Mythril 主 / Manticore 备) | A3 |
| static/ | 静态分析初筛(Slither) | A4 |
| solver/ | Z3 主 / CVC5 备 + SMT-LIB 生成 | A5 |
| counterexample/ | 反例解析 → 结构化轨迹 | A6 |
| rules/ | 7 类漏洞模式库(对齐 SWC) | A8 |
| paths/ | 路径裁剪 + 超时降级 | A9 |
| cli/ | analyze 入口 | A7/A11 |
| obs/ | 日志、指标、耗时埋点 | A14 |

## 运行(当前为 Day 1 骨架 stub)

```bash
cd ..   # 回到仓库根目录
uv run --project engine python -m engine.cli.analyze examples/contracts/VulnerableToken.sol -o result.json
uv run --project engine python -m engine.cli.analyze --mock -o result.json   # 输出完整样例
uv run schemas/validate.py result.json                                       # 契约自检
```

## 纪律

- 只在本树内加文件;契约以 `schemas/` 为准,不得改字段。
- 提交信息格式:`[A] 模块: 做了什么`
