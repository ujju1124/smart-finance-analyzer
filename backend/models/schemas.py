"""Pydantic models for transaction schema and API request/response schemas.

This module defines all data models matching the exact 10-field transaction
schema from domain.md, along with API endpoint request/response models.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class Transaction(BaseModel):
    """Transaction model conforming to the exact 10-field schema.
    
    All transactions must conform to this schema with proper validation
    for date (ISO 8601 YYYY-MM-DD) and time (HH:MM 24-hour format).
    """
    transaction_id: str = Field(..., description="UUID string")
    date: str = Field(..., description="ISO 8601 date YYYY-MM-DD")
    time: Optional[str] = Field(None, description="HH:MM 24-hour format or null")
    description_raw: str = Field(..., min_length=1, description="Exact text from PDF")
    merchant_normalized: str = Field(..., min_length=1, description="Cleaned merchant name")
    amount: float = Field(..., gt=0, description="Positive number")
    direction: Literal["debit", "credit"]
    category: Literal[
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
        "Uncategorized"
    ]
    balance_after: Optional[float] = Field(None, description="Number or null")
    source_bank: Literal["NMB", "Kumari", "Nabil", "Other", "Sample"]

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate ISO 8601 format (YYYY-MM-DD)."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('Date must be in ISO 8601 format (YYYY-MM-DD)')
        return v

    @field_validator('time')
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize time to HH:MM 24-hour format.
        
        Accepts: HH:MM, H:MM, HH:MM:SS (truncates seconds), H:MM:SS
        """
        if v is not None:
            # Strip seconds if present: "14:30:00" → "14:30"
            if len(v) >= 5 and v.count(':') >= 2:
                v = v[:5]
            # Auto-pad single-digit hours: "9:23" → "09:23"
            if len(v) == 4 and v[1] == ':':
                v = '0' + v
            if not (len(v) == 5 and v[2] == ':'):
                raise ValueError('Time must be in HH:MM format')
            try:
                hours, minutes = v.split(':')
                hour = int(hours)
                minute = int(minutes)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError('Time must be valid HH:MM (00:00-23:59)')
            except (ValueError, IndexError):
                raise ValueError('Time must be in HH:MM format')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "date": "2024-01-15",
                "time": "14:30",
                "description_raw": "Payment to Bhatbhateni Supermarket",
                "merchant_normalized": "Bhatbhateni Supermarket",
                "amount": 3450.50,
                "direction": "debit",
                "category": "Groceries",
                "balance_after": 45600.25,
                "source_bank": "NMB"
            }
        }
    }


class UploadResponse(BaseModel):
    """Response model for PDF upload endpoint."""
    success: bool
    transaction_count: int
    errors: list[str] = Field(default_factory=list)
    message: Optional[str] = None


class SampleDataResponse(BaseModel):
    """Response model for sample data loading endpoint."""
    success: bool
    transaction_count: int
    message: str = "Sample data loaded successfully"


class TransactionListResponse(BaseModel):
    """Response model for transaction list endpoint."""
    transactions: list[Transaction]
    total_count: int


class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoints.
    
    The data structure varies by pattern type:
    - day-of-week: {"monday": 5600.50, "tuesday": 3200.00, ...}
    - monthly-trend: {"2024-01": 45000.00, "2024-02": 48000.00, ...}
    - category-breakdown: {"Groceries": {"amount": 12000, "percentage": 25.5}, ...}
    - anomalies: [{"date": "2024-01-15", "amount": 15000, "threshold": 8000}, ...]
    """
    data: dict
    insight: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    error: Optional[str] = None
