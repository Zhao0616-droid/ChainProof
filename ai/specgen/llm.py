"""规约生成 LLM 客户端(v0):OpenAI 兼容 + Anthropic Messages 双协议,标准库实现。

配置(优先级从高到低):LLM_API_KEY / LLM_BASE_URL / LLM_MODEL,
兼容 OPENAI_API_KEY、ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN(本机网关)。
无密钥或调用失败 → 空规约降级,不阻塞分析链路(R8)。
"""
import json
import os
import re
import urllib.error
import urllib.request

SYSTEM_PROMPT = (
    "你是智能合约形式化验证专家。为给定 Solidity 合约的每个函数生成一条形式化不变量。"
    "不变量必须使用受限 DSL:仅允许变量名(函数参数与合约状态变量)、非负整数常量、"
    "运算符 + - *、比较符 >= <= > < == != 与括号,不允许函数调用、数组、除号。"
    "所有变量为 uint256 无符号语义:表达'余额足够'请写 balance >= amount,"
    "不要写 balance - amount >= 0(减法会回绕);表达'不会溢出'请写 a + b >= a 之类。"
    "只输出 JSON 数组,元素格式为 "
    '{"function": "函数名", "invariant": "DSL 表达式", "comment": "中文说明"},'
    "不要输出任何其他文字。"
)

DSL_RE = re.compile(r"^[\w\s+\-*()<>=!]+$")
CMP_OPS = (">=", "<=", "==", "!=", ">", "<")


def _config() -> tuple[str, str, str]:
    key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or ""
    )
    base = os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL") or ""
    model = os.environ.get("LLM_MODEL") or os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-4-6"
    return key, base, model


def _anthropic_style(key: str, base: str) -> bool:
    return bool(base and ("anthropic" in base or "claude" in base)) or key.startswith("sk-ant")


def generate_specs(source: str, filename: str, force_offline: bool = False) -> dict:
    key, base, model = _config()
    if force_offline or not key:
        return _offline("未配置 LLM_API_KEY/LLM_BASE_URL")
    try:
        text = _call(key, base, model, source, filename)
        items = _parse(text)
        return {
            "model_version": f"specgen-v0:{model}",
            "specs": items,
            "note": f"{len(items)} 条不变量由 {model} 生成",
        }
    except Exception as e:
        return _offline(f"LLM 调用失败: {e}")


def _call(key: str, base: str, model: str, source: str, filename: str) -> str:
    user = f"合约文件名:{filename}\n合约源码:\n```solidity\n{source}\n```"
    if _anthropic_style(key, base):
        url = base.rstrip("/") + "/v1/messages"
        body = {
            "model": model,
            "max_tokens": 8000,  # 推理模型 thinking 消耗预算,需留足文本输出空间
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        data = json.loads(_post(url, body, headers))
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if isinstance(block, dict)
        )
        if not text:
            raise RuntimeError("LLM 无文本输出(可能被 thinking 耗尽预算)")
        return text
    url = (base or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    }
    headers = {"Authorization": f"Bearer {key}"}
    data = json.loads(_post(url, body, headers))
    return data["choices"][0]["message"]["content"]


def _post(url: str, body: dict, headers: dict) -> str:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}") from e


def _parse(text: str) -> list[dict]:
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out: list[dict] = []
    for item in arr if isinstance(arr, list) else []:
        if not isinstance(item, dict):
            continue
        fn = str(item.get("function", "")).strip()
        inv = str(item.get("invariant", "")).replace(" ", "")
        if not fn or not inv or not DSL_RE.match(inv):
            continue
        if not any(op in inv for op in CMP_OPS):
            continue
        out.append({"function": fn, "invariant": inv, "comment": str(item.get("comment", ""))[:200]})
    return out[:20]


def _offline(note: str) -> dict:
    return {"model_version": "specgen-v0-offline", "specs": [], "note": note}
