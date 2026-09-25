"""审计报告导出(M4 v0):Markdown 格式,内容取自 analysis_result 契约字段。"""
import time

SEVERITY_LABEL = {"high": "高危", "medium": "中危", "low": "低危", "info": "提示"}
EVIDENCE_KIND_LABEL = {"formal": "形式化证明", "counterexample": "反例", "pattern": "模式匹配"}
SMT_LABEL = {"sat": "可满足(存在违规输入)", "unsat": "不可满足(已证明)", "unknown": "未知"}


def build_report(payload: dict) -> str:
    r = payload["result"]
    c = r["contract"]
    a = r["analysis"]
    findings = r["findings"]
    counts = {sev: sum(1 for f in findings if f["severity"] == sev) for sev in SEVERITY_LABEL}
    lines: list[str] = []
    add = lines.append

    add(f"# {payload['name']} 智能合约安全审计报告")
    add("")
    add(f"> 生成时间:{time.strftime('%Y-%m-%d %H:%M:%S')} · 引擎:ChainProof v0.1(演示版)")
    add("")
    add("## 1. 合约信息")
    add("")
    add(f"- 合约名:`{c['name']}`")
    add(f"- 编译器:{c['compiler']}")
    add(f"- 源码哈希:`{c['hash']}`")
    add("")
    add("## 2. 分析概览")
    add("")
    add(f"- 分析状态:`{a['status']}`")
    add(f"- 证明覆盖:{a['coverage']['proved']}/{a['coverage']['total']}(已证明/总查询)")
    add(f"- 耗时:{a['duration_ms']} ms · 模型:{a['model_version']}")
    add(f"- 漏洞统计:高危 {counts['high']} · 中危 {counts['medium']} · 低危 {counts['low']} · 提示 {counts['info']}")
    add("")

    for note in r.get("unverified", []):
        add(f"> 诚实声明:未验证范围 {note.get('scope', 'all')}:{note.get('reason', '')}")
        add("")

    add("## 3. 漏洞详情")
    add("")
    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    for i, f in enumerate(sorted(findings, key=lambda x: order[x["severity"]]), 1):
        loc = f["location"]
        ev = f["evidence"]
        add(f"### 3.{i} [{SEVERITY_LABEL[f['severity']]}] {f['type']}({f['swc']})")
        add("")
        add(f"- 位置:`{loc['file']}` 第 {loc['line']} 行{f'({loc["function"]})' if loc.get('function') else ''}")
        add(f"- 证据:{EVIDENCE_KIND_LABEL[ev['kind']]}{' · ' + SMT_LABEL[ev['smt_status']] if ev.get('smt_status') else ''}")
        if ev.get("proof_ref"):
            add(f"- 证明引用:`{ev['proof_ref']}`")
        add(f"- 说明:{f['explanation']}")
        if ev.get("counterexample"):
            add("- 反例轨迹:")
            add("")
            add("  | 步骤 | 状态 |")
            add("  |---|---|")
            for step in ev["counterexample"]:
                state = "; ".join(f"`{k}` = {v}" for k, v in step["state"].items())
                add(f"  | {step['step']} | {state} |")
            add("")
        if f["patch"].get("diff"):
            verified = "已验证" if f["patch"].get("verified") else "未验证"
            add(f"- 修复建议({verified}):")
            add("")
            add("  ```diff")
            add("\n".join("  " + line for line in f["patch"]["diff"].splitlines()))
            add("  ```")
        add("")

    add("## 4. 免责声明")
    add("")
    add("本报告由 ChainProof 演示版自动生成,证据类型为 pattern 的发现未经求解器证明,需人工复核;")
    add("未验证范围见上方诚实声明。最终结论以人工审计为准。")
    add("")
    return "\n".join(lines)
