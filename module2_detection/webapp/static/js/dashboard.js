// webapp/static/js/dashboard.js
// ─────────────────────────────────────────────────────────────
// Dashboard page — loads summary stats, charts, scan button
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {

  // ── Chart.js global defaults ──────────────────────────────
  Chart.defaults.color          = '#7a9bb5';
  Chart.defaults.borderColor    = '#1a3a52';
  Chart.defaults.font.family    = "'Source Code Pro', monospace";
  Chart.defaults.font.size      = 11;

  let histChart  = null;
  let donutChart = null;

  // ── Helpers ───────────────────────────────────────────────
  const fmt = (v, suffix='') =>
    v === null || v === undefined || v === '—'
      ? '—'
      : `${Number(v).toLocaleString()}${suffix}`;

  const pct = v =>
    v === null || v === undefined ? '—' : `${Number(v).toFixed(2)}%`;

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  const getRiskClass = score => {
    if (score < 60)  return 'low';
    if (score < 80)  return 'medium';
    if (score < 95)  return 'high';
    return 'critical';
  };

  // ── Load system status ────────────────────────────────────
  async function loadStatus() {
    try {
      const res  = await fetch('/api/status');
      const data = await res.json();
      const dot  = document.getElementById('system-dot');
      const txt  = document.getElementById('system-status-text');
      if (data.models_loaded) {
        if (dot) { dot.classList.remove('offline'); }
        if (txt) txt.textContent = 'System Online';
      } else {
        if (dot) dot.classList.add('offline');
        if (txt) txt.textContent = 'Models Offline';
      }
    } catch {
      const txt = document.getElementById('system-status-text');
      if (txt) txt.textContent = 'Connection Error';
    }
  }

  // ── Load summary and populate everything ─────────────────
  async function loadSummary() {
    try {
      const res  = await fetch('/api/summary');
      const d    = await res.json();

      // Stat cards
      set('total-flows',    fmt(d.total_flows));
      set('total-normal',   fmt(d.total_normal));
      set('total-botnet',   fmt(d.total_botnet));
      set('detection-rate', pct(d.detection_rate));
      set('fpr',            pct(d.fpr));
      set('f1-score',       d.f1_score ? (d.f1_score / 100).toFixed(4) : '—');

      // Metrics panel
      set('m-accuracy',  pct(d.accuracy));
      set('m-det-rate',  pct(d.detection_rate));
      set('m-fpr',       pct(d.fpr));
      set('m-f1',        d.f1_score ? (d.f1_score / 100).toFixed(4) : '—');

      // Confusion matrix
      set('cm-tn', fmt(d.tn));
      set('cm-fp', fmt(d.fp));
      set('cm-fn', fmt(d.fn));
      set('cm-tp', fmt(d.tp));

      // Sidebar alert badge
      const badge = document.getElementById('sb-alert-count');
      if (badge) badge.textContent = fmt(d.total_botnet);

      // Model status dots
      const models = d.models_loaded || {};
      const dotMap = {
        'dot-if':  models.isolation_forest,
        'dot-svm': models.one_class_svm,
        'dot-rf':  models.random_forest,
        'dot-xgb': models.xgboost,
      };
      Object.entries(dotMap).forEach(([id, ok]) => {
        const el = document.getElementById(id);
        if (el) {
          if (!ok) el.classList.add('offline');
          else     el.classList.remove('offline');
        }
      });

      // Tier distribution
      const tiers = d.tier_counts || {};
      const total = d.total_flows || 1;
      [1,2,3,4].forEach(t => {
        const count = tiers[t] || 0;
        const pctW  = Math.round(count / total * 100);
        const bar   = document.getElementById(`tier-bar-${t}`);
        const cnt   = document.getElementById(`tier-count-${t}`);
        if (bar) bar.style.width = `${pctW}%`;
        if (cnt) cnt.textContent  = fmt(count);
      });

      // Histogram chart
      if (d.histogram && d.histogram.labels) {
        renderHistogram(d.histogram.labels, d.histogram.values);
      }

      // Donut chart
      renderDonut(d.total_normal || 0, d.total_botnet || 0);

    } catch (e) {
      console.error('Summary load error:', e);
    }
  }

  // ── Histogram chart ───────────────────────────────────────
  function renderHistogram(labels, values) {
    const ctx = document.getElementById('histogram-chart');
    if (!ctx) return;

    if (histChart) histChart.destroy();

    // Color bars by risk level
    const colors = labels.map(label => {
      const mid = parseInt(label.split('-')[0]);
      if (mid < 60)  return 'rgba(0,230,118,0.7)';
      if (mid < 80)  return 'rgba(255,179,0,0.7)';
      if (mid < 95)  return 'rgba(255,112,67,0.7)';
      return 'rgba(255,71,87,0.7)';
    });

    histChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Flows',
          data:   values,
          backgroundColor: colors,
          borderColor:     colors.map(c => c.replace('0.7','1')),
          borderWidth: 1,
          borderRadius: 3,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0d1a26',
            borderColor:     '#1a3a52',
            borderWidth:     1,
            titleColor:      '#00c6ff',
            bodyColor:       '#7a9bb5',
            callbacks: {
              title: items => `Risk: ${items[0].label}%`,
              label: item  => ` Flows: ${item.raw.toLocaleString()}`,
            }
          }
        },
        scales: {
          x: {
            grid:  { color: 'rgba(26,58,82,0.4)' },
            ticks: { maxRotation: 45, font: { size: 9 } }
          },
          y: {
            grid:  { color: 'rgba(26,58,82,0.4)' },
            ticks: { font: { size: 10 } }
          }
        }
      }
    });
  }

  // ── Donut chart ───────────────────────────────────────────
  function renderDonut(normal, botnet) {
    const ctx = document.getElementById('donut-chart');
    if (!ctx) return;

    if (donutChart) donutChart.destroy();

    const total   = normal + botnet || 1;
    const normPct = Math.round(normal / total * 100);

    donutChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels:   ['Normal', 'Botnet'],
        datasets: [{
          data:            [normal, botnet],
          backgroundColor: ['rgba(0,230,118,0.8)', 'rgba(255,71,87,0.8)'],
          borderColor:     ['#00e676', '#ff4757'],
          borderWidth:     2,
          hoverOffset:     6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0d1a26',
            borderColor:     '#1a3a52',
            borderWidth:     1,
            titleColor:      '#00c6ff',
            bodyColor:       '#7a9bb5',
          }
        }
      },
      plugins: [{
        id: 'center-text',
        beforeDraw(chart) {
          const { ctx, chartArea: { width, height, left, top } } = chart;
          ctx.save();
          ctx.font         = "bold 28px 'Rajdhani', sans-serif";
          ctx.fillStyle    = '#e8f4fd';
          ctx.textAlign    = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${normPct}%`, left + width/2, top + height/2 - 8);
          ctx.font      = "11px 'Source Code Pro', monospace";
          ctx.fillStyle = '#7a9bb5';
          ctx.fillText('Legitimate', left + width/2, top + height/2 + 16);
          ctx.restore();
        }
      }]
    });
  }

  // ── Scan Meter ────────────────────────────────────────────
  const scanBtn = document.getElementById('scan-btn');
  if (scanBtn) {
    scanBtn.addEventListener('click', async () => {
      scanBtn.disabled    = true;
      scanBtn.textContent = 'Scanning...';

      try {
        const res  = await fetch('/api/scan', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({})
        });
        const d = await res.json();

        const panel  = document.getElementById('scan-result');
        const riskCl = getRiskClass(d.risk_score);

        set('scan-meter-id', d.meter_id || '—');
        set('scan-risk',     `${d.risk_score}%`);
        set('scan-tier',     `Tier ${d.tier}`);
        set('scan-action',   d.action || '—');
        set('scan-rf',       `${d.rf_score}%`);

        const riskEl  = document.getElementById('scan-risk');
        const statEl  = document.getElementById('scan-status');

        if (riskEl) {
          riskEl.className = `scan-risk-score ${riskCl}`;
        }

        if (statEl) {
          statEl.textContent = d.status || '—';
          statEl.className   = `label-pill ${(d.status||'').toLowerCase()}`;
        }

        if (panel) panel.classList.add('visible');

      } catch (e) {
        console.error('Scan error:', e);
      } finally {
        scanBtn.disabled    = false;
        scanBtn.innerHTML   = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Scan Meter`;
      }
    });
  }

  // ── Init ──────────────────────────────────────────────────
  loadStatus();
  loadSummary();

  // Auto-refresh every 60 seconds
  setInterval(() => {
    loadStatus();
    loadSummary();
  }, 60000);

});
