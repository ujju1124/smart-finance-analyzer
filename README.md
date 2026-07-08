# 💰 Smart Finance Analyzer

> AI-powered personal finance insights for Nepali bank users

A modern web application that transforms your bank statement PDFs into actionable financial insights. Built specifically for Nepali banks and merchants, this tool helps you understand your spending patterns through intelligent categorization, visual analytics, and conversational AI chat.

[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://smart-finance-analyzer-ashy.vercel.app)
[![Backend API](https://img.shields.io/badge/API-HuggingFace%20Spaces-orange)](https://ujju33-smart-finance-backend.hf.space)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🎯 Why Use This?

### The Problem
Managing personal finances in Nepal is challenging:
- Bank statements are PDF-only with inconsistent formats across banks (NMB, Kumari, Nabil, etc.)
- No easy way to visualize spending patterns or track where money goes
- Manual categorization of transactions is time-consuming and error-prone
- Understanding monthly trends requires spreadsheet expertise

### The Solution
Smart Finance Analyzer solves these problems by:
- **Automatically parsing** any Nepali bank statement PDF (no matter the format)
- **Intelligently categorizing** transactions using a curated database of 50+ Nepali merchants
- **Visualizing patterns** through 4 interactive charts with AI-generated insights
- **Answering questions** about your spending through natural language chat

---

## ✨ Key Features

### 📄 **Universal PDF Parsing**
- Supports any Nepali bank (NMB, Kumari, Nabil, and others)
- Format-agnostic extraction using AI — no hardcoded templates
- Processes text-based PDFs in seconds
- Automatic cleanup after processing (PDFs never stored)

### 🏷️ **Smart Categorization**
- **14 categories** tailored for Nepali spending habits:
  - Groceries (Bhatbhateni, Big Mart, Saleways)
  - Food & Dining (Foodmandu, KFC, Pizza Hut, local restaurants)
  - Transport (Pathao, Tootle, InDrive, Sajha)
  - Utilities (Nepal Telecom, Ncell, NEA, Khanepani)
  - Digital Wallets (eSewa, Khalti, ConnectIPS)
  - Shopping, Healthcare, Education, and more
- **50+ pre-mapped merchants** with automatic fallback to AI for unknown vendors
- **Smart learning** — newly categorized merchants are saved for future use

### 📊 **Visual Analytics**
Four chart types with AI-generated insights:

1. **Spending by Day of Week** — Discover which days you spend the most
2. **Monthly Spending Trend** — Track how your expenses change over time
3. **Category Breakdown** — See exactly where your money goes (pie chart)
4. **Anomaly Detection** — Identify unusual large transactions automatically

Each chart includes a natural language insight like:
> "Spending occurs only on certain days of the week, with outlays of NPR 1300.0 on Tuesday, NPR 1040.0 on Thursday..."

### 💬 **AI Chat Assistant**
Ask questions about your transactions in plain English or Nepali-influenced English:
- "What did I spend on food last month?"
- "Show me all eSewa transactions"
- "What was my biggest expense in June?"
- "Did I have any unusual spending this week?"

The chat uses **RAG (Retrieval-Augmented Generation)** to ground responses in your actual transaction data, ensuring accuracy and relevance.

**Safety Built-In:** The AI will never give financial advice — it only describes patterns in your past transactions.

### 🎨 **Demo Mode**
Try the app instantly without uploading anything:
- Click "Try Demo" to load 99 synthetic transactions
- Explore all features risk-free
- Perfect for understanding what the app does before using real data

---

## 🏗️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance REST API framework |
| **pdfplumber** | PDF text extraction (with poppler-utils) |
| **Groq API** | LLM inference (`llama-3.3-70b-versatile` for parsing/insights, `llama-3.1-8b-instant` for categorization) |
| **pandas** | All analytics computations (day-of-week, trends, anomalies) |
| **ChromaDB** | Vector database for RAG chat (local embedding with sentence-transformers) |
| **SQLite** | Transaction storage (single-file, no server setup) |
| **Python 3.11+** | Modern async/await support |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React + Vite** | Fast, modern UI framework |
| **Plotly.js** | Interactive charts (zoom, hover, export) |
| **CSS** | Clean, responsive styling |

### Infrastructure
| Service | Purpose |
|---------|---------|
| **Hugging Face Spaces** | Backend hosting (Docker containers) |
| **Vercel** | Frontend hosting (global CDN) |
| **GitHub** | Version control and CI/CD |

---

## 🚀 Getting Started

### Option 1: Use the Live Demo (Recommended)
No installation needed — just visit the live app:
- **Frontend:** [smart-finance-analyzer-ashy.vercel.app](https://smart-finance-analyzer-ashy.vercel.app)
- **Backend API:** [ujju33-smart-finance-backend.hf.space](https://ujju33-smart-finance-backend.hf.space)

### Option 2: Run Locally

#### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Groq API key (get one at [console.groq.com](https://console.groq.com))

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set up environment variable
export GROQ_API_KEY="your_groq_api_key"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

#### Frontend Setup
```bash
cd frontend
npm install

# Set up environment variable
echo "VITE_API_URL=http://localhost:8000" > .env.development

# Run the dev server
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## 📖 How to Use

### Step 1: Choose Your Data Source
- **Upload PDF:** Click "Upload PDF" and select your bank statement
- **Try Demo:** Click "Try Demo" to use synthetic sample data

### Step 2: Explore Your Analysis
Once data is loaded, you'll see:
- **Transaction count** and **date range** at the top
- **4 interactive charts** showing spending patterns
- **AI-generated insights** below each chart

### Step 3: Ask Questions
Scroll to the chat panel and ask about your transactions:
- Simple queries: "What did I spend most on?"
- Date-specific: "Show me transactions on June 21"
- Category filters: "How much did I spend on transport?"
- Merchant search: "Did I buy anything from Bhatbhateni?"

---

## 🔒 Privacy & Security

### Your Data is Safe
- **No data storage:** Uploaded PDFs are processed and immediately deleted
- **Local processing:** Transaction extraction happens on the server, not sent to third parties
- **Ephemeral sessions:** Data only exists in your browser session (cleared on reload)
- **No tracking:** No analytics, cookies, or user tracking

### What Gets Sent to Groq?
Only minimal data needed for processing:
- **PDF parsing:** Raw text from your PDF (not the file itself)
- **Categorization:** Merchant names only (not amounts or dates)
- **Chat:** Your question + relevant transaction excerpts (not your entire history)

Groq does not store API request/response data beyond 30 days for abuse monitoring.

---

## 🎯 Use Cases

### 1. **Monthly Budget Review**
Upload your statement at month-end to see:
- Which category consumed the most budget
- Days of the week you overspend
- Unusual large transactions you might have forgotten

### 2. **Expense Reporting**
Quickly filter and export transactions by:
- Category (for business expense reports)
- Date range (for quarterly reviews)
- Merchant (for specific vendor analysis)

### 3. **Spending Habit Analysis**
Use the chat to explore patterns:
- "Do I spend more on weekdays or weekends?"
- "What's my average food expense per month?"
- "Show me all transactions over NPR 5000"

### 4. **Portfolio Project Showcase**
This is a fully functional, production-ready application perfect for:
- Full-stack developer portfolios
- AI/ML project demonstrations
- Web application architecture case studies

---

## 📊 Sample Analytics Output

**Category Breakdown:**
```
Digital Wallet & Transfers: 74%
Shopping: 25%
Food & Dining: 1%
```

**Day of Week Pattern:**
```
Tuesday: NPR 1,300 (highest)
Sunday: NPR 1,240
Thursday: NPR 1,040
```

**Monthly Trend:**
```
June 2026: NPR 2,745 → July 2026: NPR 1,500 (-45%)
```

**Anomalies Detected:**
```
• NPR 13,000 ATM withdrawal on June 23 (flagged as unusually high)
```

---

## 🛠️ API Reference

### Base URL
- **Local:** `http://localhost:8000`
- **Production:** `https://ujju33-smart-finance-backend.hf.space`

### Endpoints

#### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "message": "Success",
  "transaction_count": 9,
  "date_range": "2026-06-20 to 2026-07-05"
}
```

#### Load Sample Data
```http
GET /api/sample
```

#### Get Transactions
```http
GET /api/transactions?date_from=2026-06-01&date_to=2026-06-30&category=Food%20%26%20Dining
```

#### Get Analytics
```http
GET /api/analytics/day-of-week
GET /api/analytics/monthly-trend
GET /api/analytics/category-breakdown
GET /api/analytics/anomalies
```

#### Chat
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What did I spend on food?"
}
```

**Full interactive API docs:** [/docs](https://ujju33-smart-finance-backend.hf.space/docs)

---

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_categorizer.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
```

---

## 🤝 Contributing

Contributions are welcome! Here are some ideas:
- Add support for more Nepali banks
- Expand the merchant categorization database
- Implement export to CSV/Excel
- Add multi-currency support
- Improve chart interactivity

**To contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Groq** for providing fast, free LLM inference
- **Hugging Face** for free backend hosting
- **Vercel** for seamless frontend deployment
- **Nepali banking community** for inspiring this project

---

## 📧 Contact

Created by **Ujwal** - [@ujju1124](https://github.com/ujju1124)

- **Live Demo:** [smart-finance-analyzer-ashy.vercel.app](https://smart-finance-analyzer-ashy.vercel.app)
- **GitHub:** [github.com/ujju1124/smart-finance-analyzer](https://github.com/ujju1124/smart-finance-analyzer)
- **Issues:** [Report a bug or request a feature](https://github.com/ujju1124/smart-finance-analyzer/issues)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub! It helps others discover the project and motivates continued development.

---

