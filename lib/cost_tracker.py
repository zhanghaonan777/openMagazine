"""cost_tracker — track cumulative cost for an issue."""
from __future__ import annotations

import json
import pathlib


class CostTracker:
    def __init__(self, issue_dir: pathlib.Path, *, budget_usd: float):
        self.issue_dir = pathlib.Path(issue_dir)
        self.budget_usd = budget_usd
        self.cumulative_usd = 0.0
        self._path = self.issue_dir / "cost.json"
        if self._path.is_file():
            data = json.loads(self._path.read_text())
            self.cumulative_usd = data.get("cumulative_usd", 0.0)

    def add(self, amount_usd: float) -> dict:
        self.cumulative_usd += amount_usd
        self._save()
        pct = (self.cumulative_usd / self.budget_usd) * 100 if self.budget_usd else 0
        return {
            "cumulative_usd": self.cumulative_usd,
            "budget_usd": self.budget_usd,
            "pct": pct,
            "warning": pct >= 80,
            "hard_stop": pct >= 110,
        }

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"cumulative_usd": self.cumulative_usd, "budget_usd": self.budget_usd}, indent=2),
            encoding="utf-8",
        )
