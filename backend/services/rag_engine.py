"""RAG (Retrieval-Augmented Generation) engine for conversational chat.

Uses ChromaDB with the default local embedding function (sentence-transformers
all-MiniLM-L6-v2) to embed transaction documents and analytics summaries.
Retrieves relevant context for user queries and calls Groq API to generate
grounded responses.

No Groq embeddings are used — only ChromaDB's built-in local embeddings.
"""

import os
import re
from datetime import datetime

import chromadb
import pandas as pd
from chromadb.utils import embedding_functions

try:
    from services.llm_structurer import GroqAPIError, _call_with_retry, _get_client
    from services.pattern_analytics import (
        compute_category_breakdown,
        compute_day_of_week_pattern,
        compute_monthly_trend,
        detect_anomalies,
    )
    from db import get_transactions
except ImportError:
    from backend.services.llm_structurer import GroqAPIError, _call_with_retry, _get_client
    from backend.services.pattern_analytics import (
        compute_category_breakdown,
        compute_day_of_week_pattern,
        compute_monthly_trend,
        detect_anomalies,
    )
    from backend.db import get_transactions

# ---------------------------------------------------------------------------
# Module-level ChromaDB state — ephemeral in-memory client
# ---------------------------------------------------------------------------

_chroma_client = None  # lazy-initialized to avoid blocking startup
_embedding_fn = None
_collection = None  # set by initialize_chromadb on first call

COLLECTION_NAME = "nepali_finance_transactions"


def _get_chroma_client():
    """Lazy-initialize ChromaDB client to avoid blocking app startup."""
    global _chroma_client, _embedding_fn
    if _chroma_client is None:
        _chroma_client = chromadb.Client()  # in-memory, no persistence needed
        _embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    return _chroma_client

# ---------------------------------------------------------------------------
# Financial-advice detection keywords (requirement 19.4)
# ---------------------------------------------------------------------------

_FINANCIAL_ADVICE_KEYWORDS = {
    "invest",
    "investment",
    "should i",
    "recommend",
    "advice",
    "tax",
    "budget",
    "predict",
    "forecast",
    "portfolio",
    "stocks",
    "savings advice",
}

# System prompt for RAG chat — strictly grounded in retrieved data
_RAG_SYSTEM_PROMPT = (
    "You are a personal finance assistant that ONLY answers questions about "
    "the user's transaction data. "
    "Answer based strictly on the provided transaction context. "
    "Do not provide financial advice, investment recommendations, or tax strategies. "
    "If the context doesn't contain enough information, say so clearly. "
    "Be specific and cite amounts and dates when available."
)


def initialize_chromadb(transactions: list[dict]) -> None:
    """Embed transactions and analytics summaries into ChromaDB.

    Resets the collection on every call so it always reflects the latest
    loaded dataset (e.g. after uploading a new statement or reloading
    sample data).

    Documents embedded:
    - One document per transaction: "{description_raw} {merchant_normalized}"
      with metadata {date, amount, category, direction}
    - Four analytics-summary documents (day-of-week, monthly-trend,
      category-breakdown, anomalies) prefixed with "analytics_summary:"

    Uses ChromaDB's default local embedding function
    (sentence-transformers all-MiniLM-L6-v2).  No Groq / external API
    calls are made here.

    Requirements: 12.1, 12.2
    """
    global _collection

    # Initialize client if needed
    client = _get_chroma_client()

    # Drop existing collection so we start clean each time
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # collection may not exist on first run

    _collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_fn,
    )

    # ------------------------------------------------------------------
    # 1. Add individual transaction documents
    # ------------------------------------------------------------------
    docs, ids, metas = [], [], []
    for i, txn in enumerate(transactions):
        description = txn.get("description_raw", "")
        merchant = txn.get("merchant_normalized", "")
        doc_text = f"{description} {merchant}".strip()

        docs.append(doc_text)
        ids.append(f"txn_{i}")
        metas.append(
            {
                "date": str(txn.get("date", "")),
                "amount": float(txn.get("amount", 0)),
                "category": str(txn.get("category", "")),
                "direction": str(txn.get("direction", "")),
            }
        )

    if docs:
        _collection.add(documents=docs, ids=ids, metadatas=metas)

    # ------------------------------------------------------------------
    # 2. Add analytics-summary documents
    # ------------------------------------------------------------------
    if transactions:
        df = pd.DataFrame(transactions)

        summaries = {
            "day-of-week": compute_day_of_week_pattern(df),
            "monthly-trend": compute_monthly_trend(df),
            "category-breakdown": compute_category_breakdown(df),
            "anomalies": detect_anomalies(df),
        }

        for pattern_type, data in summaries.items():
            _collection.add(
                documents=[f"analytics_summary: {pattern_type} {data}"],
                ids=[f"analytics_{pattern_type}"],
                metadatas=[{"type": "analytics", "pattern": pattern_type}],
            )


def _extract_date_from_query(query: str) -> str | None:
    """Extract ISO date (YYYY-MM-DD) from natural language query.
    
    Handles patterns like:
    - "may 20", "may 20th", "20 may" → 2024-05-20 (assumes current year)
    - "2024-05-20", "2024/05/20" → 2024-05-20
    - "january 15", "15th jan" → current-year-01-15
    
    Returns None if no date pattern found.
    """
    query_lower = query.lower()
    
    # Try ISO format first (YYYY-MM-DD or YYYY/MM/DD)
    iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', query)
    if iso_match:
        year, month, day = iso_match.groups()
        try:
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        except ValueError:
            pass
    
    # Month name + day patterns
    month_names = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
        'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }
    
    # Pattern: "may 20", "20 may", "may 20th"
    for month_str, month_num in month_names.items():
        # "may 20" or "may 20th"
        match = re.search(rf'{month_str}\s+(\d{{1,2}})(?:st|nd|rd|th)?', query_lower)
        if match:
            day = int(match.group(1))
            year = datetime.now().year
            try:
                return f"{year:04d}-{month_num:02d}-{day:02d}"
            except ValueError:
                pass
        
        # "20 may" or "20th may"
        match = re.search(rf'(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_str}', query_lower)
        if match:
            day = int(match.group(1))
            year = datetime.now().year
            try:
                return f"{year:04d}-{month_num:02d}-{day:02d}"
            except ValueError:
                pass
    
    return None


def query_and_respond(user_message: str) -> str:
    """Retrieve relevant context from ChromaDB and generate a Groq response.

    Steps:
    1. Check for financial-advice keywords → return canned refusal if found.
    2. Extract date from query if present → query database directly for that date.
    3. Check that the collection has been initialised and is non-empty.
    4. Query ChromaDB for top-10 most relevant documents (or use date-filtered).
    5. Build a prompt with the retrieved context + user question.
    6. Call Groq API (llama-3.3-70b-versatile) via _call_with_retry.
    7. Return the LLM response string.

    Fallback responses:
    - Empty/uninitialised collection → "I don't have enough information..."
    - Financial-advice keywords → "I can only describe patterns..."

    Requirements: 12.3–12.8, 19.3, 19.4
    """
    # ------------------------------------------------------------------
    # Financial-advice guard (requirement 19.4)
    # ------------------------------------------------------------------
    lower_message = user_message.lower()
    if any(keyword in lower_message for keyword in _FINANCIAL_ADVICE_KEYWORDS):
        return (
            "I can only describe patterns in your past transactions, "
            "not provide financial advice"
        )

    # ------------------------------------------------------------------
    # Guard: collection must be initialised and contain documents
    # ------------------------------------------------------------------
    if _collection is None:
        return (
            "I don't have enough information in your transaction data to answer that"
        )

    try:
        collection_count = _collection.count()
    except Exception:
        return (
            "I don't have enough information in your transaction data to answer that"
        )

    if collection_count == 0:
        return (
            "I don't have enough information in your transaction data to answer that"
        )

    # ------------------------------------------------------------------
    # Date-specific query handling — query database directly
    # ------------------------------------------------------------------
    extracted_date = _extract_date_from_query(user_message)
    
    if extracted_date:
        # Query database for exact date match
        try:
            date_txns = get_transactions(date_from=extracted_date, date_to=extracted_date)
            
            if date_txns:
                # Build context from date-specific transactions
                context_lines = []
                for txn in date_txns:
                    time_str = f" at {txn['time']}" if txn.get('time') else ""
                    context_lines.append(
                        f"• {txn['description_raw']} — Rs. {txn['amount']} ({txn['category']}) "
                        f"[{txn['direction']}]{time_str}"
                    )
                
                context_block = "\n".join(context_lines)
                user_prompt = (
                    f"Transactions on {extracted_date}:\n{context_block}\n\n"
                    f"User question: {user_message}"
                )
                
                # Call Groq API with date-specific context
                client = _get_client()

                def _api_call():
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": _RAG_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    )
                    return response

                response = _call_with_retry(_api_call)
                
                # Handle case when response is None (all API keys exhausted)
                if response is None or not hasattr(response, 'choices') or not response.choices:
                    return "⚠️ Rate limit reached. AI chat temporarily unavailable. Please try again later."
                
                return response.choices[0].message.content
            else:
                return f"I don't have any transactions recorded for {extracted_date}."
        
        except Exception as exc:
            # Fall back to semantic search if date query fails
            pass

    # ------------------------------------------------------------------
    # Retrieve top-10 most relevant documents (increased from 5)
    # ------------------------------------------------------------------
    try:
        results = _collection.query(
            query_texts=[user_message],
            n_results=min(10, collection_count),
        )
    except Exception as exc:
        raise GroqAPIError(f"ChromaDB query failed: {exc}") from exc

    retrieved_docs = results.get("documents", [[]])[0]

    if not retrieved_docs:
        return (
            "I don't have enough information in your transaction data to answer that"
        )

    # ------------------------------------------------------------------
    # Build prompt with retrieved context
    # ------------------------------------------------------------------
    context_block = "\n".join(
        f"[{i + 1}] {doc}" for i, doc in enumerate(retrieved_docs)
    )
    user_prompt = (
        f"Context from the user's transactions:\n{context_block}\n\n"
        f"User question: {user_message}"
    )

    # ------------------------------------------------------------------
    # Call Groq API with retry logic (requirement 13.1–13.3)
    # ------------------------------------------------------------------
    client = _get_client()

    def _api_call():
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response

    response = _call_with_retry(_api_call)
    
    # Handle case when response is None (all API keys exhausted)
    if response is None or not hasattr(response, 'choices') or not response.choices:
        return "⚠️ Rate limit reached. AI chat temporarily unavailable. Please try again later."
    
    return response.choices[0].message.content
