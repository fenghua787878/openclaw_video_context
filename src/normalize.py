"""简单去重与规范化（时间、URL 等）。"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """简单 URL 规范化：strip、统一 scheme。"""
    u = url.strip()
    if not u:
        return u
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    try:
        p = urlparse(u)
        return f"{p.scheme}://{p.netloc}{p.path}" if p.path else f"{p.scheme}://{p.netloc}/"
    except Exception:
        return url.strip()


def normalize_published_at(s: str) -> str:
    """时间未知或无效时返回 'unknown'。"""
    if not s or not str(s).strip():
        return "unknown"
    t = str(s).strip().lower()
    if t in ("unknown", "n/a", "-", "?"):
        return "unknown"
    return str(s).strip()


def dedupe_signals_by_url(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 url 去重，保留第一次出现。"""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for s in signals:
        url = (s.get("url") or "").strip()
        url = normalize_url(url)
        if url in seen:
            continue
        seen.add(url)
        out.append(s)
    return out
