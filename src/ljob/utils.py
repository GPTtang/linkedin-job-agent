import json
from typing import Any


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def loads(data: str | None, default: Any):
    if not data:
        return default
    try:
        return json.loads(data)
    except Exception:
        return default
