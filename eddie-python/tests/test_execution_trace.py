"""Tests for persisted, privacy-conscious plugin execution traces."""
import json
from dataclasses import dataclass

import numpy as np

from orchestrator.execution_trace import ExecutionTrace


@dataclass
class SampleOutput:
    text: str


@dataclass
class SecretOutput:
    api_key: str


def test_trace_records_run_cycles_and_dataclass_outputs(tmp_path):
    trace = ExecutionTrace(tmp_path)
    trace.record(
        "configuration",
        config={"api_key": "do-not-save", "nested": {"access_token": "private"}},
    )
    trace.record_cycle(
        1,
        {
            "ImageProcessor": {
                "ocr": SampleOutput("recognized text"),
                "auth": SecretOutput("do-not-save-this-either"),
                "frame": np.zeros((2, 3, 3), dtype=np.uint8),
            }
        },
        {"ImageProcessor": {"status": "ok", "latency_ms": 12.5}},
    )
    trace.close()

    records = [json.loads(line) for line in trace.path.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == [
        "run_started",
        "configuration",
        "plugin_cycle",
        "run_finished",
    ]
    assert records[1]["config"]["api_key"] == "[REDACTED]"
    assert records[1]["config"]["nested"]["access_token"] == "[REDACTED]"
    output = records[2]["output"]
    assert output["ocr"] == {"text": "recognized text"}
    assert output["auth"]["api_key"] == "[REDACTED]"
    assert output["frame"] == {
        "type": "ndarray",
        "shape": [2, 3, 3],
        "dtype": "uint8",
    }
    assert records[2]["status"] == "ok"
    assert records[2]["latency_ms"] == 12.5
    assert records[3]["status"] == "completed"


def test_trace_closes_with_error_status_and_is_idempotent(tmp_path):
    trace = ExecutionTrace(tmp_path)
    trace.close("error", error="camera unavailable")
    trace.close("completed")

    records = [json.loads(line) for line in trace.path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert records[-1]["status"] == "error"
    assert records[-1]["error"] == "camera unavailable"
