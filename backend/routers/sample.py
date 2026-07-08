"""Sample data router — GET /api/sample

Loads the bundled synthetic transactions from
backend/data/sample_transactions.json, validates each record with Pydantic,
persists them to SQLite, and initialises ChromaDB for RAG chat.
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

try:
    import db
    from models.schemas import SampleDataResponse, Transaction
    from services.rag_engine import initialize_chromadb
except ImportError:
    from backend import db
    from backend.models.schemas import SampleDataResponse, Transaction
    from backend.services.rag_engine import initialize_chromadb

logger = logging.getLogger(__name__)

router = APIRouter()

_SAMPLE_DATA_PATH = Path(__file__).parent.parent / "data" / "sample_transactions.json"


@router.get("/sample", response_model=SampleDataResponse)
async def load_sample_data():
    """Load the bundled sample transactions into the database.

    Reads sample_transactions.json, validates every record against the
    Transaction schema, clears the existing database, inserts the validated
    transactions, and re-initialises ChromaDB.
    """
    # ------------------------------------------------------------------
    # Load sample data file
    # ------------------------------------------------------------------
    try:
        with open(_SAMPLE_DATA_PATH, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Sample data file not found on server.",
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Sample data file is malformed: {exc}",
        )

    raw_transactions: list[dict] = payload.get("transactions", [])

    # ------------------------------------------------------------------
    # Validate each transaction with Pydantic
    # ------------------------------------------------------------------
    validated: list[dict] = []
    for raw in raw_transactions:
        try:
            txn = Transaction(**raw)
            validated.append(txn.model_dump())
        except ValidationError as exc:
            # Log but skip invalid records — sample data should always be clean
            logger.warning("Sample transaction validation error: %s", exc)

    if not validated:
        raise HTTPException(
            status_code=500,
            detail="No valid transactions found in sample data file.",
        )

    # ------------------------------------------------------------------
    # Persist to SQLite and re-initialise ChromaDB
    # ------------------------------------------------------------------
    db.clear_transactions()
    db.insert_transactions(validated)
    initialize_chromadb(validated)

    return SampleDataResponse(
        success=True,
        transaction_count=len(validated),
        message="Sample data loaded successfully",
    )
