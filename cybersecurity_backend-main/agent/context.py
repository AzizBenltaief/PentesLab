"""Shared helpers to build compact LLM contexts from scan results."""

import json
from typing import Any, Dict, Optional

MAX_STR_LENGTH = 400
MAX_LIST_ITEMS = 30
MAX_DICT_KEYS = 40


def _compact(value: Any, depth: int = 0) -> Any:
    """Recursively truncate strings, lists and dicts to keep prompts small."""
    if depth > 6:
        return None
    if isinstance(value, dict):
        return {
            k: _compact(v, depth + 1)
            for k, v in list(value.items())[:MAX_DICT_KEYS]
        }
    if isinstance(value, list):
        return [_compact(v, depth + 1) for v in value[:MAX_LIST_ITEMS]]
    if isinstance(value, str):
        return value[:MAX_STR_LENGTH]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:MAX_STR_LENGTH]


def build_scan_context(
    scan_results: Optional[Dict[str, Any]],
    target: str = "",
) -> str:
    """Build a compact JSON string of scan data for inclusion in LLM prompts."""
    data = _compact(scan_results or {})
    if target:
        data = {"target": target, **({"results": data} if data else {})}
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception:
        return str(data)
