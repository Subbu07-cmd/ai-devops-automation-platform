"""MCP server exposing infrastructure tools to Claude Code and other MCP clients.

Run:  python -m mcp_server.server
Add to Claude Code:  claude mcp add devops-tools -- python -m mcp_server.server
"""
from mcp.server.fastmcp import FastMCP

from app.agent.graph import triage_graph
from app.tools import infra

mcp = FastMCP("devops-tools")


@mcp.tool()
def recent_logs(service: str, minutes: int = 15) -> list[str]:
    """Fetch recent log lines for a service."""
    return infra.get_recent_logs(service, minutes)


@mcp.tool()
def service_metrics(service: str) -> dict:
    """Get error rate, p95 latency and pod health for a service."""
    return infra.get_service_metrics(service)


@mcp.tool()
def deployment_status(service: str) -> dict:
    """Get the current and previous deployed versions of a service."""
    return infra.get_deployment_status(service)


@mcp.tool()
def triage_incident(service: str, alert: str, environment: str = "prod") -> dict:
    """Run the full LangGraph triage workflow and return diagnosis and recommendations."""
    return triage_graph.invoke({"service": service, "alert": alert, "environment": environment})


@mcp.tool()
def propose_action(action: str, service: str, reason: str) -> dict:
    """Propose an operational action. Destructive actions return requires_approval=true."""
    return infra.propose_action(action, service, reason)


if __name__ == "__main__":
    mcp.run()
