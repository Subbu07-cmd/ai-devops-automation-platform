"""Infrastructure tool layer.

Every tool is a plain function, so the LangGraph agent, the FastAPI API and the
MCP server all share one implementation. The default backend returns
deterministic sample data so the platform runs locally and in CI. Swap
`BACKEND` for a CloudWatch / Kubernetes / Argo CD client in real environments.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime

DESTRUCTIVE_ACTIONS = {"restart_service", "rollback_deployment", "scale_to_zero"}


@dataclass
class SampleBackend:
    """Deterministic in-memory backend used for local runs and tests."""

    deployments: dict[str, dict] = field(default_factory=lambda: {
        "payments-api": {"version": "v2.14.0", "previous": "v2.13.2", "deployed_minutes_ago": 12},
        "orders-api": {"version": "v1.8.3", "previous": "v1.8.2", "deployed_minutes_ago": 4320},
    })

    def logs(self, service: str, minutes: int) -> list[str]:
        if service == "payments-api":
            return [
                "ERROR db.pool: timeout acquiring connection after 30000ms",
                "ERROR http: 503 upstream connect error",
                "WARN  db.pool: active=50 idle=0 max=50",
            ]
        return ["INFO  request completed status=200"]

    def metrics(self, service: str) -> dict:
        if service == "payments-api":
            return {"error_rate": 0.071, "p95_latency_ms": 2400, "healthy_pods": 3, "desired_pods": 6}
        return {"error_rate": 0.002, "p95_latency_ms": 180, "healthy_pods": 4, "desired_pods": 4}


BACKEND = SampleBackend()


def get_recent_logs(service: str, minutes: int = 15) -> list[str]:
    """Return recent log lines for a service."""
    return BACKEND.logs(service, minutes)


def get_service_metrics(service: str) -> dict:
    """Return key golden-signal metrics for a service."""
    return BACKEND.metrics(service)


def get_deployment_status(service: str) -> dict:
    """Return current/previous version and how long ago it was deployed."""
    return BACKEND.deployments.get(service, {"version": "unknown", "previous": None, "deployed_minutes_ago": None})


def propose_action(action: str, service: str, reason: str) -> dict:
    """Propose an operational action. Destructive actions always require human approval."""
    requires_approval = action in DESTRUCTIVE_ACTIONS or os.getenv("REQUIRE_APPROVAL_FOR_ALL") == "1"
    return {
        "action": action,
        "service": service,
        "reason": reason,
        "requires_approval": requires_approval,
        "status": "pending_approval" if requires_approval else "executed",
        "timestamp": datetime.now(UTC).isoformat(),
    }
