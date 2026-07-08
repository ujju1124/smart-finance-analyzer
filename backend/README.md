---
title: Smart Finance Analyzer Backend
emoji: 💰
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Smart Finance Analyzer Backend

FastAPI backend for Nepali bank statement analysis with PDF parsing, merchant categorization, and AI insights powered by Groq.

## Features

- PDF statement parsing with pdfplumber
- LLM-based transaction structuring (Groq llama-3.3-70b-versatile)
- Automatic merchant categorization for Nepali businesses
- Spending analytics (day-of-week, monthly trends, categories, anomalies)
- AI-generated insights
- RAG-powered chat interface

## Environment Variables

Required:
- `GROQ_API_KEY` - Your Groq API key from https://console.groq.com

## API Endpoints

- `POST /api/upload` - Upload bank statement PDF
- `GET /api/sample` - Load sample transaction data
- `GET /api/transactions` - List transactions with filters
- `GET /api/analytics/{pattern}` - Get analytics + AI insights
- `POST /api/chat` - RAG chat interface

Full API documentation available at `/docs` endpoint.
