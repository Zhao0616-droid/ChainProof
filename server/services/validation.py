"""上传校验(S6):单文件与批量共用。"""
import re

from fastapi import HTTPException

MAX_SOURCE_CHARS = 100_000
PRAGMA_RE = re.compile(r"pragma\s+solidity")


def validate_source(filename: str, source: str) -> None:
    if not filename.lower().endswith(".sol"):
        raise HTTPException(status_code=400, detail="仅支持 .sol 文件")
    if len(source) > MAX_SOURCE_CHARS:
        raise HTTPException(status_code=413, detail=f"文件过大(>{MAX_SOURCE_CHARS} 字符)")
    if "\x00" in source:
        raise HTTPException(status_code=400, detail="二进制文件不允许上传")
    if "contract " not in source and not PRAGMA_RE.search(source):
        raise HTTPException(status_code=400, detail="文件内容不像 Solidity 合约(缺少 contract 声明或 pragma)")
