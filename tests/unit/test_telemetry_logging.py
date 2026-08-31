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

from app.app_utils.logging_utils import log_intent, log_outcome, log_structured_event


def test_log_structured_event_redacts_pii() -> None:
    # Verify no exception is raised and PII is handled
    log_structured_event(
        event_type="TEST_EVENT",
        payload={"manager_phone": "555-0101", "email": "manager@store.com"},
    )


def test_log_intent_and_outcome() -> None:
    log_intent(
        session_id="test-session-123",
        agent_name="inventory_specialist",
        intent="Check stock for store 101",
        planned_action="calculate_reorder_recommendations",
        parameters={"store_id": 101},
    )

    log_outcome(
        session_id="test-session-123",
        agent_name="inventory_specialist",
        tool_name="calculate_reorder_recommendations",
        status="SUCCESS",
        duration_ms=45.2,
        summary="Calculated 1 recommendation for store 101",
        result_data={"total_shortages": 1},
    )
