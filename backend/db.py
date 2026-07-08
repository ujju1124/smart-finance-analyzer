"""
SQLite database connection and operations for transaction storage.

This module provides database initialization, transaction storage, and retrieval
functionality using SQLite as the single-file database backend.
"""
import sqlite3
from typing import Optional, List
from pathlib import Path

# Database file path — always relative to this file so it resolves correctly
# regardless of where the server is launched from
DB_PATH = Path(__file__).parent.resolve() / "transactions.db"


def init_db() -> None:
    """
    Initialize SQLite database and create transactions table if not exists.
    
    Schema enforces:
    - 10-field transaction structure from domain.md
    - CHECK constraints for direction (debit/credit) and source_bank enums
    - Indexes on date, category, and direction for efficient filtering
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            time TEXT,
            description_raw TEXT NOT NULL,
            merchant_normalized TEXT NOT NULL,
            amount REAL NOT NULL,
            direction TEXT NOT NULL,
            category TEXT NOT NULL,
            balance_after REAL,
            source_bank TEXT NOT NULL,
            CHECK (direction IN ('debit', 'credit')),
            CHECK (source_bank IN ('NMB', 'Kumari', 'Nabil', 'Other', 'Sample'))
        )
    """)
    
    # Create indexes for efficient filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON transactions(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON transactions(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_direction ON transactions(direction)")
    
    conn.commit()
    conn.close()


def insert_transactions(transactions: List[dict]) -> None:
    """
    Bulk insert validated transactions into SQLite database.
    
    Args:
        transactions: List of transaction dictionaries conforming to schema
    """
    if not transactions:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prepare data for bulk insert
        for transaction in transactions:
            cursor.execute("""
                INSERT INTO transactions (
                    transaction_id, date, time, description_raw, merchant_normalized,
                    amount, direction, category, balance_after, source_bank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.get('transaction_id'),
                transaction.get('date'),
                transaction.get('time'),
                transaction.get('description_raw'),
                transaction.get('merchant_normalized'),
                transaction.get('amount'),
                transaction.get('direction'),
                transaction.get('category'),
                transaction.get('balance_after'),
                transaction.get('source_bank')
            ))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_transactions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    direction: Optional[str] = None
) -> List[dict]:
    """
    Query transactions with optional filters, ordered by date DESC, time DESC.
    
    Args:
        date_from: Filter transactions on or after this date (ISO 8601 YYYY-MM-DD)
        date_to: Filter transactions on or before this date (ISO 8601 YYYY-MM-DD)
        category: Filter by spending category
        direction: Filter by transaction direction ('debit' or 'credit')
    
    Returns:
        List of transaction dictionaries matching filter criteria
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()
    
    # Build query with optional filters
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if date_from is not None:
        query += " AND date >= ?"
        params.append(date_from)
    
    if date_to is not None:
        query += " AND date <= ?"
        params.append(date_to)
    
    if category is not None:
        query += " AND category = ?"
        params.append(category)
    
    if direction is not None:
        query += " AND direction = ?"
        params.append(direction)
    
    # Order by date DESC, then time DESC (handling NULL times)
    # SQLite treats NULL as smallest value, so DESC naturally puts NULL last
    query += " ORDER BY date DESC, time DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Convert rows to dictionaries
    transactions = []
    for row in rows:
        transactions.append({
            'transaction_id': row['transaction_id'],
            'date': row['date'],
            'time': row['time'],
            'description_raw': row['description_raw'],
            'merchant_normalized': row['merchant_normalized'],
            'amount': row['amount'],
            'direction': row['direction'],
            'category': row['category'],
            'balance_after': row['balance_after'],
            'source_bank': row['source_bank']
        })
    
    return transactions


def clear_transactions() -> None:
    """
    Delete all transactions from the database.
    
    Used when loading new data (sample or uploaded statement).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transactions")
    
    conn.commit()
    conn.close()
