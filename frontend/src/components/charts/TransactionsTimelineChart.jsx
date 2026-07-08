import Plot from 'react-plotly.js';

/**
 * TransactionsTimelineChart - Shows ALL transactions as individual points
 *
 * Props:
 *   data    — { transactions: [{date, time, amount, merchant, category, description, direction}, ...] }
 *   insight — string, one-sentence AI insight
 */
function TransactionsTimelineChart({ data, insight }) {
  const transactions = data.transactions ?? [];

  if (transactions.length === 0) {
    return (
      <div className="chart-card">
        <h2 className="chart-card__title">All Transactions Timeline</h2>
        <p style={{ padding: '2rem', textAlign: 'center', color: '#6b6375' }}>
          No transactions to display
        </p>
      </div>
    );
  }

  // Separate debits and credits
  const debits = transactions.filter((t) => t.direction === 'debit');
  const credits = transactions.filter((t) => t.direction === 'credit');

  // Create datetime strings for better x-axis spacing
  // If time is available, use it; otherwise add index-based offset for same-day transactions
  const createDateTime = (txn, index) => {
    if (txn.time && txn.time !== 'null' && txn.time !== '') {
      return `${txn.date} ${txn.time}`;
    }
    // For same-day transactions without time, add minute offsets to spread them out
    const minuteOffset = index * 2; // 2 minutes apart
    const hours = Math.floor(minuteOffset / 60);
    const minutes = minuteOffset % 60;
    return `${txn.date} ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
  };

  const traces = [
    {
      type: 'scatter',
      mode: 'markers',
      name: 'Spending (Debit)',
      x: debits.map((t, i) => createDateTime(t, i)),
      y: debits.map((t) => t.amount),
      text: debits.map((t) => `${t.merchant || 'Unknown'}<br>${t.category}<br>${t.description?.substring(0, 60) || ''}`),
      marker: { 
        color: '#ef4444', 
        size: 10,
        opacity: 0.7,
        line: { width: 1, color: '#991b1b' }
      },
      hovertemplate: '<b>%{x}</b><br>NPR %{y:,.2f} (Debit)<br>%{text}<extra></extra>',
    },
    {
      type: 'scatter',
      mode: 'markers',
      name: 'Income (Credit)',
      x: credits.map((t, i) => createDateTime(t, i + debits.length)),
      y: credits.map((t) => t.amount),
      text: credits.map((t) => `${t.merchant || 'Unknown'}<br>${t.category}<br>${t.description?.substring(0, 60) || ''}`),
      marker: { 
        color: '#10b981', 
        size: 10,
        opacity: 0.7,
        line: { width: 1, color: '#047857' }
      },
      hovertemplate: '<b>%{x}</b><br>NPR %{y:,.2f} (Credit)<br>%{text}<extra></extra>',
    },
  ];

  return (
    <div className="chart-card">
      <h2 className="chart-card__title">All Transactions Timeline</h2>
      <Plot
        data={traces}
        layout={{
          autosize: true,
          margin: { t: 16, r: 16, b: 80, l: 72 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { family: 'system-ui, sans-serif', size: 13, color: '#6b6375' },
          xaxis: { 
            tickfont: { size: 10 }, 
            gridcolor: '#e5e4e7',
            tickangle: -45,
            type: 'date'
          },
          yaxis: {
            tickprefix: 'NPR ',
            tickformat: ',.0f',
            gridcolor: '#e5e4e7',
          },
          legend: { orientation: 'h', y: -0.3 },
          hovermode: 'closest',
        }}
        useResizeHandler
        style={{ width: '100%', height: '380px' }}
        config={{ displayModeBar: false, responsive: true }}
      />
      {insight && <p className="chart-card__insight">{insight}</p>}
    </div>
  );
}

export default TransactionsTimelineChart;
