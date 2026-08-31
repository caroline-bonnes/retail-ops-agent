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

import os

import google.auth
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.data_agent import data_agent_tool
from google.adk.tools.data_agent.config import DataAgentToolConfig
from google.adk.tools.data_agent.credentials import DataAgentCredentialsConfig
from google.adk.tools.google_tool import GoogleTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

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


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends the session's events to Memory Bank for memory generation."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        import logging

        logging.warning(f"Failed to add session to memory bank: {e}")
    return None


data_agent_resource = (
    f"projects/{project_id}/locations/global/dataAgents/retail-ops-bq-agent"
)

root_agent = Agent(
    name="retail_ops_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a retail operations assistant. You help answer natural language questions "
        "about store performance, inventory levels, sales metrics, and manager details by "
        "using the Conversational Analytics Data Agent toolset. If the user asks about stores, "
        "sales, inventory, or customer satisfaction, use the ask_data_agent tool with "
        f"data_agent_name='{data_agent_resource}'. Always provide clear, summary answers "
        "based on the retrieved data. Keep answers factual and precise."
    ),
    tools=[
        list_accessible_data_agents_tool,
        get_data_agent_info_tool,
        ask_data_agent_tool,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
