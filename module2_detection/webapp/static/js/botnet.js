// webapp/static/js/botnet.js
// ─────────────────────────────────────────────────────────────
// Botnet Detection page — anomaly chart, feature importance,
// model weights display, detection results table
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {

  Chart.defaults.color       = '#7a9bb5';
  Chart.defaults.borderColor = '#1a3a52';
  Chart.defaults.font.family = "'Source Code Pro', monospace";
  Chart.defaults.font.size   = 11;

  let anomalyChart = null;

  // ── Helpers ───────────────────────────────────────────────
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  const fmt = v =>
    v === null || v === undefined ? '—'
    : Number(v).toLocaleString();

  const pct = v =>
    v === null || v === undefined ? '—' : `${Number(v).toFixed(2)}%`;

  const getRiskClass = score => {
    if (score < 60)  return 'low';
    if (score < 80)  return 'medium';
    if (score < 95)  return 'high';
    return 'critical';
  };

  // ── Load Summary Stats ────────────────────────────────────
  async function loadSummary() {
    try {
      const res = await fetch('/api/summary');
      const d   = await res.json();

      // Top metric cards
      set('b-accuracy', pct(d.accuracy));
      set('b-f1-sub',   `F1 Score: ${d.f1_score ? (d.f1_score/100).toFixed(4) : '—'}`);
      set('b-normal',   fmt(d.total_normal));
      set('b-botnet',   fmt(d.total_botnet));

      // Model status dot
      const dot = document.getElementById('model-dot');
      const txt = document.getElementById('model-status-text');
      const ml  = d.models_loaded || {};
      const allOk = ml.isolation_forest && ml.one_class_svm
                 && ml.random_forest    && ml.xgboost;
      if (dot) {
        if (allOk) dot.classList.remove('offline');
        else       dot.classList.add('offline');
      }
      if (txt) txt.textContent = allOk ? 'Model Status: Online' : 'Model Status: Degraded';

      // Anomaly timeline chart
      if (d.timeline && d.timeline.length) {
        renderAnomalyChart(d.timeline);
      }

    } catch (e) {
      console.error('Summary error:', e);
    }
  }

  // ── Load Feature Importance ───────────────────────────────
  async function loadFeatures() {
    try {
      const res = await fetch('/api/features');
      const d   = await res.json();

      const el = document.getElementById('b-feature-list');
      if (!el) return;

      if (!d.features || !d.features.length) {
        el.innerHTML = `<p style="color:var(--text-muted); font-size:0.8rem; font-family:'Source Code Pro',monospace;">No feature data available</p>`;
        return;
      }

      const maxScore = Math.max(...d.scores);

      el.innerHTML = d.features.map((f, i) => `
        <div class="feature-row">
          <span class="feature-name" title="${f}">${f}</span>
          <div class="feature-bar-wrap">
            <div class="feature-bar" style="width:${(d.scores[i] / maxScore * 100).toFixed(1)}%"></div>
          </div>
          <span class="feature-pct">${d.scores[i].toFixed(1)}%</span>
        </div>
      `).join('');

    } catch (e) {
      console.error('Features error:', e);
    }
  }

  // ── Anomaly Detection Timeline Chart ─────────────────────
  function renderAnomalyChart(timeline) {
    const ctx = document.getElementById('anomaly-chart');
    if (!ctx) return;

    if (anomalyChart) anomalyChart.destroy();

    const labels = timeline.map((_, i) => `T${i+1}`);

    // Normalize to 0-1 range for anomaly score display
    const maxVal = Math.max(...timeline);
    const norm   = timeline.map(v => (v / (maxVal || 1)).toFixed(3));

    // Color points by severity
    const pointColors = norm.map(v => {
      const n = parseFloat(v);
      if (n < 0.3)  return '#00e676';
      if (n < 0.6)  return '#ffb300';
      if (n < 0.85) return '#ff7043';
      return '#ff4757';
    });

    anomalyChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label:           'Anomaly Score',
          data:            norm,
          borderColor:     '#ff7043',
          backgroundColor: 'rgba(255,112,67,0.08)',
          borderWidth:     2,
          fill:            true,
          tension:         0.4,
          pointRadius:     3,
          pointBackgroundColor: pointColors,
          pointBorderColor:     pointColors,
          pointHoverRadius:     5,
        }]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0d1a26',
            borderColor:     '#1a3a52',
            borderWidth:     1,
            titleColor:      '#ff7043',
            bodyColor:       '#7a9bb5',
            callbacks: {
              label: item => ` Anomaly Score: ${item.raw}`,
            }
          },
          // Threshold line annotation drawn manually
          afterDraw: chart => {
            const { ctx: c, chartArea: { left, right, top, bottom }, scales } = chart;
            const y = scales.y.getPixelForValue(0.75);
            c.save();
            c.beginPath();
            c.moveTo(left, y);
            c.lineTo(right, y);
            c.strokeStyle = 'rgba(255,71,87,0.5)';
            c.lineWidth   = 1;
            c.setLineDash([6, 4]);
            c.stroke();
            c.fillStyle  = 'rgba(255,71,87,0.7)';
            c.font       = "10px 'Source Code Pro', monospace";
            c.fillText('Isolation Threshold', right - 130, y - 6);
            c.restore();
          }
        },
        scales: {
          x: {
            grid:  { color: 'rgba(26,58,82,0.3)' },
            ticks: { maxTicksLimit: 12, font: { size: 9 } }
          },
          y: {
            min:   0,
            max:   1,
            grid:  { color: 'rgba(26,58,82,0.3)' },
            ticks: {
              font:     { size: 10 },
              callback: v => v.toFixed(2),
            }
          }
        }
      }
    });
  }

  // ── Load Detection Results Table ──────────────────────────
  async function loadFlows(n = 50) {
    const tbody = document.getElementById('b-flows-table-body');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8">
      <div class="loading"><div class="spinner"></div><span>Scoring flows...</span></div>
    </td></tr>`;

    try {
      const res   = await fetch(`/api/flows?n=${n}`);
      const d     = await res.json();
      const flows = d.flows || [];

      if (!flows.length) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:24px; font-family:'Source Code Pro',monospace; font-size:0.8rem;">No flows scored</td></tr>`;
        return;
      }

      tbody.innerHTML = flows.map(f => {
        const rc      = getRiskClass(f.risk_score);
        const correct = f.predicted === f.actual;

        const tierLabels = {
          1: { label: 'T1 — LOG',     color: 'var(--tier-1)' },
          2: { label: 'T2 — ALERT',   color: 'var(--tier-2)' },
          3: { label: 'T3 — LIMIT',   color: 'var(--tier-3)' },
          4: { label: 'T4 — ISOLATE', color: 'var(--tier-4)' },
        };
        const tier = tierLabels[f.tier] || { label: `T${f.tier}`, color: 'var(--text-muted)' };

        return `
          <tr>
            <td style="font-family:'Source Code Pro',monospace; color:var(--accent-cyan);">${f.flow_id}</td>
            <td>
              <span class="risk-pill ${rc}">${f.risk_score}%</span>
            </td>
            <td>
              <span style="font-size:0.68rem; font-family:'Source Code Pro',monospace; color:${tier.color};">
                ${tier.label}
              </span>
            </td>
            <td style="font-size:0.72rem; color:var(--text-muted); max-width:160px; overflow:hidden; text-overflow:ellipsis;">
              ${f.action}
            </td>
            <td>
              <span class="label-pill ${f.predicted.toLowerCase()}">${f.predicted}</span>
            </td>
            <td>
              <span class="label-pill ${f.actual.toLowerCase()}">${f.actual}</span>
              ${!correct ? '<span style="color:var(--accent-red); font-size:0.65rem; margin-left:4px;">✗</span>' : '<span style="color:var(--accent-green); font-size:0.65rem; margin-left:4px;">✓</span>'}
            </td>
            <td style="color:var(--accent-amber); font-family:'Source Code Pro',monospace;">${f.rf_score}%</td>
            <td style="color:var(--accent-teal);  font-family:'Source Code Pro',monospace;">${f.if_score}%</td>
          </tr>
        `;
      }).join('');

    } catch (e) {
      console.error('Flows error:', e);
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--accent-red); padding:20px; font-size:0.8rem;">Failed to load detection results</td></tr>`;
    }
  }

  // ── Re-Score Button ───────────────────────────────────────
  const rescoreBtn = document.getElementById('rescore-btn');
  if (rescoreBtn) {
    rescoreBtn.addEventListener('click', async () => {
      rescoreBtn.disabled    = true;
      rescoreBtn.textContent = 'Scoring...';
      const n = parseInt(document.getElementById('flow-count-select')?.value || 50);
      await loadFlows(n);
      rescoreBtn.disabled  = false;
      rescoreBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Re-Score`;
    });
  }

  // ── Load Flows Button ─────────────────────────────────────
  const loadFlowsBtn = document.getElementById('load-flows-btn');
  if (loadFlowsBtn) {
    loadFlowsBtn.addEventListener('click', () => {
      const n = parseInt(document.getElementById('flow-count-select')?.value || 50);
      loadFlows(n);
    });
  }

  // ── Init ──────────────────────────────────────────────────
  loadSummary();
  loadFeatures();
  loadFlows(50);

  // Auto-refresh every 90 seconds
  setInterval(() => {
    loadSummary();
    loadFeatures();
  }, 90000);

});
