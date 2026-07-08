# Nepali Finance Analyzer — API Reference

Base URL: `http://localhost:8000`  
Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## Health

### GET /health
Returns server status.

**Response 200:**
```json
{"status": "ok"}
```

---

## Upload

### POST /api/upload
Upload a PDF bank statement for processing.

**Request:** `multipart/form-data`
- `file` (required): PDF file, max 10 MB

**Response 200:**
```json
{
  "success": true,
  "transaction_count": 42,
  "errors": [],
  "message": null
}
```

**Error responses:**
- `400` — File must be a PDF / scanned image / no transactions found
- `413` — File exceeds 10 MB limit
- `429` — Groq rate limit reached
- `500` — Processing error

---

## Sample Data

### GET /api/sample
Load bundled synthetic sample transactions.

**Response 200:**
```json
{
  "success": true,
  "transaction_count": 130,
  "message": "Sample data loaded successfully"
}
```

---

## Transactions

### GET /api/transactions
Retrieve all stored transactions with optional filters.

**Query parameters (all optional):**
- `date_from` — ISO 8601 date string (YYYY-MM-DD), inclusive
- `date_to` — ISO 8601 date string (YYYY-MM-DD), inclusive
- `category` — one of the 14 fixed categories
- `direction` — `debit` or `credit`

**Response 200:**
```json
{
  "transactions": [...],
  "total_count": 42
}
```

**Error responses:**
- `404` — No transactions found

---

## Analytics

### GET /api/analytics/{pattern_type}
Compute spending analytics and generate an AI insight.

**Path parameter:**
- `pattern_type` — one of: `day-of-week`, `monthly-trend`, `category-breakdown`, `anomalies`

**Response 200:**
```json
{
  "data": { ... },
  "insight": "You spend most on Fridays with NPR 8,450 average."
}
```

**Data shapes by pattern_type:**

`day-of-week`:
```json
{"monday": 5600.50, "tuesday": 3200.00, ..., "average_transactions_per_day": 12.5}
```

`monthly-trend`:
```json
{"months": ["2024-01", "2024-02"], "amounts": [45000, 48000], "mom_changes": [null, 6.67]}
```

`category-breakdown`:
```json
{"categories": ["Food & Dining", ...], "amounts": [18000, ...], "percentages": [37.5, ...]}
```

`anomalies`:
```json
{
  "daily_totals": [{"date": "2024-01-15", "amount": 8500, "is_anomaly": true}],
  "threshold": 7200.0,
  "method": "zscore",
  "anomaly_count": 2
}
```

**Error responses:**
- `400` — Unknown pattern type
- `404` — No transactions loaded
- `429` — Groq rate limit reached

---

## Chat

### POST /api/chat
Ask a question about your transactions (RAG-powered).

**Request body:**
```json
{"message": "How much did I spend on food last month?"}
```
- `message`: string, 1–500 characters

**Response 200:**
```json
{"response": "You spent NPR 18,450 on Food & Dining in January 2024.", "error": null}
```

**Error responses:**
- `400` — Empty or invalid message
- `429` — Groq rate limit reached
- `500` — RAG processing error
