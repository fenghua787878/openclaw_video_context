#!/usr/bin/env python3
"""
信号发现执行器（过渡层）。
输入：关键词（argv 或 env QUERY/KEYWORDS）
输出：signals.json 或 stdout JSON。
无外部 API 时：可读 mock 输入或打印说明，供 OpenClaw 或人工替代。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# 可选：从项目根加载 src
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from src.run_id import make_signal_id
except ImportError:
    def make_signal_id(i: int) -> str:
        return f"sig_{i:03d}"


def get_keywords() -> list[str]:
    """从 argv 或环境变量获取关键词。"""
    if len(sys.argv) > 1:
        return sys.argv[1:]
    raw = os.environ.get("QUERY") or os.environ.get("KEYWORDS") or ""
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def mock_signals(keywords: list[str]) -> list[dict[str, Any]]:
    """无 web_search 时返回 mock 信号，仅作占位。"""
    signals = []
    for i, kw in enumerate(keywords[:10] or ["示例主题"]):
        signals.append({
            "id": make_signal_id(i + 1),
            "title": f"【Mock】与 {kw} 相关的内容",
            "url": "https://example.com/mock-signal",
            "source": "mock",
            "published_at": "unknown",
            "reason": "无 web_search 时的占位条目，请使用 OpenClaw web_search 或配置 API",
            "score": 5.0,
        })
    return signals


def main() -> int:
    keywords = get_keywords()
    if not keywords:
        print(
            "usage: fetch_sources.py <keyword1> [keyword2 ...]\n"
            "   or: QUERY='kw1,kw2' fetch_sources.py\n"
            "无关键词且无 web_search 时，将输出 mock 信号。",
            file=sys.stderr,
        )
        signals = mock_signals(["示例"])
    else:
        # 实际环境应由 OpenClaw 的 web_search 完成；此处仅作过渡
        signals = mock_signals(keywords)

    out = os.environ.get("OUT_SIGNALS")
    payload = json.dumps(signals, ensure_ascii=False, indent=2)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(payload, encoding="utf-8")
        print(f"Wrote {len(signals)} signals to {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
