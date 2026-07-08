"""Pandas-based spending pattern analytics.

All functions accept a pandas DataFrame with columns matching the Transaction
schema: transaction_id, date, time, description_raw, merchant_normalized,
amount, direction, category, balance_after, source_bank.

The `date` column is expected to be a string "YYYY-MM-DD"; each function
converts it to datetime internally.
"""

import numpy as np
import pandas as pd


def compute_day_of_week_pattern(transactions_df: pd.DataFrame) -> dict:
    """Compute total spending grouped by day of week from debit transactions.

    Args:
        transactions_df: DataFrame with transaction records.

    Returns:
        Dict with lowercase day names as keys (monday–sunday), each mapping
        to the total debit spending on that day, plus
        "average_transactions_per_day" (average number of debit transactions
        across the days that have at least one transaction).

        Example::

            {
                "monday": 5600.50,
                "tuesday": 3200.00,
                ...,
                "average_transactions_per_day": 12.5
            }

        All 7 days are always present (0.0 for days with no transactions).
    """
    # Ordered day names for consistent output
    day_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    # Safe empty structure
    empty_result = {day: 0.0 for day in day_order}
    empty_result["average_transactions_per_day"] = 0.0

    if transactions_df.empty:
        return empty_result

    # Filter debit transactions
    debits = transactions_df[transactions_df["direction"] == "debit"].copy()
    if debits.empty:
        return empty_result

    # Parse dates and extract day name
    debits["date"] = pd.to_datetime(debits["date"], format="%Y-%m-%d")
    debits["day_name"] = debits["date"].dt.day_name().str.lower()

    # Total spending per day
    day_totals = debits.groupby("day_name")["amount"].sum()

    # Transaction count per day (for average calculation)
    day_counts = debits.groupby("day_name")["amount"].count()

    result = {day: round(float(day_totals.get(day, 0.0)), 2) for day in day_order}

    # Average transactions per day (across days that appear in data)
    avg = float(day_counts.mean()) if not day_counts.empty else 0.0
    result["average_transactions_per_day"] = round(avg, 2)

    return result


def compute_monthly_trend(transactions_df: pd.DataFrame) -> dict:
    """Compute monthly spending totals and month-over-month % changes.

    Args:
        transactions_df: DataFrame with transaction records.

    Returns:
        Dict with lists for months, amounts, and MoM % changes::

            {
                "months": ["2024-01", "2024-02", ...],
                "amounts": [45000.0, 48000.0, ...],
                "mom_changes": [None, 6.67, ...]
            }

        The first month always has ``None`` for MoM change.
        Returns an empty structure if there are no debit transactions.
    """
    empty_result = {"months": [], "amounts": [], "mom_changes": []}

    if transactions_df.empty:
        return empty_result

    debits = transactions_df[transactions_df["direction"] == "debit"].copy()
    if debits.empty:
        return empty_result

    debits["date"] = pd.to_datetime(debits["date"], format="%Y-%m-%d")
    debits["month"] = debits["date"].dt.to_period("M").astype(str)

    monthly = debits.groupby("month")["amount"].sum().sort_index()

    months = list(monthly.index)
    amounts = [round(float(v), 2) for v in monthly.values]

    mom_changes = [None]
    for i in range(1, len(amounts)):
        prev = amounts[i - 1]
        curr = amounts[i]
        if prev != 0:
            change = round(((curr - prev) / prev) * 100, 2)
        else:
            change = None
        mom_changes.append(change)

    return {"months": months, "amounts": amounts, "mom_changes": mom_changes}


def compute_category_breakdown(transactions_df: pd.DataFrame) -> dict:
    """Compute total spending and percentage share per category.

    Args:
        transactions_df: DataFrame with transaction records.

    Returns:
        Dict with parallel lists sorted by amount descending::

            {
                "categories": ["Food & Dining", "Groceries", ...],
                "amounts": [18000.0, 12000.0, ...],
                "percentages": [37.5, 25.0, ...]
            }

        Percentages sum to 100.0 (within floating-point tolerance).
        Returns empty lists if there are no debit transactions.
    """
    empty_result = {"categories": [], "amounts": [], "percentages": []}

    if transactions_df.empty:
        return empty_result

    debits = transactions_df[transactions_df["direction"] == "debit"].copy()
    if debits.empty:
        return empty_result

    category_totals = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    total = category_totals.sum()

    categories = list(category_totals.index)
    amounts = [round(float(v), 2) for v in category_totals.values]

    if total > 0:
        percentages = [round(float(v / total * 100), 2) for v in category_totals.values]
    else:
        percentages = [0.0] * len(categories)

    return {"categories": categories, "amounts": amounts, "percentages": percentages}


def get_transactions_timeline(transactions_df: pd.DataFrame) -> dict:
    """Return all transactions with full details for timeline visualization.

    Args:
        transactions_df: DataFrame with transaction records.

    Returns:
        Dict containing all transactions with their details::

            {
                "transactions": [
                    {
                        "date": "2024-01-15",
                        "time": "14:30",
                        "amount": 450.0,
                        "direction": "debit",
                        "merchant": "KFC Nepal",
                        "category": "Food & Dining",
                        "description": "KFC NEPAL PAYMENT"
                    },
                    ...
                ]
            }

        Returns empty list if no transactions exist.
    """
    if transactions_df.empty:
        return {"transactions": []}

    # Convert to list of dicts with all relevant fields
    transactions = []
    for _, row in transactions_df.iterrows():
        transactions.append({
            "date": str(row["date"]),
            "time": str(row.get("time", "")) if pd.notna(row.get("time")) else "",
            "amount": round(float(row["amount"]), 2),
            "direction": str(row["direction"]),
            "merchant": str(row.get("merchant_normalized", "")),
            "category": str(row.get("category", "Uncategorized")),
            "description": str(row.get("description_raw", ""))[:100],  # truncate long descriptions
        })

    # Sort by date, then time
    transactions.sort(key=lambda x: (x["date"], x["time"] or "00:00"))

    return {"transactions": transactions}


def detect_anomalies(transactions_df: pd.DataFrame) -> dict:
    """Detect anomalous individual transactions using z-score or IQR method.

    Method selection:
    - **≥ 10 transactions** → z-score: anomaly if amount > mean + 2*std
    - **< 10 transactions** → IQR: anomaly if amount > Q3 + 1.5*IQR

    Args:
        transactions_df: DataFrame with transaction records.

    Returns:
        Dict containing individual transactions, the computed threshold, the method
        name, and an anomaly count::

            {
                "daily_totals": [
                    {"date": "2024-01-15", "amount": 8500.0, "is_anomaly": True, 
                     "merchant": "Laptop Store", "description": "laptop purchase"},
                    ...
                ],
                "threshold": 7200.0,
                "method": "zscore",   # or "iqr"
                "anomaly_count": 2
            }

        Returns a safe empty structure if there are no debit transactions.
        
        Note: Field is still called "daily_totals" for backward compatibility with frontend,
        but now contains individual transactions instead of daily aggregates.
    """
    empty_result = {
        "daily_totals": [],
        "threshold": 0.0,
        "method": "zscore",
        "anomaly_count": 0,
    }

    if transactions_df.empty:
        return empty_result

    debits = transactions_df[transactions_df["direction"] == "debit"].copy()
    if debits.empty:
        return empty_result

    # Work with individual transaction amounts, not daily aggregates
    amounts = debits["amount"].values.astype(float)
    n_transactions = len(debits)

    if n_transactions >= 10:
        method = "zscore"
        mean = float(np.mean(amounts))
        std = float(np.std(amounts, ddof=0))  # population std
        threshold = round(mean + 2 * std, 2)
    else:
        method = "iqr"
        q1 = float(np.percentile(amounts, 25))
        q3 = float(np.percentile(amounts, 75))
        iqr = q3 - q1
        threshold = round(q3 + 1.5 * iqr, 2)

    # Build result with individual transactions
    daily_totals = []
    for _, row in debits.iterrows():
        amount = round(float(row["amount"]), 2)
        is_anomaly = amount > threshold
        daily_totals.append({
            "date": str(row["date"]),
            "amount": amount,
            "is_anomaly": is_anomaly,
            "merchant": str(row.get("merchant_normalized", "")),
            "description": str(row.get("description_raw", ""))[:50],  # truncate long descriptions
        })

    # Sort by date for better visualization
    daily_totals.sort(key=lambda x: x["date"])

    anomaly_count = sum(1 for d in daily_totals if d["is_anomaly"])

    return {
        "daily_totals": daily_totals,
        "threshold": threshold,
        "method": method,
        "anomaly_count": anomaly_count,
    }
