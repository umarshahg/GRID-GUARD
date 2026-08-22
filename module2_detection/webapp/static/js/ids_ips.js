// webapp/static/js/ids_ips.js
// Polls Module 3's response log and renders it into the table + tier cards.

const TIER_COLOR_VAR = {
    1: "var(--status-normal)",
    2: "var(--status-alert)",
    3: "var(--status-ratelimit)",
    4: "var(--accent-red)",
};

async function loadResponseLog() {
    const tbody = document.getElementById('ids-ips-table-body');
    const limit = document.getElementById('log-count-select')?.value || 50;

    try {
        const res = await fetch(`/api/response-log?limit=${limit}`);
        const data = await res.json();

        if (!data.actions || data.actions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:24px;">No responses logged yet.</td></tr>';
        } else {
            tbody.innerHTML = data.actions.map(a => `
                <tr>
                    <td>${a.meter_id}</td>
                    <td>${a.risk_score !== null && a.risk_score !== undefined ? a.risk_score.toFixed(2) + '%' : '—'}</td>
                    <td><span style="color:${TIER_COLOR_VAR[a.tier] || 'var(--text-secondary)'}; font-weight:600;">Tier ${a.tier ?? '?'}</span></td>
                    <td>${a.action_type}</td>
                    <td style="color:var(--text-secondary); font-size:0.8rem;">${a.description || ''}</td>
                    <td style="font-family:'Source Code Pro',monospace; font-size:0.75rem; color:var(--text-muted);">
                        ${a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="color:var(--accent-red);">Error loading response log: ${e}</td></tr>`;
    }
}

async function loadTierCounts() {
    try {
        const res = await fetch('/api/response-counts');
        const data = await res.json();
        const counts = data.counts || {};

        document.getElementById('count-tier-1').textContent = counts.LOG || 0;
        document.getElementById('count-tier-2').textContent = counts.ALERT || 0;
        document.getElementById('count-tier-3').textContent = counts.RATE_LIMIT || 0;
        document.getElementById('count-tier-4').textContent = counts.FULL_ISOLATION || 0;
    } catch (e) {
        console.error('Error loading tier counts:', e);
    }
}

function refreshAll() {
    loadResponseLog();
    loadTierCounts();
}

document.getElementById('refresh-log-btn')?.addEventListener('click', refreshAll);
document.getElementById('log-count-select')?.addEventListener('change', refreshAll);

refreshAll();
setInterval(refreshAll, 5000);  // auto-refresh every 5s
