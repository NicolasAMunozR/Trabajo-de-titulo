"""Append-only JSONL execution traces for reproducible plugin-flow inspection."""
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

logger = logging.getLogger(__name__)


def json_safe(value: Any) -> Any:
    """Convert plugin outputs to JSON without embedding raw image arrays."""
    if is_dataclass(value) and not isinstance(value, type):
        return json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return {
            "type": "ndarray",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
        }
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def redact_sensitive(value: Any) -> Any:
    """Redact common credential fields before writing configuration to disk."""
    sensitive_names = ("api_key", "apikey", "token", "password", "secret")
    if is_dataclass(value) and not isinstance(value, type):
        return redact_sensitive(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): (
                "[REDACTED]"
                if any(term in str(key).lower() for term in sensitive_names)
                else redact_sensitive(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item) for item in value]
    return json_safe(value)


class ExecutionTrace:
    """Writes run lifecycle, per-plugin cycle outputs and errors to JSONL."""

    def __init__(self, directory: str | Path) -> None:
        trace_directory = Path(directory)
        trace_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_id = str(uuid4())
        self.path = trace_directory / f"plugin-flow-{timestamp}-{self.run_id[:8]}.jsonl"
        self._stream = self.path.open("a", encoding="utf-8")
        self._write({
            "event": "run_started",
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record(self, event: str, **fields: Any) -> None:
        self._write({
            "event": event,
            "run_id": self.run_id,
            **redact_sensitive(fields),
        })

    def record_cycle(
        self,
        cycle: int,
        results: dict[str, Any],
        metrics: dict[str, dict],
    ) -> None:
        recorded_at = datetime.now(timezone.utc).isoformat()
        for plugin_name, output in results.items():
            metric = metrics.get(plugin_name, {})
            self._write({
                "event": "plugin_cycle",
                "run_id": self.run_id,
                "cycle": cycle,
                "timestamp": recorded_at,
                "plugin": plugin_name,
                "status": metric.get("status", "unknown"),
                "latency_ms": metric.get("latency_ms"),
                "output": redact_sensitive(output),
            })

    def close(self, status: str = "completed", error: str | None = None) -> None:
        if self._stream.closed:
            return
        fields = {"status": status}
        if error:
            fields["error"] = error
        self.record("run_finished", **fields)
        self._stream.close()

    def _write(self, record: dict[str, Any]) -> None:
        try:
            self._stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._stream.flush()
        except (OSError, TypeError, ValueError):
            logger.exception("No se pudo escribir la traza JSONL: %s", self.path)
            raise
