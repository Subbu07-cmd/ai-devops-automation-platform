"""LLM factory: AWS Bedrock (Claude) in real environments, a rule-based fallback otherwise."""
from __future__ import annotations

import os


class RuleBasedDiagnoser:
    """Deterministic stand-in for the LLM, used in tests and offline runs."""

    def diagnose(self, context: dict) -> str:
        logs = " ".join(context.get("logs", [])).lower()
        deploy = context.get("deployment", {})
        if "pool" in logs and "timeout" in logs:
            cause = "Database connection pool exhaustion"
        elif "oom" in logs or "out of memory" in logs:
            cause = "Container memory exhaustion (OOMKilled)"
        else:
            cause = "No clear signature in logs; needs human investigation"
        recent = deploy.get("deployed_minutes_ago")
        if recent is not None and recent <= 60:
            cause += f" — likely introduced by recent deploy {deploy.get('version')}"
        return cause


class BedrockDiagnoser:
    def __init__(self) -> None:
        from langchain_aws import ChatBedrockConverse

        self.llm = ChatBedrockConverse(
            model=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            temperature=0,
        )

    def diagnose(self, context: dict) -> str:
        prompt = (
            "You are an SRE assistant. Given the incident context below, state the single most "
            "likely root cause in one sentence. Do not invent data.\n\n" + repr(context)
        )
        return self.llm.invoke(prompt).content


def get_diagnoser():
    if os.getenv("LLM_PROVIDER", "rules").lower() == "bedrock":
        return BedrockDiagnoser()
    return RuleBasedDiagnoser()
