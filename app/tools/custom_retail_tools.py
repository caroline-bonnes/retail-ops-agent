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

import datetime
import logging
import uuid
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas for Explicit Tool Definitions
# ============================================================================


class RestockRecommendationInput(BaseModel):
    store_id: int = Field(
        ...,
        description="The unique numerical identifier of the retail store (e.g. 101, 102, 103, 104, 105).",
        ge=100,
        le=999,
    )
    department: str = Field(
        default="",
        description="Optional retail department name filter (e.g. 'Electronics', 'Clothing', 'Home & Kitchen').",
    )


class RestockOrderInput(BaseModel):
    store_id: int = Field(
        ...,
        description="The store ID where the restock shipment will be delivered.",
        ge=100,
        le=999,
    )
    product_name: str = Field(
        ...,
        description="The exact name of the product to order (e.g. 'Smart TV 55', 'Wireless Headphones').",
        min_length=2,
    )
    quantity: int = Field(
        ...,
        description="Number of units to reorder. Must be at least 1.",
        gt=0,
        le=5000,
    )
    urgency: Literal["standard", "expedited", "critical"] = Field(
        default="standard",
        description="Delivery urgency level: 'standard' (3-5 days), 'expedited' (1-2 days), or 'critical' (same-day).",
    )


class StoreScorecardInput(BaseModel):
    store_id: int = Field(
        ...,
        description="The store ID for which to generate the health scorecard.",
        ge=100,
        le=999,
    )


class InventoryShortageItem(TypedDict):
    product_name: str
    department: str
    stock_count: int
    reorder_point: int
    unit_cost: float


class StoreProfile(TypedDict):
    city: str
    manager: str
    rating: float
    open_shortages: int
    revenue: float


# ============================================================================
# Custom Tool Implementations with Guided Error Handling
# ============================================================================

VALID_STORE_IDS: set[int] = {101, 102, 103, 104, 105}


def calculate_reorder_recommendations(
    store_id: int, department: str = ""
) -> dict[str, Any]:
    """Calculates automated restock recommendations based on stock counts and reorder thresholds.

    Evaluates inventory health for a store, identifying items that have fallen below
    their target reorder thresholds, and computes suggested reorder batch sizes.

    Args:
        store_id: The numerical ID of the store (e.g. 101 to 105).
        department: Optional department name to filter results (e.g. 'Electronics').

    Returns:
        A dictionary with 'status', 'store_id', 'items_needing_reorder', and 'recommendations'.
    """
    try:
        # Validate input schema
        validated_input = RestockRecommendationInput(
            store_id=store_id, department=department
        )
    except Exception as e:
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": f"Invalid input parameters: {e}",
            "guidance": "Please provide a valid 3-digit store ID between 101 and 105.",
        }

    if validated_input.store_id not in VALID_STORE_IDS:
        return {
            "status": "error",
            "error_type": "StoreNotFound",
            "message": f"Store ID {store_id} is not recognized in active retail network.",
            "valid_stores": sorted(VALID_STORE_IDS),
            "guidance": f"Valid store IDs are {sorted(VALID_STORE_IDS)}. Please verify the store number.",
        }

    # Department and baseline product data for replenishment calculation
    mock_shortages: dict[int, list[InventoryShortageItem]] = {
        101: [
            {
                "product_name": "Wireless Headphones",
                "department": "Electronics",
                "stock_count": 8,
                "reorder_point": 15,
                "unit_cost": 89.99,
            },
        ],
        103: [
            {
                "product_name": "Smart TV 55",
                "department": "Electronics",
                "stock_count": 3,
                "reorder_point": 10,
                "unit_cost": 499.99,
            },
            {
                "product_name": "Air Fryer XL",
                "department": "Home & Kitchen",
                "stock_count": 2,
                "reorder_point": 5,
                "unit_cost": 129.99,
            },
        ],
        105: [
            {
                "product_name": "Smart TV 55",
                "department": "Electronics",
                "stock_count": 5,
                "reorder_point": 10,
                "unit_cost": 499.99,
            },
            {
                "product_name": "Winter Jacket",
                "department": "Clothing",
                "stock_count": 4,
                "reorder_point": 15,
                "unit_cost": 79.99,
            },
        ],
    }

    raw_items = mock_shortages.get(store_id, [])
    dept_filter = validated_input.department.strip().lower()
    if dept_filter:
        raw_items = [i for i in raw_items if dept_filter in i["department"].lower()]

    recommendations: list[dict[str, Any]] = []
    for item in raw_items:
        reorder_pt: int = item["reorder_point"]
        stock_cnt: int = item["stock_count"]
        unit_price: float = item["unit_cost"]

        recommended_quantity: int = (reorder_pt * 2) - stock_cnt
        estimated_cost: float = round(float(recommended_quantity) * unit_price, 2)
        priority = "HIGH" if stock_cnt <= (reorder_pt // 2) else "MEDIUM"

        recommendations.append(
            {
                "product_name": item["product_name"],
                "department": item["department"],
                "current_stock": stock_cnt,
                "reorder_point": reorder_pt,
                "recommended_order_quantity": recommended_quantity,
                "estimated_order_cost": estimated_cost,
                "priority": priority,
            }
        )

    return {
        "status": "success",
        "store_id": store_id,
        "department_filter": department or "ALL",
        "total_shortages": len(recommendations),
        "recommendations": recommendations,
        "summary": (
            f"Found {len(recommendations)} items needing replenishment for Store {store_id}."
            if recommendations
            else f"Inventory is healthy for Store {store_id}; no items below reorder threshold."
        ),
    }


def generate_store_health_scorecard(store_id: int) -> dict[str, Any]:
    """Generates a multi-dimensional operational scorecard for a store.

    Combines customer satisfaction ratings, inventory replenishment health,
    and revenue status into an overall health index score (0-100).

    Args:
        store_id: The numerical ID of the store (e.g. 101 to 105).

    Returns:
        A dictionary containing the health score, operational status, and metric breakdowns.
    """
    if store_id not in VALID_STORE_IDS:
        return {
            "status": "error",
            "message": f"Store {store_id} does not exist.",
            "guidance": f"Please choose from available stores: {sorted(VALID_STORE_IDS)}.",
        }

    # Store baseline metrics
    store_profiles: dict[int, StoreProfile] = {
        101: {
            "city": "San Francisco",
            "manager": "Alice Smith",
            "rating": 4.7,
            "open_shortages": 1,
            "revenue": 739.96,
        },
        102: {
            "city": "New York",
            "manager": "Bob Jones",
            "rating": 4.2,
            "open_shortages": 0,
            "revenue": 499.99,
        },
        103: {
            "city": "Los Angeles",
            "manager": "Charlie Brown",
            "rating": 3.9,
            "open_shortages": 2,
            "revenue": 129.99,
        },
        104: {
            "city": "Chicago",
            "manager": "Diana Prince",
            "rating": 4.5,
            "open_shortages": 0,
            "revenue": 239.97,
        },
        105: {
            "city": "Seattle",
            "manager": "Evan Wright",
            "rating": 4.7,
            "open_shortages": 2,
            "revenue": 999.98,
        },
    }

    profile = store_profiles[store_id]

    # Calculate health score: 40% CSAT + 30% Stock health + 30% Sales strength
    csat_score: float = (profile["rating"] / 5.0) * 40.0
    stock_score: float = (
        max(0.0, (1.0 - (float(profile["open_shortages"]) * 0.35))) * 30.0
    )
    revenue_score: float = min(30.0, (profile["revenue"] / 1000.0) * 30.0)
    composite_health_score: float = round(csat_score + stock_score + revenue_score, 1)

    if composite_health_score >= 85:
        tier = "EXCELLENT"
    elif composite_health_score >= 70:
        tier = "GOOD"
    elif composite_health_score >= 50:
        tier = "ATTENTION_REQUIRED"
    else:
        tier = "CRITICAL"

    return {
        "status": "success",
        "store_id": store_id,
        "city": profile["city"],
        "manager": profile["manager"],
        "composite_health_score": composite_health_score,
        "health_tier": tier,
        "metrics_breakdown": {
            "customer_satisfaction_rating": profile["rating"],
            "open_inventory_shortages": profile["open_shortages"],
            "recent_revenue": profile["revenue"],
        },
        "recommendations": (
            "Store operating smoothly."
            if profile["open_shortages"] == 0
            else f"Review {profile['open_shortages']} inventory shortages to prevent sales loss."
        ),
    }


def create_restock_order(
    store_id: int,
    product_name: str,
    quantity: int,
    urgency: str = "standard",
) -> dict[str, Any]:
    """Stages a purchase replenishment order for retail restocking.

    Requires human confirmation before final transmission to supplier.

    Args:
        store_id: Numerical ID of the destination store.
        product_name: Name of product to order.
        quantity: Units to order.
        urgency: Urgency level ('standard', 'expedited', 'critical').

    Returns:
        Order staging confirmation with order reference ID.
    """
    try:
        urgency_typed: Literal["standard", "expedited", "critical"] = "standard"
        if urgency in ("standard", "expedited", "critical"):
            urgency_typed = urgency  # type: ignore[assignment]

        validated = RestockOrderInput(
            store_id=store_id,
            product_name=product_name,
            quantity=quantity,
            urgency=urgency_typed,
        )
    except Exception as e:
        return {
            "status": "error",
            "message": f"Order parameters invalid: {e}",
            "guidance": "Please provide a valid store ID, product name, and positive quantity.",
        }

    order_id = f"PO-{store_id}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    return {
        "status": "PENDING_CONFIRMATION",
        "order_id": order_id,
        "store_id": validated.store_id,
        "product_name": validated.product_name,
        "quantity": validated.quantity,
        "urgency": validated.urgency,
        "created_at": timestamp,
        "requires_human_approval": True,
        "message": (
            f"Restock Purchase Order {order_id} staged for Store {validated.store_id}: "
            f"{validated.quantity} units of '{validated.product_name}' ({validated.urgency} delivery). "
            "Awaiting final human confirmation to dispatch."
        ),
    }
