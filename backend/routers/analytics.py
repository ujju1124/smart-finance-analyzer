"""Analytics router — GET /api/analytics/{pattern_type}

Computes spending patterns from the stored transactions and returns the
result together with a one-sentence AI-generated insight.

Supported pattern types:
- day-of-week
- monthly-trend
- category-breakdown
- anomalies
"""

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

try:
    import db
    from models.schemas import AnalyticsResponse
    from services import llm_structurer
    from services.insight_generator import generate_insight
    from services.llm_structurer import GroqAPIError
    from services.pattern_analytics import (
        compute_category_breakdown,
        compute_day_of_week_pattern,
        compute_monthly_trend,
        detect_anomalies,
        get_transactions_timeline,
    )
except ImportError:
    from backend import db
    from backend.models.schemas import AnalyticsResponse
    from backend.services import llm_structurer
    from backend.services.insight_generator import generate_insight
    from backend.services.llm_structurer import GroqAPIError
    from backend.services.pattern_analytics import (
        compute_category_breakdown,
        compute_day_of_week_pattern,
        compute_monthly_trend,
        detect_anomalies,
        get_transactions_timeline,
    )

router = APIRouter()

_VALID_PATTERN_TYPES = frozenset({
    "day-of-week",
    "monthly-trend",
    "category-breakdown",
    "anomalies",
    "transactions-timeline",
})

_PATTERN_HANDLERS = {
    "day-of-week": compute_day_of_week_pattern,
    "monthly-trend": compute_monthly_trend,
    "category-breakdown": compute_category_breakdown,
    "anomalies": detect_anomalies,
    "transactions-timeline": get_transactions_timeline,
}


@router.get("/analytics/{pattern_type}", response_model=AnalyticsResponse)
async def get_analytics(pattern_type: str, request: Request):
    """Return computed analytics data and an AI insight for the given pattern type.

    Path parameter:
    - pattern_type: one of day-of-week | monthly-trend | category-breakdown | anomalies | transactions-timeline

    Header:
    - X-Groq-API-Key (optional): User-provided Groq API key for this request

    Returns 404 if no transactions are loaded, 400 for an unknown pattern type,
    and 429 if the Groq rate limit is hit while generating the insight.
    """
    # ------------------------------------------------------------------
    # Extract user-provided API key if present
    # ------------------------------------------------------------------
    user_api_key = request.headers.get("X-Groq-API-Key")
    if user_api_key:
        llm_structurer.set_user_api_key(user_api_key)
    
    try:
        # ------------------------------------------------------------------
        # Validate pattern type first (cheap check before hitting the DB)
        # ------------------------------------------------------------------
        if pattern_type not in _VALID_PATTERN_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown pattern type '{pattern_type}'. "
                    f"Valid options: {', '.join(sorted(_VALID_PATTERN_TYPES))}"
                ),
            )

        # ------------------------------------------------------------------
        # Load transactions from SQLite
        # ------------------------------------------------------------------
        rows = db.get_transactions()
        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No transactions found. Please upload a statement or load sample data.",
            )

        # ------------------------------------------------------------------
        # Build DataFrame and run the analytics function
        # ------------------------------------------------------------------
        df = pd.DataFrame(rows)
        handler = _PATTERN_HANDLERS[pattern_type]
        computed_data = handler(df)

        # ------------------------------------------------------------------
        # Generate AI insight via Groq
        # ------------------------------------------------------------------
        try:
            insight = generate_insight(pattern_type, computed_data)
        except GroqAPIError as exc:
            if "Rate limit" in str(exc):
                # Return data without insight when rate limit is hit (graceful degradation)
                insight = "⚠️ Rate limit reached. AI insights temporarily unavailable. Please try again later."
            else:
                raise HTTPException(status_code=500, detail=str(exc))

        return AnalyticsResponse(data=computed_data, insight=insight)
    finally:
        # Clear user API key after request completes
        if user_api_key:
            llm_structurer.set_user_api_key(None)
