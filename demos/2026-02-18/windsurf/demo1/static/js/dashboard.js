function safePlot(elId, fig) {
  const el = document.getElementById(elId);
  if (!el) return;

  if (!fig || !fig.data) {
    el.innerHTML = '<div class="text-muted">No chart available.</div>';
    return;
  }

  Plotly.react(el, fig.data, fig.layout || {}, { responsive: true });
}

function setError(msg) {
  const box = document.getElementById('filterError');
  if (!box) return;

  if (!msg) {
    box.classList.add('d-none');
    box.textContent = '';
    return;
  }

  box.classList.remove('d-none');
  box.textContent = msg;
}

function getConditions() {
  const column = document.getElementById('filterColumn')?.value;
  const operator = document.getElementById('filterOperator')?.value;
  const value = document.getElementById('filterValue')?.value ?? '';

  if (!column || !operator || value.trim() === '') return [];
  return [{ column, operator, value }];
}

async function applyFilters({ clear = false } = {}) {
  setError(null);

  const histColumn = document.getElementById('histColumn')?.value;
  const barColumn = document.getElementById('barColumn')?.value;

  const payload = {
    conditions: clear ? [] : getConditions(),
    hist_column: histColumn,
    bar_column: barColumn
  };

  const res = await fetch('/api/apply_filters', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  if (!res.ok) {
    setError(data?.error || 'Failed to apply filter.');
    return;
  }

  document.getElementById('rowCount').textContent = data.row_count;
  document.getElementById('previewTable').innerHTML = data.preview_html;
  document.getElementById('statsTable').innerHTML = data.stats_html;

  safePlot('histChart', data.hist_fig);
  safePlot('barChart', data.bar_fig);
  safePlot('corrChart', data.corr_fig);
}

function init() {
  const initEl = document.getElementById('initialDashboardData');
  const histRaw = initEl?.dataset?.hist;
  const barRaw = initEl?.dataset?.bar;
  const corrRaw = initEl?.dataset?.corr;

  let histFig = null;
  let barFig = null;
  let corrFig = null;
  try {
    histFig = histRaw ? JSON.parse(histRaw) : null;
    barFig = barRaw ? JSON.parse(barRaw) : null;
    corrFig = corrRaw ? JSON.parse(corrRaw) : null;
  } catch (_e) {
    // If parsing fails, fall back to empty charts.
  }

  safePlot('histChart', histFig);
  safePlot('barChart', barFig);
  safePlot('corrChart', corrFig);

  document.getElementById('applyFilterBtn')?.addEventListener('click', () => applyFilters());
  document.getElementById('clearFilterBtn')?.addEventListener('click', () => {
    const input = document.getElementById('filterValue');
    if (input) input.value = '';
    applyFilters({ clear: true });
  });

  document.getElementById('histColumn')?.addEventListener('change', () => applyFilters());
  document.getElementById('barColumn')?.addEventListener('change', () => applyFilters());
}

document.addEventListener('DOMContentLoaded', init);
