# AI-Enabled DevOps Automation Platform

> **About this repo:** my production work lives in private enterprise repositories, so this is a public reference build of the same patterns, written from scratch with sample data and placeholder account IDs.

An agentic AI platform that brings LLM reasoning into day-to-day DevOps work: **incident triage**, **deployment validation** and **guard-railed operational actions**. It's built on **LangGraph**, **AWS Bedrock (Anthropic Claude)**, **FastAPI** and the **Model Context Protocol (MCP)**, so the same tools can be used by the API, by Claude Code or by any MCP-capable agent.

```
            ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
 alert ───▶ │   classify   │ ──▶ │ gather ctx   │ ──▶ │  diagnose    │ ──▶ │  recommend   │ ──▶ result
            │ (severity)   │     │ logs/deploys │     │ (Bedrock LLM)│     │ + guardrails │
            └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                        ▲                                         │
                                        │          MCP tools (infra.py)           │ approval needed for
                                        └─────────────────────────────────────────┘ destructive actions
```

## Features

- **LangGraph incident-triage workflow** with typed state, deterministic routing and an LLM diagnosis step
- **AWS Bedrock** via `langchain-aws`, with a rule-based fallback so everything runs locally and in CI without cloud credentials
- **MCP server** (`mcp_server/server.py`) that exposes infrastructure tools such as logs, deployments, health and restarts to Claude Code and other agents
- **Guardrails**: destructive actions (restart, rollback) are never auto-executed and always come back as `requires_approval`
- **Deployment validation** endpoint that checks health, error rate and latency against thresholds
- **Runs anywhere**: as a FastAPI service (Docker) or as AWS Lambda (via Mangum)

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
curl -s localhost:8000/triage -H 'content-type: application/json' -d '{
  "service": "payments-api",
  "alert": "5xx error rate above 5% for 10 minutes",
  "environment": "prod"
}' | jq
```

To use Bedrock, set `LLM_PROVIDER=bedrock`, `AWS_REGION` and optionally `BEDROCK_MODEL_ID`.

### Use the tools from Claude Code (MCP)

```bash
claude mcp add devops-tools -- python -m mcp_server.server
```

## Project layout

| Path | Purpose |
|------|---------|
| `app/agent/graph.py` | LangGraph state machine for triage |
| `app/tools/infra.py` | Infrastructure tool layer (pluggable backends) |
| `app/llm.py` | Bedrock / fallback LLM factory |
| `app/main.py` | FastAPI API (`/triage`, `/validate-deployment`, `/health`) |
| `mcp_server/server.py` | MCP server exposing the same tools |
| `lambda_handler.py` | AWS Lambda entry point |

## Tests

```bash
pytest -q
```

## Tech

LangGraph · LangChain · AWS Bedrock · MCP · Claude Code · Python · FastAPI · AWS Lambda
