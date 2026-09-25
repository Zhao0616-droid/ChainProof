"""发现 → 中文解释模板(B7 v0)。LLM 接入后替换为生成式解释。"""

EXPLANATIONS = {
    "reentrancy": "函数 {function} 在外部调用之后仍写入状态变量,违反 CEI(检查-生效-交互)顺序。攻击者合约可在接收转账的回调中重入该函数,在余额扣减前重复提现。",
    "unchecked-low-level-call": "低层级调用(.call/.send)的返回值未被检查。调用失败(如 gas 不足、被调用合约回退)时交易不会回滚,后续逻辑会基于错误前提继续执行。",
    "tx-origin": "使用 tx.origin 做权限判断可被钓鱼攻击利用:用户调用攻击者合约时,攻击者合约再以用户身份调用本合约,tx.origin 仍是用户地址,权限检查被绕过。应改用 msg.sender。",
    "timestamp": "判断依赖 block.timestamp 可被操纵:矿工/验证者可在一定范围内调整时间戳,且同一区块内所有交易的时间戳相同,不能作为随机源或公平依据。",
    "unchecked-overflow": "unchecked 块内的算术运算发生溢出/下溢时不会回滚,结果静默回绕。Z3 求解器已给出使表达式回绕的具体输入,见反例轨迹。",
    "spec-violation": "LLM 生成的形式化不变量被 Z3 判定可违反(SAT):存在具体输入使该性质不成立,见反例轨迹。性质违反可能对应余额、权限或算术类安全缺陷,需人工确认后修复。",
    "spec-proved": "LLM 生成的形式化不变量经 Z3 证明成立(UNSAT,havoc 模型:输入无约束),该性质在任意输入下保持。",
}


def explain(finding: dict, source_lines: list[str]) -> str:
    fn = finding["location"]["function"]
    tpl = EXPLANATIONS.get(finding["type"], "检测到 {type} 类漏洞。")
    text = tpl.format(function=fn, type=finding["type"])
    line_no = finding["location"]["line"]
    if 0 < line_no <= len(source_lines):
        text += f" 相关代码(第 {line_no} 行): {source_lines[line_no - 1].strip()}"
    return text
