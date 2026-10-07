from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def json_safe(value: Any) -> Any:
    """Convert nested values into JSON-serializable Python primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if is_dataclass(value):
        return json_safe(asdict(value))

    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]

    if isinstance(value, Path):
        return str(value)

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    if hasattr(value, "tolist"):
        try:
            return json_safe(value.tolist())
        except Exception:
            pass

    return str(value)
