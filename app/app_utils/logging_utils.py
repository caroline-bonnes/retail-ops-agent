# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import time
from typing import Any

from google.adk.agents.callback_context import CallbackContext

from app.app_utils.pii import sanitize_pii_recursive

logger = logging.getLogger("retail_ops_agent.telemetry")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"time":"%(asctime)s", "level":"%(levelname)s", "message":%(message)s}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_structured_event(
    event_type: str, payload: dict[str, Any], severity: str = "INFO"
) -> None:
    """Logs a structured JSON payload with PII redacted.

    Args:
        event_type: Category of the event (e.g., 'INTENT', 'OUTCOME', 'GUARDRAIL').
        payload: Event data dictionary.
        severity: Log severity level ('INFO', 'WARNING', 'ERROR').
    """
    sanitized_payload = sanitize_pii_recursive(payload)
    structured_log = {
        "event_type": event_type,
        "payload": sanitized_payload,
    }
    log_json = json.dumps(structured_log)
    if severity == "ERROR":
        logger.error(log_json)
    elif severity == "WARNING":
        logger.warning(log_json)
    else:
        logger.info(log_json)


def log_intent(
    session_id: str,
    agent_name: str,
    intent: str,
    planned_action: str,
    parameters: dict[str, Any],
) -> None:
    """Logs the agent's parsed intent prior to action execution.

    Args:
        session_id: The session ID of the interaction.
        agent_name: Name of the agent initiating the action.
        intent: Classified user intent or operational goal.
        planned_action: The tool or subagent being invoked.
        parameters: Target arguments/parameters for the action.
    """
    log_structured_event(
        event_type="AGENT_INTENT",
        payload={
            "session_id": session_id,
            "agent_name": agent_name,
            "intent": intent,
            "planned_action": planned_action,
            "parameters": parameters,
            "timestamp": time.time(),
        },
        severity="INFO",
    )


def log_outcome(
    session_id: str,
    agent_name: str,
    tool_name: str,
    status: str,
    duration_ms: float,
    summary: str,
    result_data: Any | None = None,
) -> None:
    """Logs the actual outcome and execution metrics after action completion.

    Args:
        session_id: The session ID of the interaction.
        agent_name: Name of the executing agent.
        tool_name: Name of the executed tool.
        status: Execution status ('SUCCESS', 'ERROR', 'GUARDRAIL_BLOCKED', etc.).
        duration_ms: Execution duration in milliseconds.
        summary: Brief outcome summary.
        result_data: Detailed outcome dictionary/response.
    """
    log_structured_event(
        event_type="AGENT_OUTCOME",
        payload={
            "session_id": session_id,
            "agent_name": agent_name,
            "tool_name": tool_name,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "summary": summary,
            "result_preview": str(result_data)[:500] if result_data else None,
            "timestamp": time.time(),
        },
        severity="INFO" if status == "SUCCESS" else "WARNING",
    )


async def intent_outcome_before_tool_callback(
    callback_context: CallbackContext,
    tool_name: str,
    args: dict[str, Any],
) -> dict[str, Any] | None:
    """ADK callback invoked immediately before any tool executes to log Intent."""
    session_id = getattr(callback_context, "session_id", "default_session")
    agent_name = getattr(callback_context, "agent_name", "retail_agent")
    callback_context.state[f"tool_start_time_{tool_name}"] = time.time()

    log_intent(
        session_id=str(session_id),
        agent_name=str(agent_name),
        intent=f"Execute tool '{tool_name}'",
        planned_action=tool_name,
        parameters=args,
    )
    return None


async def intent_outcome_after_tool_callback(
    callback_context: CallbackContext,
    tool_name: str,
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """ADK callback invoked immediately after a tool executes to log Outcome."""
    session_id = getattr(callback_context, "session_id", "default_session")
    agent_name = getattr(callback_context, "agent_name", "retail_agent")
    start_time = callback_context.state.get(f"tool_start_time_{tool_name}", time.time())
    duration_ms = (time.time() - start_time) * 1000.0

    status = "SUCCESS"
    if isinstance(result, dict) and (
        result.get("status") == "error" or "error" in result
    ):
        status = "ERROR"

    log_outcome(
        session_id=str(session_id),
        agent_name=str(agent_name),
        tool_name=tool_name,
        status=status,
        duration_ms=duration_ms,
        summary=f"Finished {tool_name} with status {status}",
        result_data=result,
    )
    return None
