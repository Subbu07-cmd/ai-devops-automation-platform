"""LangGraph incident-triage workflow."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agent.state import TriageState
from app.llm import get_diagnoser
from app.tools import infra


def classify(state: TriageState) -> TriageState:
    alert = state["alert"].lower()
    prod = state.get("environment", "prod") == "prod"
    if prod and any(k in alert for k in ("5xx", "down", "unavailable", "error rate")):
        severity = "SEV1"
    elif prod:
        severity = "SEV2"
    else:
        severity = "SEV3"
    return {"severity": severity}


def gather_context(state: TriageState) -> TriageState:
    svc = state["service"]
    return {
        "logs": infra.get_recent_logs(svc),
        "metrics": infra.get_service_metrics(svc),
        "deployment": infra.get_deployment_status(svc),
    }


def diagnose(state: TriageState) -> TriageState:
    context = {k: state.get(k) for k in ("alert", "logs", "metrics", "deployment")}
    return {"diagnosis": get_diagnoser().diagnose(context)}


def recommend(state: TriageState) -> TriageState:
    svc, diag = state["service"], state["diagnosis"]
    recs = [infra.propose_action("open_incident_channel", svc, f"{state['severity']}: {state['alert']}")]
    if "recent deploy" in diag:
        recs.append(infra.propose_action("rollback_deployment", svc, diag))
    m = state.get("metrics", {})
    if m.get("healthy_pods", 0) < m.get("desired_pods", 0):
        recs.append(infra.propose_action("restart_service", svc, "Unhealthy pods below desired count"))
    return {"recommendations": recs}


def build_graph():
    g = StateGraph(TriageState)
    for name, fn in [("classify", classify), ("gather_context", gather_context),
                     ("diagnose", diagnose), ("recommend", recommend)]:
        g.add_node(name, fn)
    g.set_entry_point("classify")
    g.add_edge("classify", "gather_context")
    g.add_edge("gather_context", "diagnose")
    g.add_edge("diagnose", "recommend")
    g.add_edge("recommend", END)
    return g.compile()


triage_graph = build_graph()
