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

from app.tools.custom_retail_tools import (
    calculate_reorder_recommendations,
    create_restock_order,
    generate_store_health_scorecard,
)


def test_calculate_reorder_recommendations_valid_store() -> None:
    result = calculate_reorder_recommendations(store_id=101)
    assert result["status"] == "success"
    assert result["store_id"] == 101
    assert "recommendations" in result
    assert len(result["recommendations"]) >= 1


def test_calculate_reorder_recommendations_invalid_store() -> None:
    result = calculate_reorder_recommendations(store_id=999)
    assert result["status"] == "error"
    assert "guidance" in result
    assert result["error_type"] == "StoreNotFound"


def test_generate_store_health_scorecard() -> None:
    result = generate_store_health_scorecard(store_id=101)
    assert result["status"] == "success"
    assert "composite_health_score" in result
    assert 0 <= result["composite_health_score"] <= 100
    assert result["city"] == "San Francisco"


def test_create_restock_order_staging() -> None:
    result = create_restock_order(
        store_id=101,
        product_name="Wireless Headphones",
        quantity=20,
        urgency="expedited",
    )
    assert result["status"] == "PENDING_CONFIRMATION"
    assert result["requires_human_approval"] is True
    assert result["order_id"].startswith("PO-101-")
    assert result["quantity"] == 20
