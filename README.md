# Nepali Finance Analyzer

A personal finance analyzer built for Nepali bank users. Upload a bank statement PDF (or use the bundled sample data) and get a clean transaction list, automatic spending categorization tuned to Nepali merchants, visual spending-pattern analysis with AI-written insights, and a conversational chat interface to ask questions about your own spending.

The app is fully local — uploaded PDFs are processed and deleted immediately. The only external service used is the [Groq API](https://console.groq.com) for LLM calls, which is free with no credit card required.

---

## Tech Stack

| Layer | Libraries |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn, pandas, pdfplumber, chromadb, groq |
| **Frontend** | React (Vite), react-plotly.js |
| **Database** | SQLite (single file, no server setup needed) |
| **LLM** | Groq — `llama-3.3-70b-versatile` for parsing/insights/chat, `llama-3.1-8b-instant` for merchant categorization |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Groq API key** (free, no credit card) — get one at https://console.groq.com

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Configuration

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_key_here
```

The `.env` file should live in the project root. The backend reads `GROQ_API_KEY` from this file on startup. If the key is missing, the server will still start but endpoints that call the Groq API will return errors.

---

## Running

```bash
# Terminal 1 — Backend
cd backend
python main.py
# or: uvicorn backend.main:app --reload
```

```bash
# Terminal 2 — Frontend
cd frontend
npm run dev
```

- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:5173
- **API docs (Swagger)**: http://localhost:8000/docs

---

## Running Tests

```bash
# Backend tests (from project root)
python -m pytest backend/tests/ -v
```

```bash
# Frontend tests
cd frontend
npm test
```

---

## Usage

**Upload PDF mode** — click "Upload PDF", select a bank statement PDF (text-based, not scanned), and click upload. The app extracts transactions using pdfplumber, structures them with the Groq LLM, categorizes merchants, and displays charts and chat immediately. The PDF is deleted from the server as soon as processing finishes.

**Sample Data mode** — click "Use Sample Data" to load a bundled set of ~130 synthetic transactions spanning 6 months. This is ideal for exploring the app without a real bank statement.

Once data is loaded, the Dashboard shows four charts — Day-of-Week spending, Monthly Trend, Category Breakdown, and Anomaly Detection — each with a one-sentence AI-generated insight. The Chat panel at the bottom lets you ask free-form questions about your transactions (e.g. "How much did I spend on food in March?").

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload a bank statement PDF for processing |
| `GET` | `/api/sample` | Load bundled sample transaction data |
| `GET` | `/api/transactions` | List transactions with optional filters (`date_from`, `date_to`, `category`, `direction`) |
| `GET` | `/api/analytics/{pattern_type}` | Get computed analytics + AI insight. `pattern_type` is one of: `day-of-week`, `monthly-trend`, `category-breakdown`, `anomalies` |
| `POST` | `/api/chat` | Send a chat message; returns a RAG-grounded response |

Full interactive docs available at http://localhost:8000/docs when the backend is running.

---

## Groq Free Tier Limits

Groq's free tier (no credit card required) has daily usage caps:

- **`llama-3.3-70b-versatile`** — ~1,000 requests/day, 100K tokens/day. Used for PDF parsing, insight generation, and chat.
- **`llama-3.1-8b-instant`** — ~14,400 requests/day. Used only for merchant categorization fallback (high-volume, simple classification).

If you hit the rate limit, the app will display a "Rate limit reached, please try again later" message rather than failing silently. The backend implements automatic exponential backoff (5s → 10s → 20s, up to 3 retries) before surfacing the error.

For development, avoid re-uploading the same PDF repeatedly — the app caches categorized merchants in `backend/data/merchant_categories.json` to minimize repeat LLM calls.
