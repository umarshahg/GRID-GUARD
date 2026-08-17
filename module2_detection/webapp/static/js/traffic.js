// webapp/static/js/traffic.js
// ─────────────────────────────────────────────────────────────
// Traffic Monitor page — loads traffic stats, protocol chart,
// feature list, and live flow table
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {

  Chart.defaults.color       = '#7a9bb5';
  Chart.defaults.borderColor = '#1a3a52';
  Chart.defaults.font.family = "'Source Code Pro', monospace";
  Chart.defaults.font.size   = 11;

  let protocolChart = null;

  // ── Helpers ───────────────────────────────────────────────
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  const fmt = (v, suffix='') =>
    v === null || v === undefined ? '—'
    : `${Number(v).toLocaleString()}${suffix}`;

  const getRiskClass = score => {
    if (score < 60)  return 'low';
    if (score < 80)  return 'medium';
    if (score < 95)  return 'high';
    return 'critical';
  };

  const getTierLabel = tier => {
    const map = {
      1: 'LOG ONLY',
      2: 'ALERT',
      3: 'RATE LIMIT',
      4: 'ISOLATE'
    };
    return map[tier] || '—';
  };

  // ── Load Traffic Stats ────────────────────────────────────
  async function loadTraffic() {
    try {
      const res = await fetch('/api/traffic');
      const d   = await res.json();

      set('t-total',       fmt(d.total_flows));
      set('t-normal',      fmt(d.normal_flows));
      set('t-botnet',      fmt(d.botnet_flows));
      set('t-normal-risk', d.normal_mean_risk !== undefined ? `${d.normal_mean_risk}%` : '—');
      set('t-botnet-risk', d.botnet_mean_risk !== undefined ? `${d.botnet_mean_risk}%` : '—');
      set('t-features',    d.feature_names ? d.feature_names.length : '—');

      // Feature list
      if (d.feature_names) {
        renderFeatureList(d.feature_names);
      }

      // Protocol chart
      if (d.protocol_timeline) {
        renderProtocolChart(d.protocol_timeline);
      }

    } catch (e) {
      console.error('Traffic load error:', e);
    }
  }

  // ── Protocol Distribution Chart ───────────────────────────
  function renderProtocolChart(timeline) {
    const ctx = document.getElementById('protocol-chart');
    if (!ctx) return;

    if (protocolChart) protocolChart.destroy();

    const labels = timeline.map(t => t.time);
    const dlms   = timeline.map(t => t.dlms);
    const mqtt   = timeline.map(t => t.mqtt);

    protocolChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label:           'DLMS/COSEM',
            data:            dlms,
            borderColor:     '#00c6ff',
            backgroundColor: 'rgba(0,198,255,0.08)',
            borderWidth:     2,
            fill:            true,
            tension:         0.4,
            pointRadius:     0,
            pointHoverRadius: 4,
          },
          {
            label:           'MQTT',
            data:            mqtt,
            borderColor:     '#00e5cc',
            backgroundColor: 'rgba(0,229,204,0.06)',
            borderWidth:     2,
            fill:            true,
            tension:         0.4,
            pointRadius:     0,
            pointHoverRadius: 4,
          }
        ]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display:  true,
            position: 'top',
            labels: {
              boxWidth:  10,
              padding:   16,
              color:     '#7a9bb5',
              font:      { size: 11 },
            }
          },
          tooltip: {
            backgroundColor: '#0d1a26',
            borderColor:     '#1a3a52',
            borderWidth:     1,
            titleColor:      '#00c6ff',
            bodyColor:       '#7a9bb5',
          }
        },
        scales: {
          x: {
            grid:  { color: 'rgba(26,58,82,0.4)' },
            ticks: { maxTicksLimit: 10, font: { size: 10 } }
          },
          y: {
            grid:  { color: 'rgba(26,58,82,0.4)' },
            ticks: { font: { size: 10 } },
            beginAtZero: true,
          }
        }
      }
    });
  }

  // ── Feature List ──────────────────────────────────────────
  function renderFeatureList(features) {
    const el = document.getElementById('feature-list');
    if (!el) return;

    el.innerHTML = features.map((f, i) => `
      <div class="feature-row">
        <span class="feature-name" title="${f}">${f}</span>
        <div class="feature-bar-wrap">
          <div class="feature-bar" style="width:${Math.max(20, 100 - i * 4)}%"></div>
        </div>
        <span class="feature-pct" style="color:var(--text-muted); font-size:0.65rem;">${i+1}</span>
      </div>
    `).join('');
  }

  // ── Load Flows Table ──────────────────────────────────────
  async function loadFlows(n = 30) {
    const tbody = document.getElementById('flows-table-body');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7">
      <div class="loading"><div class="spinner"></div><span>Loading flows...</span></div>
    </td></tr>`;

    try {
      const res = await fetch(`/api/flows?n=${n}`);
      const d   = await res.json();
      const flows = d.flows || [];

      if (!flows.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:20px; font-family:'Source Code Pro',monospace; font-size:0.8rem;">No flows available</td></tr>`;
        return;
      }

      tbody.innerHTML = flows.map(f => {
        const rc      = getRiskClass(f.risk_score);
        const correct = f.predicted === f.actual;
        return `
          <tr>
            <td>${f.flow_id}</td>
            <td>
              <span class="label-pill ${f.predicted.toLowerCase()}">${f.predicted}</span>
            </td>
            <td>
              <span class="label-pill ${f.actual.toLowerCase()}">${f.actual}</span>
            </td>
            <td>
              <span class="risk-pill ${rc}">${f.risk_score}%</span>
            </td>
            <td style="color:var(--accent-cyan);">${f.rf_score}%</td>
            <td style="color:var(--accent-teal);">${f.if_score}%</td>
            <td>
              <span style="font-size:0.68rem; font-family:'Source Code Pro',monospace; color:${correct ? 'var(--accent-green)' : 'var(--accent-red)'};">
                T${f.tier}
              </span>
            </td>
          </tr>
        `;
      }).join('');

    } catch (e) {
      console.error('Flows load error:', e);
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--accent-red); padding:20px; font-size:0.8rem;">Failed to load flows</td></tr>`;
    }
  }

  // ── Range Button (decorative — data is same) ──────────────
  window.setRange = (range) => {
    document.querySelectorAll('.btn-outline').forEach(b => {
      b.style.borderColor = '';
      b.style.color       = '';
    });
    event.target.style.borderColor = 'var(--accent-cyan)';
    event.target.style.color       = 'var(--accent-cyan)';
  };

  // ── Refresh Buttons ───────────────────────────────────────
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadTraffic();
      loadFlows(30);
    });
  }

  const refreshFlowsBtn = document.getElementById('refresh-flows-btn');
  if (refreshFlowsBtn) {
    refreshFlowsBtn.addEventListener('click', () => loadFlows(30));
  }

  // ── Init ──────────────────────────────────────────────────
  loadTraffic();
  loadFlows(30);

});
