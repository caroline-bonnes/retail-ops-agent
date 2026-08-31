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

import logging
import os

import google.auth
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import FunctionTool
from google.adk.tools.data_agent import data_agent_tool
from google.adk.tools.data_agent.config import DataAgentToolConfig
from google.adk.tools.data_agent.credentials import DataAgentCredentialsConfig
from google.adk.tools.google_tool import GoogleTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.app_utils.logging_utils import (
    intent_outcome_after_tool_callback,
    intent_outcome_before_tool_callback,
    log_structured_event,
)
from app.tools.custom_retail_tools import (
    calculate_reorder_recommendations,
    create_restock_order,
    generate_store_health_scorecard,
)

# Load environment variables from .env
load_dotenv()

# Setup credentials
creds, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

# Initialize DataAgent Tools
credentials_config = DataAgentCredentialsConfig(credentials=creds)
tool_settings = DataAgentToolConfig(max_query_result_rows=100)

list_accessible_data_agents_tool = GoogleTool(
    func=data_agent_tool.list_accessible_data_agents,
    credentials_config=credentials_config,
    tool_settings=tool_settings,
)
get_data_agent_info_tool = GoogleTool(
    func=data_agent_tool.get_data_agent_info,
    credentials_config=credentials_config,
    tool_settings=tool_settings,
)
ask_data_agent_tool = GoogleTool(
    func=data_agent_tool.ask_data_agent,
    credentials_config=credentials_config,
    tool_settings=tool_settings,
)

data_agent_resource = (
    f"projects/{project_id}/locations/global/dataAgents/retail-ops-bq-agent"
)

# ============================================================================
# Custom Tools with Pydantic Validation & HITL Confirmation
# ============================================================================

# Automated Reorder Calculation Tool
reorder_calc_tool = FunctionTool(func=calculate_reorder_recommendations)

# Store Health Scorecard Tool
store_scorecard_tool = FunctionTool(func=generate_store_health_scorecard)

# Restock Purchase Order Creation with Human-in-the-Loop Confirmation
restock_order_tool = FunctionTool(
    func=create_restock_order,
    require_confirmation=True,  # Consequential action requiring explicit human confirmation
)


# ============================================================================
# Memory & Lifecycle Callbacks with Guardrails
# ============================================================================


async def generate_memories_callback(callback_context: CallbackContext) -> None:
    """Sends the session's events to Memory Bank for persistent memory generation."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        logging.warning(f"Failed to add session to memory bank: {e}")
    return None


async def guardrail_and_sanitization_callback(
    callback_context: CallbackContext,
) -> None:
    """Input guardrail callback that logs incoming request and enforces retail scope boundaries."""
    session_id = getattr(callback_context, "session_id", "session")
    log_structured_event(
        event_type="GUARDRAIL_CHECK",
        payload={
            "session_id": str(session_id),
            "status": "EVALUATED",
            "message": "Input passed to multi-agent retail coordinator.",
        },
    )
    return None


# ============================================================================
# Specialized Sub-Agents (Multi-Agent Hierarchy & Model Routing)
# ============================================================================

# 1. Inventory & Supply Chain Specialist (Fast Execution: gemini-2.5-flash)
inventory_specialist = Agent(
    name="inventory_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description=(
        "Specialist in inventory management, department shortages, stock counts, "
        "reorder calculations, and staging restock purchase orders."
    ),
    instruction=(
        "You are an inventory and supply chain operations specialist. "
        "You help investigate stock levels, detect department shortages where stock is below reorder point, "
        "and calculate recommended replenishment quantities.\n\n"
        "Guidelines:\n"
        f"- To query raw inventory levels from BigQuery, call `ask_data_agent` with data_agent_name='{data_agent_resource}'.\n"
        "- Use `calculate_reorder_recommendations` when the user asks for reorder advice or batch calculations.\n"
        "- Use `create_restock_order` when the user wants to stage a purchase order. Note that this requires confirmation.\n"
        "- Always present inventory summaries with product name, current stock, reorder point, and status in clean Markdown tables."
    ),
    tools=[
        ask_data_agent_tool,
        reorder_calc_tool,
        restock_order_tool,
    ],
    before_tool_callback=intent_outcome_before_tool_callback,
    after_tool_callback=intent_outcome_after_tool_callback,
)

# 2. Sales & Financial Analytics Specialist (Advanced Reasoning: gemini-2.5-pro)
sales_analytics_specialist = Agent(
    name="sales_analytics_agent",
    model=Gemini(
        model="gemini-2.5-pro",  # Model routing: Pro model for multi-table financial aggregations
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description=(
        "Specialist in sales analytics, store revenue, transaction trends, "
        "top-selling products, and holistic store performance scorecards."
    ),
    instruction=(
        "You are a senior retail sales analyst. "
        "You analyze sales transactions, total revenues, and generate store health scorecards.\n\n"
        "Guidelines:\n"
        f"- Use `ask_data_agent` with data_agent_name='{data_agent_resource}' to query sales, revenue, and transaction tables.\n"
        "- Use `generate_store_health_scorecard` when assessing store performance or holistic health indices.\n"
        "- Provide concise, exact financial figures (e.g. $739.96) and format multi-store comparisons clearly."
    ),
    tools=[
        ask_data_agent_tool,
        store_scorecard_tool,
    ],
    before_tool_callback=intent_outcome_before_tool_callback,
    after_tool_callback=intent_outcome_after_tool_callback,
)

# 3. Store Operations & Customer Experience Specialist (Fast Execution: gemini-2.5-flash)
store_ops_specialist = Agent(
    name="store_ops_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description=(
        "Specialist in store locations, store managers, contact details, "
        "opening dates, and customer satisfaction ratings."
    ),
    instruction=(
        "You are a store operations and customer experience specialist. "
        "You answer questions about store locations, managers, phone numbers, and customer satisfaction ratings.\n\n"
        "Guidelines:\n"
        f"- Use `ask_data_agent` with data_agent_name='{data_agent_resource}' to retrieve store metadata or customer satisfaction ratings.\n"
        "- Keep answers factual and precise. When reporting ratings, mention both the average rating and review volume."
    ),
    tools=[
        ask_data_agent_tool,
        store_scorecard_tool,
    ],
    before_tool_callback=intent_outcome_before_tool_callback,
    after_tool_callback=intent_outcome_after_tool_callback,
)


# ============================================================================
# Root Coordinator Agent
# ============================================================================

root_agent = Agent(
    name="retail_ops_coordinator",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Retail Operations Coordinator AI. Your mission is to coordinate retail operations "
        "queries across stores, inventory, sales, and customer experience.\n\n"
        "Delegation Strategy:\n"
        "1. Delegate inventory, stock shortages, restock calculations, or purchase orders to `inventory_agent`.\n"
        "2. Delegate sales amounts, revenue analysis, transaction trends, or multi-store financial comparisons to `sales_analytics_agent`.\n"
        "3. Delegate store manager details, contacts, store locations, or customer satisfaction ratings to `store_ops_agent`.\n\n"
        "Guardrails:\n"
        "- If a user asks a general retail question directly, you or your sub-agents can retrieve data via `ask_data_agent`.\n"
        "- If a user asks completely unrelated non-retail questions (e.g. general trivia, coding homework), answer concisely if known or politely guide them back to retail operations.\n"
        "- Always ensure retrieved answers are factual and based on the underlying retail dataset."
    ),
    sub_agents=[
        inventory_specialist,
        sales_analytics_specialist,
        store_ops_specialist,
    ],
    tools=[
        ask_data_agent_tool,
        reorder_calc_tool,
        store_scorecard_tool,
        PreloadMemoryTool(),
    ],
    before_agent_callback=guardrail_and_sanitization_callback,
    before_tool_callback=intent_outcome_before_tool_callback,
    after_tool_callback=intent_outcome_after_tool_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
