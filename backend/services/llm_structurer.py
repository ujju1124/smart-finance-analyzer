"""LLM structuring service using Groq API with json_object mode.

Converts raw bank statement text extracted from PDFs into structured
transaction dicts conforming to the 9-field schema (source_bank is set
by the calling router, not here).

Uses model: llama-3.3-70b-versatile with response_format={"type":"json_object"}
Note: json_schema structured outputs are not supported by llama-3.3-70b-versatile
on Groq's free tier. We use json_object mode + a strict system prompt instead.

Rate limit handling: exponential backoff on HTTP 429 (5s → 10s → 20s),
max 3 retries, then raises GroqAPIError with a user-friendly message.
"""

import json
import os
import time
import uuid
from typing import Optional

from groq import Groq, RateLimitError


class GroqAPIError(Exception):
    """Raised on unrecoverable Groq API failures (including exhausted retries)."""
    pass


# Backoff delays in seconds for retry attempts 1, 2, 3.
_RETRY_DELAYS = [5, 10, 20]
_MAX_RETRIES = 3

# Global state for API key rotation
_CURRENT_KEY_INDEX = 0
_API_KEYS = []
_KEY_FAILURE_COUNT = {}
_USER_PROVIDED_KEY = None  # NEW: For user-provided API key from request header


def set_user_api_key(api_key: str | None):
    """Set user-provided API key for the current request.
    
    SECURITY NOTE: This key is only used for the duration of the request
    and is never persisted to disk, database, or logs. It exists only in
    memory for this request context.
    """
    global _USER_PROVIDED_KEY
    _USER_PROVIDED_KEY = api_key


def _load_api_keys():
    """Load all available Groq API keys from environment variables."""
    global _API_KEYS, _KEY_FAILURE_COUNT, _CURRENT_KEY_INDEX
    
    if _API_KEYS:  # Already loaded
        return
    
    # Try to load numbered keys first (GROQ_API_KEY_1, GROQ_API_KEY_2, etc.)
    keys = []
    for i in range(1, 11):  # Support up to 10 keys
        key = os.environ.get(f"GROQ_API_KEY_{i}")
        if key:
            keys.append(key)
    
    # Fallback to single key if no numbered keys found
    if not keys:
        key = os.environ.get("GROQ_API_KEY")
        if key:
            keys.append(key)
    
    if not keys:
        raise GroqAPIError(
            "No GROQ_API_KEY found in environment. "
            "Set GROQ_API_KEY or GROQ_API_KEY_1, GROQ_API_KEY_2, etc."
        )
    
    _API_KEYS = keys
    _KEY_FAILURE_COUNT = {i: 0 for i in range(len(keys))}
    # Start with the LAST key (most recently added, likely freshest)
    _CURRENT_KEY_INDEX = len(keys) - 1
    
    print(f"✓ Loaded {len(_API_KEYS)} Groq API key(s) for rotation (starting with key {_CURRENT_KEY_INDEX + 1})")


def _get_next_api_key() -> str:
    """Get the next API key in rotation, skipping recently failed keys.
    
    If a user-provided API key is set (via request header), use that instead.
    """
    global _CURRENT_KEY_INDEX
    
    # PRIORITY 1: User-provided API key (from X-Groq-API-Key header)
    if _USER_PROVIDED_KEY:
        return _USER_PROVIDED_KEY
    
    # PRIORITY 2: Environment-configured keys with rotation
    _load_api_keys()
    
    if len(_API_KEYS) == 1:
        return _API_KEYS[0]
    
    # Find the next key with lowest failure count
    start_index = _CURRENT_KEY_INDEX
    best_index = start_index
    min_failures = _KEY_FAILURE_COUNT[start_index]
    
    for offset in range(1, len(_API_KEYS)):
        index = (start_index + offset) % len(_API_KEYS)
        if _KEY_FAILURE_COUNT[index] < min_failures:
            best_index = index
            min_failures = _KEY_FAILURE_COUNT[index]
    
    _CURRENT_KEY_INDEX = best_index
    return _API_KEYS[best_index]


def _mark_key_failed():
    """Mark current key as failed (rate limited)."""
    global _CURRENT_KEY_INDEX
    _KEY_FAILURE_COUNT[_CURRENT_KEY_INDEX] += 1
    print(f"⚠ API key {_CURRENT_KEY_INDEX + 1} hit rate limit. Rotating to next key...")


def _rotate_to_next_key():
    """Rotate to the next API key."""
    global _CURRENT_KEY_INDEX
    
    if len(_API_KEYS) <= 1:
        return False  # No other keys available
    
    old_index = _CURRENT_KEY_INDEX
    _CURRENT_KEY_INDEX = (old_index + 1) % len(_API_KEYS)
    
    print(f"→ Rotated from key {old_index + 1} to key {_CURRENT_KEY_INDEX + 1}")
    return True


def _call_with_retry(fn, max_retries: int = _MAX_RETRIES):
    """Call fn() and retry on RateLimitError with exponential backoff and key rotation.
    
    Also adds a small delay after successful calls to prevent TPM (tokens-per-minute) burst.
    """
    for attempt in range(max_retries + 1):
        try:
            result = fn()
            
            # Add small delay after successful call to prevent TPM burst
            # Groq free tier has 6,000 TPM limit for llama-3.3-70b-versatile
            # This prevents hitting rate limits when processing multiple pages/merchants
            time.sleep(0.5)  # 500ms delay between calls
            
            return result
        except RateLimitError as e:
            _mark_key_failed()
            
            # Try rotating to next key
            if _rotate_to_next_key():
                print(f"  Retrying with different API key...")
                continue  # Retry immediately with new key
            
            # No more keys available, use backoff
            if attempt < max_retries:
                delay = _RETRY_DELAYS[attempt]
                print(f"  All keys exhausted. Waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(delay)
            else:
                # Reset failure counts for next request
                for key_idx in _KEY_FAILURE_COUNT:
                    _KEY_FAILURE_COUNT[key_idx] = 0
                
                raise GroqAPIError(
                    f"Rate limit reached on all {len(_API_KEYS)} API key(s). "
                    "Please try again in a few minutes."
                )


def _get_client() -> Groq:
    """Initialise and return a Groq client with current API key."""
    api_key = _get_next_api_key()
    return Groq(api_key=api_key)


_SYSTEM_PROMPT = """You are a bank statement parser. Extract ONLY the transaction rows visible on this specific page.

CRITICAL INSTRUCTIONS:
- Extract ONLY transactions shown on this page
- Skip header rows, footer rows, account summary sections, opening balance, and closing balance
- If this page has no transaction rows, return an empty array: {"transactions": []}
- Do NOT invent or duplicate transactions from other pages

Each transaction MUST have exactly these fields:
- date: ISO 8601 date string YYYY-MM-DD
- time: HH:MM 24-hour format (zero-padded, e.g. "09:30"), or null if not available
- description_raw: exact transaction text from the statement
- merchant_normalized: extracted business/merchant name (see extraction rules below)
- amount: positive number as a JSON number (always positive regardless of debit/credit)
- direction: exactly "debit" for money going out (Withdraw column), "credit" for money coming in (Deposit column)
- balance_after: running balance after this transaction as a number, or null

MERCHANT EXTRACTION RULES (merchant_normalized field):
Common Nepali payment description patterns:
- "MPAY FPQR,<code>,<MERCHANT NAME>,<note>" → extract MERCHANT NAME
- "eSewa Load <phone>" → merchant = "eSewa"
- "FON:IBFT:<code>:<bank>" → merchant = "Bank Transfer"
- "C-ASBA Fee - IPO - <company>" → merchant = company name
- "ACCOUNTFT:<name>" → extract the name
- "MPAY <code>,MOB,<ref>" → merchant = "Mobile Payment"
- If description contains clear business name (cafe, restaurant, shop, etc.) → extract that name
- If you cannot identify a clear merchant, use the payment method (e.g., "eSewa", "MPAY", "IBFT", "Bank Transfer")
- NEVER use "Unknown" as merchant_normalized - always extract something meaningful

AMOUNT PARSING RULES - ABSOLUTELY CRITICAL - READ CAREFULLY:
YOU MUST PRESERVE EVERY SINGLE DIGIT IN THE AMOUNT. DO NOT DROP ANY ZEROS OR DIGITS.

STEP 1: Find the exact amount string in the statement (e.g., "13,000.00" or "3,890.00" or "14,720.00")
STEP 2: Remove ALL commas from the amount string
STEP 3: Convert to a number PRESERVING ALL DIGITS

CORRECT EXAMPLES FROM REAL STATEMENTS:
  PDF shows "13,000.00" → Remove commas → "13000.00" → Output: 13000.00 ✅
  PDF shows "3,890.00" → Remove commas → "3890.00" → Output: 3890.00 ✅
  PDF shows "6,900.00" → Remove commas → "6900.00" → Output: 6900.00 ✅
  PDF shows "1,400.00" → Remove commas → "1400.00" → Output: 1400.00 ✅
  PDF shows "2,000.00" → Remove commas → "2000.00" → Output: 2000.00 ✅
  PDF shows "14,720.00" → Remove commas → "14720.00" → Output: 14720.00 ✅
  PDF shows "105,000.00" → Remove commas → "105000.00" → Output: 105000.00 ✅
  PDF shows "210.00" → No commas → "210.00" → Output: 210.00 ✅
  PDF shows "50.00" → No commas → "50.00" → Output: 50.00 ✅
  PDF shows "1,500.00" → Remove commas → "1500.00" → Output: 1500.00 ✅

WRONG EXAMPLES (NEVER DO THIS):
  PDF shows "13,000.00" → Output: 1300.00 ❌ WRONG - missing digit
  PDF shows "3,890.00" → Output: 389.00 ❌ WRONG - dropped zero
  PDF shows "2,000.00" → Output: 200.00 ❌ WRONG - dropped zero
  PDF shows "14,720.00" → Output: 1472.00 ❌ WRONG - dropped zero
  PDF shows "105,000.00" → Output: 10500.00 ❌ WRONG - dropped zero
  
VERIFICATION STEP: After extracting an amount, COUNT THE DIGITS:
- If PDF shows "13,000.00", you should have 5 digits before decimal (1-3-0-0-0)
- If PDF shows "3,890.00", you should have 4 digits before decimal (3-8-9-0)
- If PDF shows "14,720.00", you should have 5 digits before decimal (1-4-7-2-0)
- If your extracted number has fewer digits than the PDF, YOU MADE A MISTAKE - GO BACK AND FIX IT

DIRECTION RULES - CRITICAL:
For Kumari Bank / Nabil Bank statements (two-column format):
- If the amount appears in the "Debit" or "Withdraw" column → direction = "debit" (money OUT)
- If the amount appears in the "Credit" or "Deposit" column → direction = "credit" (money IN)
- A dash "-" symbol in a column means that column is EMPTY for that transaction
- Examples:
  * "Debit: 5,000  Credit: -" → direction = "debit" (money out)
  * "Debit: -  Credit: 105,000" → direction = "credit" (money in)

Return ONLY valid JSON, no markdown, no explanation:
{"transactions": [{"date": "2024-01-15", "time": "10:30", "description_raw": "Payment for laptop", "merchant_normalized": "Electronics Store", "amount": 100010.00, "direction": "debit", "balance_after": 45600.25}]}"""


def _parse_single_page(page_text: str, page_num: int, total_pages: int) -> list[dict]:
    """Parse transactions from a single page of text.
    
    Args:
        page_text: Raw text extracted from one page
        page_num: Current page number (1-indexed)
        total_pages: Total number of pages in the document
        
    Returns:
        List of transaction dicts from this page (may be empty)
        
    Raises:
        GroqAPIError: On API failure or rate limit exhaustion
    """
    client = _get_client()
    
    user_content = (
        f"This is page {page_num} of {total_pages} from a bank statement. "
        f"Extract ONLY the transaction rows from this page:\n\n{page_text}"
    )

    def _api_call():
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,  # Limit to prevent runaway generation
            temperature=0.1,  # Low temperature for consistent extraction
        )
        return response

    try:
        response = _call_with_retry(_api_call)
    except GroqAPIError:
        raise
    except Exception as exc:
        raise GroqAPIError(f"Groq API call failed on page {page_num}: {exc}") from exc

    # Handle case when response is None (all API keys exhausted)
    if response is None or not hasattr(response, 'choices') or not response.choices:
        raise GroqAPIError(
            "Rate limit reached on all API keys. Please try again in a few minutes."
        )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GroqAPIError(f"LLM returned invalid JSON for page {page_num}: {exc}") from exc

    transactions = parsed.get("transactions", [])
    
    # ALWAYS generate fresh UUIDs in Python - don't trust LLM to generate unique IDs
    for txn in transactions:
        txn["transaction_id"] = str(uuid.uuid4())
    
    return transactions


def _deduplicate(transactions: list[dict]) -> list[dict]:
    """Remove duplicate transactions based on (date, amount, direction, FULL description).
    
    Uses the complete description_raw field to avoid incorrectly removing valid
    transactions that have the same amount on the same day but different details
    (e.g., two eSewa loads of identical amount to different phone numbers).
    
    Args:
        transactions: List of transaction dicts, possibly with duplicates across pages
        
    Returns:
        Deduplicated list of transactions
    """
    seen = set()
    unique = []
    
    for txn in transactions:
        # Create a fingerprint using FULL description (not truncated)
        # This ensures two identical-amount transactions on same day are NOT deduped
        # unless their descriptions are also identical
        fingerprint = (
            txn.get("date"),
            txn.get("amount"),
            txn.get("direction"),
            txn.get("description_raw", "")  # Full description, not [:30]
        )
        
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(txn)
    
    return unique


def structure_transactions(pages: list[str]) -> list[dict]:
    """Convert raw bank statement pages to structured transaction dicts.

    Processes each page separately with Groq API to avoid output truncation,
    then combines and deduplicates the results.

    Args:
        pages: List of text strings, one per page of the PDF

    Raises:
        GroqAPIError: On API failure, rate limit exhaustion, or invalid JSON.
    """
    all_transactions = []
    total_pages = len(pages)
    
    for i, page_text in enumerate(pages):
        page_num = i + 1
        page_transactions = _parse_single_page(page_text, page_num, total_pages)
        all_transactions.extend(page_transactions)
    
    # Deduplicate in case transactions span page boundaries
    unique_transactions = _deduplicate(all_transactions)
    
    # POST-PROCESSING: Fix comma-parsing errors using balance validation
    for i, txn in enumerate(unique_transactions):
        if txn.get("balance_after") is not None and i > 0:
            prev_balance = unique_transactions[i-1].get("balance_after")
            if prev_balance is not None:
                current_balance = txn["balance_after"]
                amount = txn["amount"]
                direction = txn["direction"]
                
                # Calculate expected balance
                if direction == "debit":
                    expected_balance = prev_balance - amount
                else:  # credit
                    expected_balance = prev_balance + amount
                
                # If mismatch is significant (more than 1 NPR), try multiplying by 10
                if abs(expected_balance - current_balance) > 1:
                    # Try amount * 10 (common error: 10,010 parsed as 1,001)
                    test_amount = amount * 10
                    if direction == "debit":
                        test_balance = prev_balance - test_amount
                    else:
                        test_balance = prev_balance + test_amount
                    
                    if abs(test_balance - current_balance) < abs(expected_balance - current_balance):
                        txn["amount"] = test_amount
                        continue
                    
                    # Try amount / 10 (opposite error)
                    test_amount = amount / 10
                    if direction == "debit":
                        test_balance = prev_balance - test_amount
                    else:
                        test_balance = prev_balance + test_amount
                    
                    if abs(test_balance - current_balance) < abs(expected_balance - current_balance):
                        txn["amount"] = test_amount

    return unique_transactions
