import { useState, useEffect } from 'react';
import { getAnalytics } from '../api/client.js';
import DayOfWeekChart from './charts/DayOfWeekChart.jsx';
import MonthlyTrendChart from './charts/MonthlyTrendChart.jsx';
import CategoryBreakdownChart from './charts/CategoryBreakdownChart.jsx';
import AnomalyChart from './charts/AnomalyChart.jsx';
import TransactionsTimelineChart from './charts/TransactionsTimelineChart.jsx';
import TransactionSummary from './TransactionSummary.jsx';
import ApiKeyPrompt from './ApiKeyPrompt.jsx';
import './Dashboard.css';

/**
 * Dashboard
 *
 * Props:
 *   transactionCount — number of loaded transactions (displayed in header)
 *   onReset          — callback to return to the upload screen
 *   isDemoMode       — whether we're in demo mode (loads from sessionStorage instead of API)
 *
 * Fetches all analytics endpoints on mount (or loads from demo data).
 * Each chart shows a loading spinner while its request is in-flight and 
 * an error message on failure.
 */
function Dashboard({ transactionCount, onReset, isDemoMode = false, showChat = false, onToggleChat }) {
  const [charts, setCharts] = useState({
    'day-of-week':         { loading: true, error: null, data: null, insight: '' },
    'monthly-trend':       { loading: true, error: null, data: null, insight: '' },
    'category-breakdown':  { loading: true, error: null, data: null, insight: '' },
    'transactions-timeline': { loading: true, error: null, data: null, insight: '' },
    anomalies:             { loading: true, error: null, data: null, insight: '' },
  });
  const [showApiKeyPrompt, setShowApiKeyPrompt] = useState(false);
  const [userApiKey, setUserApiKey] = useState(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);

  useEffect(() => {
    if (isDemoMode) {
      loadDemoData();
    } else {
      loadAllCharts();
    }
  }, [isDemoMode]);

  function loadDemoData() {
    try {
      const demoJson = sessionStorage.getItem('demoAnalysis');
      if (!demoJson) {
        throw new Error('Demo data not found');
      }

      const demoData = JSON.parse(demoJson);
      const { analytics, insights } = demoData;

      // The new demo data structure matches the backend API format exactly
      // No transformation needed - just use the data directly
      
      const demoCharts = {
        'day-of-week': {
          loading: false,
          error: null,
          data: analytics.day_of_week,
          insight: insights.day_of_week
        },
        'monthly-trend': {
          loading: false,
          error: null,
          data: analytics.monthly_trend,
          insight: insights.monthly_trend
        },
        'category-breakdown': {
          loading: false,
          error: null,
          data: analytics.category_breakdown,
          insight: insights.category_breakdown
        },
        'transactions-timeline': {
          loading: false,
          error: null,
          data: analytics.transactions_timeline,
          insight: insights.transactions_timeline
        },
        'anomalies': {
          loading: false,
          error: null,
          data: analytics.anomalies,
          insight: insights.anomalies
        }
      };

      setCharts(demoCharts);
    } catch (err) {
      console.error('Failed to load demo data:', err);
      // Set error state for all charts
      const errorCharts = {};
      Object.keys(charts).forEach(pattern => {
        errorCharts[pattern] = {
          loading: false,
          error: 'Failed to load demo data',
          data: null,
          insight: ''
        };
      });
      setCharts(errorCharts);
    }
  }

  function loadAllCharts(apiKey = null) {
    const patterns = ['day-of-week', 'monthly-trend', 'category-breakdown', 'transactions-timeline', 'anomalies'];

    patterns.forEach((pattern) => {
      getAnalytics(pattern, apiKey)
        .then(({ data, insight }) => {
          setCharts((prev) => ({
            ...prev,
            [pattern]: { loading: false, error: null, data, insight: insight ?? '' },
          }));
        })
        .catch((err) => {
          // If rate limit (429), show API key prompt instead of error
          if (err.status === 429) {
            setShowApiKeyPrompt(true);
            setCharts((prev) => ({
              ...prev,
              [pattern]: {
                loading: false,
                error: 'Rate limit reached',
                data: null,
                insight: '',
              },
            }));
          } else {
            setCharts((prev) => ({
              ...prev,
              [pattern]: {
                loading: false,
                error: err.message || 'Failed to load chart data.',
                data: null,
                insight: '',
              },
            }));
          }
        });
    });
  }

  function handleApiKeySubmit(apiKey) {
    setUserApiKey(apiKey);
    setShowApiKeyPrompt(false);
    // Reload all charts with the new API key
    loadAllCharts(apiKey);
  }

  function handleApiKeyDismiss() {
    setShowApiKeyPrompt(false);
  }

  function renderChart(pattern, ChartComponent) {
    const { loading, error, data, insight } = charts[pattern];

    if (loading) {
      return (
        <div className="chart-card chart-card--loading" aria-label="Loading chart…">
          <span className="dashboard__spinner" aria-hidden="true" />
          <span className="dashboard__spinner-label">Loading…</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="chart-card chart-card--error" role="alert">
          <p className="chart-card__error-msg">⚠ {error}</p>
        </div>
      );
    }

    return <ChartComponent data={data} insight={insight} />;
  }

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <div className="dashboard__header-text">
          <h1 className="dashboard__title">Your Spending Analysis</h1>
          <p className="dashboard__subtitle">
            {transactionCount} transaction{transactionCount !== 1 ? 's' : ''} analyzed
          </p>
        </div>
        <div className="dashboard__header-actions">
          {isDemoMode && (
            <button
              type="button"
              className="dashboard__action-btn"
              onClick={() => setShowPdfViewer(!showPdfViewer)}
            >
              {showPdfViewer ? '📊 View Charts' : '📄 View Demo PDF'}
            </button>
          )}
          {onToggleChat && (
            <button
              type="button"
              className="dashboard__action-btn"
              onClick={onToggleChat}
            >
              {showChat ? '📊 Hide Chat' : '💬 Ask Questions'}
            </button>
          )}
          <button
            type="button"
            className="dashboard__reset-btn"
            onClick={onReset}
          >
            ← Load different data
          </button>
        </div>
      </div>

      {showPdfViewer && isDemoMode ? (
        <div className="dashboard__pdf-viewer">
          <iframe
            src="/demo_bank_statement.pdf"
            title="Demo Bank Statement PDF"
            style={{
              width: '100%',
              height: '80vh',
              border: '1px solid var(--border)',
              borderRadius: '10px'
            }}
          />
        </div>
      ) : (
        <>
          {/* Transaction Summary - Textual overview (REMOVED to save space) */}
          {/* <TransactionSummary isDemoMode={isDemoMode} /> */}

          <div className="dashboard__grid">
        {/* Full-width timeline chart at the top */}
        <div className="dashboard__cell dashboard__cell--full">
          {renderChart('transactions-timeline', TransactionsTimelineChart)}
        </div>
        
        {/* 2x2 grid for other charts */}
        <div className="dashboard__cell">
          {renderChart('day-of-week', DayOfWeekChart)}
        </div>
        <div className="dashboard__cell">
          {renderChart('monthly-trend', MonthlyTrendChart)}
        </div>
        <div className="dashboard__cell">
          {renderChart('category-breakdown', CategoryBreakdownChart)}
        </div>
        <div className="dashboard__cell">
          {renderChart('anomalies', AnomalyChart)}
        </div>
      </div>
      </>
      )}

      {/* User API key indicator */}
      {userApiKey && (
        <div className="dashboard__api-key-active" role="status">
          ✓ Using your API key
        </div>
      )}

      {/* API key prompt modal */}
      {showApiKeyPrompt && (
        <ApiKeyPrompt
          onSubmit={handleApiKeySubmit}
          onDismiss={handleApiKeyDismiss}
        />
      )}
    </div>
  );
}

export default Dashboard;
