import json
from typing import Any, Optional


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def loads(data: Optional[str], default: Any) -> Any:
    if not data:
        return default
    try:
        return json.loads(data)
    except Exception:
        return default
