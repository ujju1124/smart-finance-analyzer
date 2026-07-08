# Data Files

## sample_transactions.json

Synthetic bank statement data for demo/portfolio use. Contains ~130 transactions spanning September 2024 – February 2025.

**Structure:**
```json
{
  "transactions": [ /* array of Transaction objects */ ]
}
```

Each transaction has 10 fields matching the exact schema from `domain.md`:
`transaction_id`, `date`, `time`, `description_raw`, `merchant_normalized`, `amount`, `direction`, `category`, `balance_after`, `source_bank`.

All records have `source_bank: "Sample"`.

**Realistic patterns included:**
- Monthly salary credit on the 1st (~NPR 85,000)
- Rent payment on the 5th (~NPR 25,000)
- Utility bills on the 10th (NEA, Ncell, Khanepani)
- Weekend spending spikes (higher Food & Dining on Fridays/Saturdays)
- 2–3 deliberate anomalies (unusually high single-day spending) for anomaly detection demo

**Category distribution:** Food & Dining ~25%, Groceries ~20%, Transport ~12%, Utilities ~10%, and others.

To regenerate with different parameters, edit `backend/generate_sample_data.py` and run it with Python.

---

## merchant_categories.json

Lookup table mapping merchant names (lowercase) to the 14 fixed spending categories.

**Structure:**
```json
{
  "version": "1.0",
  "categories": [ /* 14 fixed category strings */ ],
  "merchant_map": {
    "daraz": "Shopping",
    "bhatbhateni": "Groceries",
    ...
  }
}
```

**How it grows:** When a merchant is not found in this file, the categorizer falls back to the Groq LLM (`llama-3.1-8b-instant`), which classifies it into one of the 14 categories. The new mapping is then written back to this file — so the same merchant is never sent to the LLM twice.

**The 14 fixed categories (closed set):**
1. Groceries
2. Food & Dining
3. Transport
4. Utilities
5. Shopping
6. Digital Wallet & Transfers
7. Entertainment
8. Healthcare
9. Education
10. Rent & Housing
11. Cash Withdrawal
12. Bank Fees & Charges
13. Income & Salary
14. Uncategorized
