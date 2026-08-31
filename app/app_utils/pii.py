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

import re
from typing import Any

# Regex patterns for PII detection
# Matches 7-digit (e.g. 555-0101) as well as 10/11 digit phone numbers (e.g. +1 555-555-0101, (555) 555-0101)
PHONE_REGEX = re.compile(r"(?:\+?1[-. ]?)?(?:\(?\d{3}\)?[-. ]?)?\b\d{3}[-. ]\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def sanitize_pii(text: str) -> str:
    """Redacts PII (phone numbers, emails, credit cards, SSNs) from text strings.

    Args:
        text: The raw input string potentially containing PII.

    Returns:
        Sanitized string with sensitive identifiers replaced with redaction tokens.
    """
    if not isinstance(text, str):
        return text

    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    sanitized = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", sanitized)
    sanitized = SSN_REGEX.sub("[REDACTED_SSN]", sanitized)
    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)
    return sanitized


def sanitize_pii_recursive(data: Any) -> Any:
    """Recursively traverses dictionaries, lists, and primitives to redact PII.

    Args:
        data: The input structure (dict, list, string, etc.).

    Returns:
        Data structure with all string fields sanitized of PII.
    """
    if isinstance(data, str):
        return sanitize_pii(data)
    elif isinstance(data, dict):
        return {k: sanitize_pii_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_pii_recursive(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_pii_recursive(item) for item in data)
    return data
