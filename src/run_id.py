"""生成 run_id 与 signal id，供工作流与 Scout 使用。"""
from __future__ import annotations

from datetime import datetime, timezone


def make_run_id(prefix: str = "daily") -> str:
    """生成唯一 run_id，格式：daily_YYYYMMDD_HHMMSS。"""
    now = datetime.now(timezone.utc)
    return f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}"


def make_signal_id(index: int) -> str:
    """生成信号 id，如 sig_001。"""
    return f"sig_{index:03d}"
