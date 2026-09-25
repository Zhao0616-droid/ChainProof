"""补丁模板(B8 v0):按漏洞类型生成修复建议 diff。

demo 范围:verified 恒为 False;真实补丁生成与打补丁重跑验证见 B8。
"""
import re

STATE_WRITE_RE = re.compile(r"\b\w+\s*(\+=|-=|\+\+|--)|[\w\]]+\s*=")


def build_patch(finding: dict, source_lines: list[str]) -> dict:
    file = finding["location"]["file"]
    t = finding["type"]
    if t == "reentrancy":
        diff = _reentrancy(finding, source_lines, file)
    elif t == "unchecked-low-level-call":
        diff = _insert_check(finding, source_lines, file)
    elif t == "tx-origin":
        diff = _replace_line(finding, source_lines, file)
    elif t == "timestamp":
        diff = _add_comment(finding, source_lines, file)
    elif t == "unchecked-overflow":
        diff = _unchecked_note(finding, source_lines, file)
    else:
        diff = f"--- a/{file}\n+++ b/{file}\n@@ 暂无模板化修复建议 @@\n"
    return {"diff": diff, "verified": False}


def _lines(finding: dict, source_lines: list[str]) -> list[str]:
    return source_lines


def _reentrancy(finding: dict, source_lines: list[str], file: str) -> str:
    call_line = finding["location"]["line"]
    write_line = None
    for no in range(call_line, len(source_lines)):
        if STATE_WRITE_RE.search(source_lines[no]) and ".call" not in source_lines[no] and ".send" not in source_lines[no]:
            write_line = no + 1
            break
    if write_line is None or call_line > len(source_lines):
        return f"--- a/{file}\n+++ b/{file}\n@@ 修复建议:把状态更新移到外部调用之前(CEI) @@\n"
    call_text = source_lines[call_line - 1].rstrip()
    write_text = source_lines[write_line - 1].rstrip()
    return (
        f"--- a/{file}\n+++ b/{file}\n"
        f"@@ -{call_line},1 +{write_line},1 @@\n"
        f"-{call_text}\n+{write_text}\n"
        f"@@ -{write_line},1 +{call_line},1 @@\n"
        f"-{write_text}\n+{call_text}\n"
    )


def _insert_check(finding: dict, source_lines: list[str], file: str) -> str:
    no = finding["location"]["line"]
    if no > len(source_lines):
        return f"--- a/{file}\n+++ b/{file}\n@@ 修复建议:检查低层级调用返回值 @@\n"
    text = source_lines[no - 1]
    indent = text[: len(text) - len(text.lstrip())]
    return (
        f"--- a/{file}\n+++ b/{file}\n"
        f"@@ -{no},1 +{no},2 @@\n"
        f" {text.rstrip()}\n"
        f"+{indent}require(ok, \"call failed\");\n"
    )


def _replace_line(finding: dict, source_lines: list[str], file: str) -> str:
    no = finding["location"]["line"]
    if no > len(source_lines):
        return f"--- a/{file}\n+++ b/{file}\n@@ 修复建议:改用 msg.sender 鉴权 @@\n"
    old = source_lines[no - 1].rstrip()
    new = old.replace("tx.origin", "msg.sender")
    return f"--- a/{file}\n+++ b/{file}\n@@ -{no},1 +{no},1 @@\n-{old}\n+{new}\n"


def _add_comment(finding: dict, source_lines: list[str], file: str) -> str:
    no = finding["location"]["line"]
    if no > len(source_lines):
        return f"--- a/{file}\n+++ b/{file}\n@@ 修复建议:避免依赖区块时间戳 @@\n"
    text = source_lines[no - 1]
    indent = text[: len(text) - len(text.lstrip())]
    return (
        f"--- a/{file}\n+++ b/{file}\n"
        f"@@ -{no},1 +{no},2 @@\n"
        f" {text.rstrip()}\n"
        f"+{indent}// 建议:改用链上预言机或 commit-reveal 方案,不要用区块时间戳做随机源\n"
    )


def _unchecked_note(finding: dict, source_lines: list[str], file: str) -> str:
    no = finding["location"]["line"]
    if no > len(source_lines):
        return f"--- a/{file}\n+++ b/{file}\n@@ 修复建议:移除 unchecked,使用 0.8 默认的溢出检查 @@\n"
    text = source_lines[no - 1]
    indent = text[: len(text) - len(text.lstrip())]
    return (
        f"--- a/{file}\n+++ b/{file}\n"
        f"@@ -{no},1 +{no},2 @@\n"
        f" {text.rstrip()}\n"
        f"+{indent}// 修复建议:移除 unchecked 包装,让编译器默认检查溢出(0.8+)\n"
    )
