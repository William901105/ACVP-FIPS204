from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_loads(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
    return json.loads(value)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

