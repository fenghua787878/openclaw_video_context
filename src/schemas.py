"""使用 JSON Schema 做基本校验（draft-07）。不引入重型依赖，仅做关键字段检查。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load_schema(name: str) -> dict[str, Any]:
    p = _SCHEMAS_DIR / f"{name}.schema.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _validate_required(data: dict[str, Any], required: list[str], name: str) -> list[str]:
    missing = [k for k in required if k not in data]
    if missing:
        return [f"{name}: missing required keys: {missing}"]
    return []


def validate_signals(signals: list[dict[str, Any]]) -> list[str]:
    """校验 signals 列表，返回错误信息列表。"""
    errors: list[str] = []
    required = ["id", "title", "url", "source", "reason", "score"]
    for i, s in enumerate(signals):
        if not isinstance(s, dict):
            errors.append(f"signals[{i}]: not an object")
            continue
        errors.extend(_validate_required(s, required, f"signals[{i}]"))
        if "url" in s and not str(s["url"]).startswith(("http://", "https://")):
            errors.append(f"signals[{i}]: url must be http(s)")
    return errors


def validate_state(state: dict[str, Any]) -> list[str]:
    """校验 state 对象。"""
    required = ["run_id", "started_at", "steps", "degradation"]
    return _validate_required(state, required, "state")


def validate_item(item: dict[str, Any]) -> list[str]:
    """校验单条 item。"""
    required = ["signal_id", "url", "reliability"]
    errors = _validate_required(item, required, "item")
    if "reliability" in item and item["reliability"] not in ("high", "medium", "low"):
        errors.append("item: reliability must be high|medium|low")
    return errors


def validate_experiment_row(row: dict[str, Any]) -> list[str]:
    """校验 experiments 单行。兼容旧格式，并支持人工反馈指标字段。"""
    errors = _validate_required(row, ["ts"], "experiment")

    has_legacy_summary = all(k in row for k in ("what_worked", "what_to_try_next"))
    has_manual_metrics = (
        isinstance(row.get("metrics"), dict)
        and all(k in row.get("metrics", {}) for k in ("plays", "likes", "follows"))
        and "content_category" in row
        and "expression_variant" in row
    )

    if not (has_legacy_summary or has_manual_metrics):
        errors.append(
            "experiment: must contain either legacy keys (what_worked + what_to_try_next) "
            "or manual feedback keys (content_category + expression_variant + metrics.plays/likes/follows)"
        )
    return errors
