from fastapi.testclient import TestClient

from app.agent.graph import triage_graph
from app.main import app

client = TestClient(app)


def test_triage_detects_pool_exhaustion_and_recent_deploy():
    out = triage_graph.invoke({"service": "payments-api", "alert": "5xx error rate high", "environment": "prod"})
    assert out["severity"] == "SEV1"
    assert "connection pool" in out["diagnosis"].lower()
    actions = {r["action"]: r for r in out["recommendations"]}
    assert actions["rollback_deployment"]["requires_approval"] is True
    assert actions["restart_service"]["status"] == "pending_approval"


def test_non_prod_is_low_severity():
    out = triage_graph.invoke({"service": "orders-api", "alert": "latency up", "environment": "dev"})
    assert out["severity"] == "SEV3"
    assert all(r["action"] != "rollback_deployment" for r in out["recommendations"])


def test_validate_deployment_endpoint():
    bad = client.post("/validate-deployment", json={"service": "payments-api"}).json()
    good = client.post("/validate-deployment", json={"service": "orders-api"}).json()
    assert bad["recommendation"] == "rollback"
    assert good["passed"] is True
