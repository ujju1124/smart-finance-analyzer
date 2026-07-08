import Plot from 'react-plotly.js';

/**
 * MonthlyTrendChart
 *
 * Props:
 *   data    — { months: string[], amounts: number[], mom_changes: (number|null)[] }
 *   insight — string, one-sentence AI insight
 */
function MonthlyTrendChart({ data, insight }) {
  const months = data.months ?? [];
  const amounts = data.amounts ?? [];
  const momChanges = data.mom_changes ?? [];

  // Build hover text that includes MoM % change when available
  const hoverText = amounts.map((amt, i) => {
    const mom = momChanges[i];
    const momStr =
      mom != null
        ? `<br>MoM change: ${mom > 0 ? '+' : ''}${mom.toFixed(1)}%`
        : '';
    return `NPR ${amt.toLocaleString()}${momStr}`;
  });

  return (
    <div className="chart-card">
      <h2 className="chart-card__title">Monthly Spending Trend</h2>
      <Plot
        data={[
          {
            type: 'scatter',
            mode: 'lines+markers',
            x: months,
            y: amounts,
            line: { color: '#10b981', width: 2 },
            marker: { color: '#10b981', size: 7 },
            hovertext: hoverText,
            hovertemplate: '<b>%{x}</b><br>%{hovertext}<extra></extra>',
          },
        ]}
        layout={{
          autosize: true,
          margin: { t: 16, r: 16, b: 48, l: 72 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { family: 'system-ui, sans-serif', size: 13, color: '#6b6375' },
          xaxis: { tickfont: { size: 12 }, gridcolor: '#e5e4e7' },
          yaxis: {
            tickprefix: 'NPR ',
            tickformat: ',.0f',
            gridcolor: '#e5e4e7',
          },
        }}
        useResizeHandler
        style={{ width: '100%', height: '320px' }}
        config={{ displayModeBar: false, responsive: true }}
      />
      {insight && <p className="chart-card__insight">{insight}</p>}
    </div>
  );
}

export default MonthlyTrendChart;
