"""Transactions router — GET /api/transactions

Returns the stored transactions with optional date range, category, and
direction filters.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

try:
    import db
    from models.schemas import Transaction, TransactionListResponse
except ImportError:
    from backend import db
    from backend.models.schemas import Transaction, TransactionListResponse

router = APIRouter()


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    direction: Optional[str] = None,
):
    """Retrieve transactions with optional filters.

    Query parameters:
    - date_from: include transactions on or after this date (YYYY-MM-DD)
    - date_to: include transactions on or before this date (YYYY-MM-DD)
    - category: filter by spending category (exact match)
    - direction: filter by "debit" or "credit"

    Returns 404 if no transactions match the filters (or if the database
    is empty).
    """
    rows = db.get_transactions(
        date_from=date_from,
        date_to=date_to,
        category=category,
        direction=direction,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No transactions found")

    transactions = [Transaction(**row) for row in rows]

    return TransactionListResponse(
        transactions=transactions,
        total_count=len(transactions),
    )
