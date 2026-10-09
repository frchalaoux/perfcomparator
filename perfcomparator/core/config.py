"""Configuration du serveur PCE."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_token: str = ""
    control_token: str = ""
    port: int = 8765
    reports_dir: Path = Path.home() / "Documents" / "PerfComparator"

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            api_token=os.environ.get("PERFCOMPARATOR_ENGINE_TOKEN", ""),
            control_token=os.environ.get("PERFCOMPARATOR_ENGINE_CONTROL_TOKEN", ""),
            port=int(os.environ.get("PERFCOMPARATOR_ENGINE_PORT", "8765")),
            reports_dir=Path(
                os.environ.get(
                    "PERFCOMPARATOR_WEB_REPORTS_DIR",
                    str(Path.home() / "Documents" / "PerfComparator"),
                )
            ).expanduser(),
        )
