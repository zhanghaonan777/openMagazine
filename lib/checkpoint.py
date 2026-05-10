"""checkpoint — write/read checkpoint sidecar JSON files."""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any


def write_checkpoint(
    issue_dir: pathlib.Path,
    stage_name: str,
    decision: str,
    *,
    reason: str = "",
    actor: str = "user",
) -> pathlib.Path:
    """Decision should be 'approved' or 'rejected'."""
    if decision not in ("approved", "rejected"):
        raise ValueError(f"decision must be 'approved' or 'rejected', got {decision!r}")
    out_path = issue_dir / "checkpoints" / f"{stage_name}-{int(time.time())}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": stage_name,
        "decision": decision,
        "reason": reason,
        "actor": actor,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path
