"""原子写 JSON/JSONL 与读文件，路径统一用 pathlib。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def write_json(path: Path, data: Any, indent: int = 2) -> None:
    """原子写入 JSON：先写 .tmp 再 replace。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> Any:
    """读取 JSON 文件。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """原子追加 JSONL：先读现有内容，追加后写 tmp 再 replace。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    new_lines = [json.dumps(r, ensure_ascii=False) for r in records]
    new_content = (existing + "\n" + "\n".join(new_lines)).strip() + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    tmp.replace(path)


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    """读取 JSONL，可选只取最后 limit 行。"""
    p = Path(path)
    if not p.exists():
        return []
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    if limit is not None and limit > 0:
        out = out[-limit:]
    return out


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """原子写入整份 JSONL：先写 tmp 再 replace。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    content = "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
