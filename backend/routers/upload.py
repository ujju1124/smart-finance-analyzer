"""Upload router — POST /api/upload

Handles PDF bank statement uploads: validates the file, extracts text,
structures transactions via LLM, categorizes merchants, persists to SQLite,
and initialises ChromaDB for RAG chat.
"""

import logging
import os
import tempfile
import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import ValidationError

try:
    import db
    from models.schemas import Transaction, UploadResponse
    from services.categorizer import categorize_transaction
    from services import llm_structurer
    from services.llm_structurer import GroqAPIError, structure_transactions
    from services.pdf_parser import PDFTextExtractionError, extract_pages
    from services.rag_engine import initialize_chromadb
except ImportError:
    from backend import db
    from backend.models.schemas import Transaction, UploadResponse
    from backend.services.categorizer import categorize_transaction
    from backend.services import llm_structurer
    from backend.services.llm_structurer import GroqAPIError, structure_transactions
    from backend.services.pdf_parser import PDFTextExtractionError, extract_pages
    from backend.services.rag_engine import initialize_chromadb

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), request: Request = None):
    """Upload a PDF bank statement and extract structured transactions.

    Optional header:
    - X-Groq-API-Key: User-provided Groq API key (session-only, never stored)

    Validation order:
    1. content_type must be application/pdf → 400
    2. file size must be ≤ 10 MB → 413
    3. PDF must contain extractable text (not a scanned image) → 400
    4. LLM must return ≥ 1 transaction → 400
    """
    # ------------------------------------------------------------------
    # 0. Extract user-provided API key from header (if present)
    # ------------------------------------------------------------------
    user_api_key = request.headers.get("x-groq-api-key") if request else None
    
    # Set user API key for this request (cleared at end)
    # SECURITY: This key is only held in memory for this request and never persisted
    if user_api_key:
        llm_structurer.set_user_api_key(user_api_key)
    
    try:
        # ------------------------------------------------------------------
        # 1. Validate content type
        # ------------------------------------------------------------------
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must be a PDF")

        # ------------------------------------------------------------------
        # 2. Read file bytes and validate size
        # ------------------------------------------------------------------
        contents = await file.read()
        if len(contents) > _MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File exceeds 10MB limit")

        # ------------------------------------------------------------------
        # 3. Write to a temp file for pdfplumber (needs a path)
        # ------------------------------------------------------------------
        tmp_path = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # ------------------------------------------------------------------
        # 4. Extract pages from PDF
        # ------------------------------------------------------------------
        try:
            pages = extract_pages(tmp_path)
            logger.info(f"Extracted {len(pages)} pages from PDF")
        except PDFTextExtractionError:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This PDF appears to be a scanned image. "
                    "Please upload a text-based statement"
                ),
            )

        # ------------------------------------------------------------------
        # 5. Structure transactions via LLM (page-by-page)
        # ------------------------------------------------------------------
        try:
            raw_transactions = structure_transactions(pages)
            
            logger.info(f"LLM returned {len(raw_transactions)} transactions from {len(pages)} pages")
            
        except GroqAPIError as exc:
            if "Rate limit" in str(exc):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit reached. Please try again in a few minutes.",
                )
            raise HTTPException(status_code=500, detail=str(exc))

        # ------------------------------------------------------------------
        # 6. Check that at least one transaction was found
        # ------------------------------------------------------------------
        if not raw_transactions:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No transactions found. "
                    "Please ensure this is a valid bank statement"
                ),
            )

        errors: list[str] = []

        # Warn if suspiciously few transactions
        if len(raw_transactions) < 5:
            errors.append(
                f"Only {len(raw_transactions)} transaction(s) found. "
                "Please verify this is a complete bank statement."
            )

        # ------------------------------------------------------------------
        # 7. Set source_bank, validate with Pydantic, categorize
        # ------------------------------------------------------------------
        validated: list[dict] = []
        for raw in raw_transactions:
            raw["source_bank"] = "Other"

            # Categorize merchant (pattern match → cache hit → LLM fallback)
            try:
                raw["category"] = categorize_transaction(
                    raw.get("merchant_normalized", ""),
                    raw.get("description_raw", ""),
                    raw.get("direction", "")  # Pass direction for direction-aware patterns
                )
            except GroqAPIError as exc:
                if "Rate limit" in str(exc):
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit reached. Please try again in a few minutes.",
                    )
                # Non-fatal: fall back to Uncategorized
                raw["category"] = "Uncategorized"
                logger.warning("Categorization failed for %s: %s", raw.get("merchant_normalized"), exc)

            try:
                txn = Transaction(**raw)
                validated.append(txn.model_dump())
            except ValidationError as exc:
                # Collect field-level errors but don't abort — skip the bad row
                for error in exc.errors():
                    field = ".".join(str(f) for f in error["loc"])
                    errors.append(
                        f"Transaction validation error — {field}: {error['msg']}"
                    )

        # ------------------------------------------------------------------
        # 8. Persist to SQLite and (re-)initialise ChromaDB
        # ------------------------------------------------------------------
        if errors:
            logger.warning("Validation errors on upload (%d errors, %d valid out of %d raw): %s",
                           len(errors), len(validated), len(raw_transactions), errors[:5])

        if not validated:
            raise HTTPException(
                status_code=400,
                detail=f"All transactions failed validation. First error: {errors[0] if errors else 'unknown'}"
            )

        db.clear_transactions()
        db.insert_transactions(validated)
        initialize_chromadb(validated)

        return UploadResponse(
            success=True,
            transaction_count=len(validated),
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error in upload_pdf: %s", exc)
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")
    finally:
        # Clear user-provided API key after request completes
        # SECURITY: Ensures key is never held longer than request duration
        if user_api_key:
            llm_structurer.set_user_api_key(None)
        
        # Always clean up the temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
