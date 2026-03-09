"""从 signals + items 生成简报结构的辅助（摘要、角度归纳等）。供 Agent 或脚本调用。"""
from __future__ import annotations

from typing import Any


def top_angles_from_signals(
    signals: list[dict[str, Any]], max_angles: int = 5
) -> list[str]:
    """从信号中归纳若干角度（按 score 取高，再取 reason 摘要）。"""
    sorted_sigs = sorted(
        [s for s in signals if isinstance(s, dict) and s.get("score") is not None],
        key=lambda x: float(x.get("score", 0)),
        reverse=True,
    )
    angles: list[str] = []
    for s in sorted_sigs[: max_angles * 2]:
        reason = (s.get("reason") or "").strip()
        if reason and reason not in angles:
            angles.append(reason)
        if len(angles) >= max_angles:
            break
    return angles[:max_angles]


def evidence_list(
    signals: list[dict[str, Any]], items: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """生成 Evidence 列表：point, signal_id, source, url。"""
    by_id = {s["id"]: s for s in signals if isinstance(s, dict) and s.get("id")}
    out: list[dict[str, str]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        sid = it.get("signal_id")
        s = by_id.get(sid) if sid else None
        point = (it.get("content") or (s.get("title") if s else ""))[:200]
        source = (s.get("source") if s else "") or it.get("url", "")
        out.append({
            "point": point,
            "signal_id": sid or "",
            "source": source,
            "url": it.get("url", ""),
        })
    return out
