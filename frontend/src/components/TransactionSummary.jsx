import { useState, useEffect } from 'react';
import { getTransactions } from '../api/client.js';
import './TransactionSummary.css';

/**
 * TransactionSummary - Textual summary of loaded transactions
 *
 * Props:
 *   isDemoMode - whether we're in demo mode (loads from sessionStorage instead of API)
 *
 * Shows:
 * - Date range
 * - Total transactions (debits/credits breakdown)
 * - Largest debit and credit
 * - Top spending categories
 */
function TransactionSummary({ isDemoMode = false }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isDemoMode) {
      loadDemoSummary();
    } else {
      loadApiSummary();
    }
  }, [isDemoMode]);

  function loadDemoSummary() {
    try {
      const demoJson = sessionStorage.getItem('demoAnalysis');
      if (!demoJson) {
        throw new Error('Demo data not found');
      }

      const demoData = JSON.parse(demoJson);
      const transactions = demoData.transactions || [];
      const computed = computeSummary(transactions);
      setSummary(computed);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load demo summary:', err);
      setError('Failed to load demo summary');
      setLoading(false);
    }
  }

  function loadApiSummary() {
    getTransactions()
      .then((response) => {
        // getTransactions returns { transactions: Array, total_count: number }
        const transactions = response.transactions || [];
        const computed = computeSummary(transactions);
        setSummary(computed);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load transaction summary');
        setLoading(false);
      });
  }

  function computeSummary(transactions) {
    if (!transactions || transactions.length === 0) {
      return null;
    }

    // Date range
    const dates = transactions.map((t) => t.date).sort();
    const dateRange = dates.length > 0 
      ? dates[0] === dates[dates.length - 1]
        ? `${dates[0]}`
        : `${dates[0]} to ${dates[dates.length - 1]}`
      : 'N/A';

    // Debits and credits
    const debits = transactions.filter((t) => t.direction === 'debit');
    const credits = transactions.filter((t) => t.direction === 'credit');
    
    // Income transactions (only credits with "Income & Salary" category)
    const incomeTransactions = credits.filter((t) => t.category === 'Income & Salary');

    const totalDebits = debits.reduce((sum, t) => sum + t.amount, 0);
    const totalCredits = credits.reduce((sum, t) => sum + t.amount, 0);
    const totalIncome = incomeTransactions.reduce((sum, t) => sum + t.amount, 0);

    // Largest transactions
    const largestDebit = debits.length > 0 
      ? debits.reduce((max, t) => t.amount > max.amount ? t : max)
      : null;
    
    // Largest income (only from Income & Salary category, not all credits)
    const largestIncome = incomeTransactions.length > 0
      ? incomeTransactions.reduce((max, t) => t.amount > max.amount ? t : max)
      : null;

    // Top 3 spending categories
    const categoryTotals = {};
    debits.forEach((t) => {
      categoryTotals[t.category] = (categoryTotals[t.category] || 0) + t.amount;
    });
    const topCategories = Object.entries(categoryTotals)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([category, amount]) => ({ category, amount }));

    // Day of week distribution
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayCounts = {};
    transactions.forEach((t) => {
      const date = new Date(t.date);
      const dayName = dayNames[date.getDay()];
      dayCounts[dayName] = (dayCounts[dayName] || 0) + 1;
    });
    const sortedDays = Object.entries(dayCounts)
      .sort(([, a], [, b]) => b - a)
      .map(([day, count]) => `${day} (${count})`);

    return {
      dateRange,
      totalTransactions: transactions.length,
      debitsCount: debits.length,
      creditsCount: credits.length,
      totalDebits,
      totalIncome,  // Changed: now shows only Income & Salary, not all credits
      largestDebit,
      largestIncome,  // Changed: now shows largest income, not largest credit
      topCategories,
      dayDistribution: sortedDays.join(', '),
    };
  }

  if (loading) {
    return (
      <div className="transaction-summary transaction-summary--loading">
        <span className="summary__spinner" />
        <span>Loading summary...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="transaction-summary transaction-summary--error">
        ⚠ {error}
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="transaction-summary">
      <h2 className="summary__title">📊 Transaction Summary</h2>
      
      <div className="summary__grid">
        {/* Date Range */}
        <div className="summary__card">
          <div className="summary__label">Date Range</div>
          <div className="summary__value">{summary.dateRange}</div>
        </div>

        {/* Total Transactions */}
        <div className="summary__card">
          <div className="summary__label">Total Transactions</div>
          <div className="summary__value">{summary.totalTransactions}</div>
          <div className="summary__detail">
            {summary.debitsCount} debits, {summary.creditsCount} credits
          </div>
        </div>

        {/* Total Spending */}
        <div className="summary__card">
          <div className="summary__label">Total Spending</div>
          <div className="summary__value summary__value--negative">
            NPR {summary.totalDebits.toLocaleString('en-NP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        {/* Total Income */}
        <div className="summary__card">
          <div className="summary__label">Total Income</div>
          <div className="summary__value summary__value--positive">
            NPR {summary.totalIncome.toLocaleString('en-NP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="summary__details">
        {/* Day Distribution */}
        <div className="summary__row">
          <span className="summary__row-label">Day of Week:</span>
          <span className="summary__row-value">{summary.dayDistribution}</span>
        </div>

        {/* Largest Debit */}
        {summary.largestDebit && (
          <div className="summary__row">
            <span className="summary__row-label">Largest Expense:</span>
            <span className="summary__row-value">
              NPR {summary.largestDebit.amount.toLocaleString('en-NP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              {' '}- {summary.largestDebit.merchant_normalized || 'Unknown'}
              {' '}({summary.largestDebit.category})
            </span>
          </div>
        )}

        {/* Largest Income */}
        {summary.largestIncome && (
          <div className="summary__row">
            <span className="summary__row-label">Largest Income:</span>
            <span className="summary__row-value">
              NPR {summary.largestIncome.amount.toLocaleString('en-NP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              {' '}- {summary.largestIncome.merchant_normalized || 'Unknown'}
              {' '}({summary.largestIncome.category})
            </span>
          </div>
        )}

        {/* Top Categories */}
        {summary.topCategories.length > 0 && (
          <div className="summary__row">
            <span className="summary__row-label">Top Spending Categories:</span>
            <span className="summary__row-value">
              {summary.topCategories.map((cat, i) => (
                <span key={cat.category}>
                  {i > 0 && ' • '}
                  {cat.category} (NPR {cat.amount.toLocaleString('en-NP', { maximumFractionDigits: 0 })})
                </span>
              ))}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default TransactionSummary;
