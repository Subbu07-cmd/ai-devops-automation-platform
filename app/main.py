from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.agent.graph import triage_graph
from app.tools import infra

app = FastAPI(title="AI DevOps Automation Platform", version="1.0.0")


class TriageRequest(BaseModel):
    service: str
    alert: str
    environment: str = "prod"


class ValidationRequest(BaseModel):
    service: str
    max_error_rate: float = Field(0.01, ge=0, le=1)
    max_p95_latency_ms: int = 500


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triage")
def triage(req: TriageRequest):
    return triage_graph.invoke(req.model_dump())


@app.post("/validate-deployment")
def validate_deployment(req: ValidationRequest):
    m = infra.get_service_metrics(req.service)
    checks = {
        "error_rate": m["error_rate"] <= req.max_error_rate,
        "latency": m["p95_latency_ms"] <= req.max_p95_latency_ms,
        "replicas": m["healthy_pods"] >= m["desired_pods"],
    }
    passed = all(checks.values())
    return {
        "service": req.service,
        "passed": passed,
        "checks": checks,
        "metrics": m,
        "recommendation": "promote" if passed else "rollback",
    }
