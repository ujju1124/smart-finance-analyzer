import Plot from 'react-plotly.js';

/**
 * CategoryBreakdownChart
 *
 * Props:
 *   data    — { categories: string[], amounts: number[], percentages: number[] }
 *   insight — string, one-sentence AI insight
 */
function CategoryBreakdownChart({ data, insight }) {
  const categories = data?.categories ?? [];
  const amounts = data?.amounts ?? [];
  
  // If no data, show message
  if (!categories.length || !amounts.length) {
    return (
      <div className="chart-card">
        <h2 className="chart-card__title">Spending by Category</h2>
        <p style={{ padding: '2rem', textAlign: 'center', color: '#6b6375' }}>
          No category data available
        </p>
        {insight && <p className="chart-card__insight">{insight}</p>}
      </div>
    );
  }

  return (
    <div className="chart-card">
      <h2 className="chart-card__title">Spending by Category</h2>
      <Plot
        data={[
          {
            type: 'pie',
            labels: categories,
            values: amounts,
            hovertemplate: '<b>%{label}</b><br>NPR %{value:,.0f}<br>%{percent}<extra></extra>',
            textinfo: 'label+percent',
            textposition: 'outside',
            automargin: true,
          },
        ]}
        layout={{
          autosize: true,
          margin: { t: 16, r: 16, b: 16, l: 16 },
          paper_bgcolor: 'transparent',
          showlegend: false,
          font: { family: 'system-ui, sans-serif', size: 12, color: '#6b6375' },
        }}
        useResizeHandler
        style={{ width: '100%', height: '320px' }}
        config={{ displayModeBar: false, responsive: true }}
      />
      {insight && <p className="chart-card__insight">{insight}</p>}
    </div>
  );
}

export default CategoryBreakdownChart;
