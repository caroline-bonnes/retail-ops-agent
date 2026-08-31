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

from app.app_utils.pii import sanitize_pii, sanitize_pii_recursive


def test_sanitize_pii_phone_and_email() -> None:
    text = "Call manager Alice Smith at 555-0101 or email alice@retailstore.com for store 101."
    sanitized = sanitize_pii(text)
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "555-0101" not in sanitized
    assert "alice@retailstore.com" not in sanitized


def test_sanitize_pii_credit_card_and_ssn() -> None:
    text = "Customer card 4111-2222-3333-4444 and ssn 123-45-6789."
    sanitized = sanitize_pii(text)
    assert "[REDACTED_CARD]" in sanitized
    assert "[REDACTED_SSN]" in sanitized
    assert "4111-2222-3333-4444" not in sanitized
    assert "123-45-6789" not in sanitized


def test_sanitize_pii_recursive_dict() -> None:
    data = {
        "user": {
            "name": "Bob Jones",
            "contact": "555-0102",
            "email": "bob@example.com",
        },
        "order": {
            "card": "1234-5678-9012-3456",
            "quantity": 5,
        },
    }
    sanitized = sanitize_pii_recursive(data)
    assert sanitized["user"]["contact"] == "[REDACTED_PHONE]"
    assert sanitized["user"]["email"] == "[REDACTED_EMAIL]"
    assert sanitized["order"]["card"] == "[REDACTED_CARD]"
    assert sanitized["order"]["quantity"] == 5
