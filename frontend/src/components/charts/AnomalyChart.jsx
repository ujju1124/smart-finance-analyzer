import Plot from 'react-plotly.js';

/**
 * AnomalyChart
 *
 * Props:
 *   data    — { daily_totals: [{date, amount, is_anomaly, merchant, description}, ...],
 *               threshold: number, method: string, anomaly_count: number }
 *   insight — string, one-sentence AI insight
 */
function AnomalyChart({ data, insight }) {
  const dailyTotals = data.daily_totals ?? [];
  const threshold = data.threshold ?? null;

  // Split into normal and anomaly series
  const normal = dailyTotals.filter((d) => !d.is_anomaly);
  const anomalies = dailyTotals.filter((d) => d.is_anomaly);

  // Threshold line spanning the full date range
  const allDates = dailyTotals.map((d) => d.date);

  const traces = [
    {
      type: 'scatter',
      mode: 'markers',
      name: 'Normal',
      x: normal.map((d) => d.date),
      y: normal.map((d) => d.amount),
      text: normal.map((d) => d.merchant || d.description || ''),
      marker: { color: '#3b82f6', size: 8 },
      hovertemplate: '<b>%{x}</b><br>NPR %{y:,.0f}<br>%{text}<extra></extra>',
    },
    {
      type: 'scatter',
      mode: 'markers',
      name: 'Anomaly',
      x: anomalies.map((d) => d.date),
      y: anomalies.map((d) => d.amount),
      text: anomalies.map((d) => d.merchant || d.description || ''),
      marker: { color: '#ef4444', size: 10, symbol: 'circle-open', line: { width: 2 } },
      hovertemplate: '<b>%{x}</b><br>NPR %{y:,.0f} ⚠ anomaly<br>%{text}<extra></extra>',
    },
  ];

  // Add threshold horizontal line if available
  if (threshold != null && allDates.length > 0) {
    const sortedDates = [...allDates].sort();
    traces.push({
      type: 'scatter',
      mode: 'lines',
      name: 'Threshold',
      x: [sortedDates[0], sortedDates[sortedDates.length - 1]],
      y: [threshold, threshold],
      line: { color: '#f59e0b', width: 1.5, dash: 'dash' },
      hoverinfo: 'skip',
    });
  }

  return (
    <div className="chart-card">
      <h2 className="chart-card__title">Transaction Spending Anomalies</h2>
      <Plot
        data={traces}
        layout={{
          autosize: true,
          margin: { t: 16, r: 16, b: 48, l: 72 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { family: 'system-ui, sans-serif', size: 13, color: '#6b6375' },
          xaxis: { tickfont: { size: 11 }, gridcolor: '#e5e4e7' },
          yaxis: {
            tickprefix: 'NPR ',
            tickformat: ',.0f',
            gridcolor: '#e5e4e7',
          },
          legend: { orientation: 'h', y: -0.15 },
        }}
        useResizeHandler
        style={{ width: '100%', height: '320px' }}
        config={{ displayModeBar: false, responsive: true }}
      />
      {insight && <p className="chart-card__insight">{insight}</p>}
    </div>
  );
}

export default AnomalyChart;
