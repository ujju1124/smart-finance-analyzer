"""Merchant categorization service.

Two-tier categorization system:
1. Pattern-based matching (fast, no LLM): Uses keyword patterns from merchant_patterns.json
2. LLM fallback (only for unknown): Batch processes up to 10 merchants per API call

The merchant→category map is loaded from merchant_categories.json at import
into module-level _MERCHANT_CACHE (keys are normalized lowercase strings).
Pattern-based rules are loaded from merchant_patterns.json.
All LLM calls are constrained to the VALID_CATEGORIES set.
"""

import json
import os
import re
from pathlib import Path

from groq import Groq, RateLimitError

try:
    from services.llm_structurer import _call_with_retry, _get_client, GroqAPIError
except ImportError:
    from backend.services.llm_structurer import _call_with_retry, _get_client, GroqAPIError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CATEGORIES = frozenset({
    "Groceries",
    "Food & Dining",
    "Transport",
    "Utilities",
    "Shopping",
    "Digital Wallet & Transfers",
    "Entertainment",
    "Healthcare",
    "Education",
    "Rent & Housing",
    "Cash Withdrawal",
    "Bank Fees & Charges",
    "Income & Salary",
    "Bank Transfer",
    "Investment",
    "Personal Care",
    "Housing",
    "Uncategorized",
})

_CATEGORIES_STR = ", ".join(sorted(VALID_CATEGORIES))

CATEGORIES_FILE = Path(__file__).parent.parent / "data" / "merchant_categories.json"
PATTERNS_FILE = Path(__file__).parent.parent / "data" / "merchant_patterns.json"

# ---------------------------------------------------------------------------
# Module-level cache — loaded once at import
# ---------------------------------------------------------------------------

def _load_cache(path: Path) -> dict[str, str]:
    """Load merchant_map from the JSON file; return empty dict if file is missing."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Normalize keys to lowercase so lookups are always case-insensitive.
    return {k.lower(): v for k, v in data.get("merchant_map", {}).items()}


def _load_patterns(path: Path) -> list[dict]:
    """Load keyword patterns from JSON file."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("patterns", [])


_MERCHANT_CACHE: dict[str, str] = _load_cache(CATEGORIES_FILE)
_PATTERNS: list[dict] = _load_patterns(PATTERNS_FILE)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_groq_client() -> Groq:
    """Return a Groq client using the rotation system from llm_structurer."""
    return _get_client()


def _write_back(new_mappings: dict[str, str], path: Path) -> None:
    """Persist new merchant→category pairs into the JSON file and update cache.

    Reads the current file (to preserve existing entries), merges in
    new_mappings (keys stored as-is — callers pass normalized lowercase keys),
    and writes back.
    """
    global _MERCHANT_CACHE  # noqa: PLW0603 — intentional module-level mutation

    # Load existing data (or start fresh).
    if path.exists():
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        data = {
            "version": "1.0",
            "categories": sorted(VALID_CATEGORIES),
            "merchant_map": {},
        }

    data.setdefault("merchant_map", {})
    data["merchant_map"].update(new_mappings)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    # Keep in-memory cache in sync.
    _MERCHANT_CACHE.update({k.lower(): v for k, v in new_mappings.items()})


# ---------------------------------------------------------------------------
# 4.1 — normalize_merchant
# ---------------------------------------------------------------------------

def normalize_merchant(merchant: str) -> str:
    """Lowercase, strip leading/trailing whitespace, collapse internal spaces.

    Idempotent: normalize(normalize(x)) == normalize(x) for all x.
    """
    if merchant is None:
        return ""
    return re.sub(r" +", " ", merchant.strip().lower())


# ---------------------------------------------------------------------------
# Pattern matching (Tier 1)
# ---------------------------------------------------------------------------

def match_by_patterns(description: str, merchant: str, direction: str = "") -> str | None:
    """Match transaction to category using keyword patterns.
    
    Args:
        description: Raw transaction description
        merchant: Normalized merchant name
        direction: Transaction direction ("credit" or "debit"), optional
        
    Returns:
        Category string if a pattern matches, None otherwise
    """
    # Combine description and merchant for comprehensive keyword search
    text = (description + " " + merchant).lower()
    
    for pattern in _PATTERNS:
        keywords = pattern.get("keywords", [])
        category = pattern.get("category")
        required_direction = pattern.get("direction")  # New: direction requirement
        
        # If pattern specifies direction, check if it matches
        if required_direction and direction and direction.lower() != required_direction.lower():
            continue  # Skip this pattern if direction doesn't match
        
        for keyword in keywords:
            if keyword.lower() in text:
                return category
    
    return None  # No pattern matched


# ---------------------------------------------------------------------------
# 4.3 — categorize_transaction
# ---------------------------------------------------------------------------

def categorize_transaction(
    merchant_normalized: str,
    description_raw: str = "",
    direction: str = "",
    *,
    _categories_file: Path | None = None,
) -> str:
    """Return the category for a single merchant using two-tier system.

    Steps:
    1. Normalize the input.
    2. Try pattern matching (Tier 1) - fast, no LLM, direction-aware
    3. Check _MERCHANT_CACHE.
    4. If found → return cached category.
    5. If not found → call Groq (llama-3.1-8b-instant) - Tier 2
    6. Validate; fall back to "Uncategorized" if LLM returns invalid category.
    7. Write new mapping back to JSON and update cache.
    8. Return category.
    
    Args:
        merchant_normalized: Normalized merchant name
        description_raw: Full transaction description for pattern matching
        direction: Transaction direction ("credit" or "debit") for direction-aware patterns

    The optional _categories_file parameter lets tests inject a tmp path
    without touching the real merchant_categories.json.
    """
    path = _categories_file if _categories_file is not None else CATEGORIES_FILE
    key = normalize_merchant(merchant_normalized)

    # TIER 1: Pattern matching (fast, no LLM needed, direction-aware)
    pattern_match = match_by_patterns(description_raw, key, direction)
    if pattern_match:
        # Write to cache for future lookups
        _write_back({key: pattern_match}, path)
        return pattern_match

    # Cache hit — skip LLM entirely.
    if key in _MERCHANT_CACHE:
        return _MERCHANT_CACHE[key]

    # TIER 2: LLM fallback (only for genuinely unknown merchants)
    prompt = (
        "Categorize this Nepali merchant/transaction into exactly one of these categories:\n"
        f"{_CATEGORIES_STR}\n\n"
        f"Merchant: {key}\n"
        f"Description: {description_raw}\n"
        f"Direction: {direction if direction else 'unknown'}\n"
        "Reply with ONLY the category name, nothing else."
    )

    client = _get_groq_client()

    def _api_call():
        return client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
        )

    try:
        response = _call_with_retry(_api_call)
    except GroqAPIError:
        raise
    except Exception as exc:
        raise GroqAPIError(f"Groq API call failed: {exc}") from exc

    # Handle case when response is None (all API keys exhausted)
    if response is None or not hasattr(response, 'choices') or not response.choices:
        # Return "Uncategorized" when rate limit is hit (graceful degradation)
        return "Uncategorized"

    raw_category = response.choices[0].message.content.strip()
    category = raw_category if raw_category in VALID_CATEGORIES else "Uncategorized"

    _write_back({key: category}, path)
    return category


# ---------------------------------------------------------------------------
# 4.6 — batch_categorize
# ---------------------------------------------------------------------------

def batch_categorize(
    merchants: list[str],
    *,
    _categories_file: Path | None = None,
) -> dict[str, str]:
    """Categorize up to 10 merchants in a single Groq API call.

    Already-cached merchants are resolved without an API call; only the
    remaining unknowns (up to 10) are sent to the LLM.

    Returns a dict {original_merchant: category} for every input merchant.

    The optional _categories_file parameter lets tests inject a tmp path.
    """
    path = _categories_file if _categories_file is not None else CATEGORIES_FILE
    result: dict[str, str] = {}
    unknown: list[str] = []

    for merchant in merchants:
        key = normalize_merchant(merchant)
        if key in _MERCHANT_CACHE:
            result[merchant] = _MERCHANT_CACHE[key]
        else:
            unknown.append(merchant)

    if not unknown:
        return result

    # Clamp to 10 unknowns per call (as per spec).
    batch = unknown[:10]
    merchant_list = "\n".join(normalize_merchant(m) for m in batch)

    prompt = (
        "Categorize each merchant below into exactly one of these categories:\n"
        "Groceries, Food & Dining, Transport, Utilities, Shopping, "
        "Digital Wallet & Transfers, Entertainment, Healthcare, Education, "
        "Rent & Housing, Cash Withdrawal,\nBank Fees & Charges, Income & Salary, "
        "Uncategorized\n\n"
        "Return a JSON object where each key is the merchant name and each value "
        "is the category.\n"
        f"Merchants:\n{merchant_list}"
    )

    client = _get_groq_client()

    def _api_call():
        return client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
        )

    try:
        response = _call_with_retry(_api_call)
    except GroqAPIError:
        raise
    except Exception as exc:
        raise GroqAPIError(f"Groq API call failed: {exc}") from exc

    # Handle case when response is None (all API keys exhausted)
    if response is None or not hasattr(response, 'choices') or not response.choices:
        # Return empty dict when rate limit is hit (graceful degradation)
        return {}

    raw_content = response.choices[0].message.content.strip()

    # Parse JSON from the LLM response; tolerate markdown code fences.
    json_text = re.sub(r"^```[a-z]*\n?", "", raw_content, flags=re.MULTILINE)
    json_text = re.sub(r"```$", "", json_text.strip())

    try:
        llm_map: dict = json.loads(json_text)
    except (json.JSONDecodeError, TypeError):
        llm_map = {}

    new_mappings: dict[str, str] = {}
    for merchant in batch:
        key = normalize_merchant(merchant)
        raw_cat = llm_map.get(key) or llm_map.get(merchant, "")
        category = raw_cat if raw_cat in VALID_CATEGORIES else "Uncategorized"
        result[merchant] = category
        new_mappings[key] = category

    if new_mappings:
        _write_back(new_mappings, path)

    # Any merchants beyond the first 10 that weren't cached get "Uncategorized".
    for merchant in unknown[10:]:
        result[merchant] = "Uncategorized"

    return result
