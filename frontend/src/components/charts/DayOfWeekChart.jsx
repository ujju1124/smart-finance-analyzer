import Plot from 'react-plotly.js';

/**
 * DayOfWeekChart
 *
 * Props:
 *   data    — { monday, tuesday, wednesday, thursday, friday, saturday, sunday,
 *               average_transactions_per_day }
 *   insight — string, one-sentence AI insight
 */
function DayOfWeekChart({ data, insight }) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  const amounts = keys.map((k) => data[k] ?? 0);

  return (
    <div className="chart-card">
      <h2 className="chart-card__title">Spending by Day of Week</h2>
      <Plot
        data={[
          {
            type: 'bar',
            x: days,
            y: amounts,
            marker: { color: '#3b82f6' },
            hovertemplate: '<b>%{x}</b><br>NPR %{y:,.0f}<extra></extra>',
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
            tickformat: ',',
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

export default DayOfWeekChart;
