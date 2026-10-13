from __future__ import annotations

from typing import TypedDict


class TriageState(TypedDict, total=False):
    service: str
    alert: str
    environment: str
    severity: str
    logs: list[str]
    metrics: dict
    deployment: dict
    diagnosis: str
    recommendations: list[dict]
