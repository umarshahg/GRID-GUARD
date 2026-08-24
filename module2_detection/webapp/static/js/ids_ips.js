// webapp/static/js/ids_ips.js
// Polls Module 3's response log and renders it into the table + tier cards.


function statusBadge(sent) {
    if (sent === true) {
        return '<span style="color:var(--status-normal); font-weight:600;">Sent</span>';
    } else if (sent === false) {
        return '<span style="color:var(--accent-red); font-weight:600;">Failed</span>';
    }
    return '<span style="color:var(--text-muted);">Not attempted</span>';
}

async function loadDeliveryLog() {
    try {
        const res = await fetch('/api/response-log?limit=100');
        const data = await res.json();
        const tbody = document.getElementById('delivery-log-table-body');

        const deliveryRows = (data.actions || []).filter(
            a => a.email_sent !== null || a.webhook_sent !== null
        );

        if (deliveryRows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:24px;">No delivery attempts yet.</td></tr>';
        } else {
            tbody.innerHTML = deliveryRows.map(a => `
                <tr>
                    <td>${a.meter_id}</td>
                    <td>${a.risk_score !== null && a.risk_score !== undefined ? a.risk_score.toFixed(2) + '%' : '—'}</td>
                    <td>${statusBadge(a.email_sent)}</td>
                    <td>${statusBadge(a.webhook_sent)}</td>
                    <td style="font-family:'Source Code Pro',monospace; font-size:0.75rem; color:var(--text-muted);">
                        ${a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Error loading delivery log:', e);
    }
}

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


async function loadSystemMetrics() {
    try {
        const res = await fetch('/api/module3/system-metrics');
        const data = await res.json();
        const m = data.metrics || {};

        document.getElementById('sys-total-meters').textContent = m.total_meters ?? '—';
        document.getElementById('sys-avg-risk').textContent =
            m.average_risk_score !== undefined ? (m.average_risk_score * 100).toFixed(1) + '%' : '—';
        document.getElementById('sys-critical-count').textContent = m.critical_count ?? '—';
        document.getElementById('sys-isolated-count').textContent = m.isolation_count ?? '—';
    } catch (e) {
        console.error('Error loading system metrics:', e);
    }
}


function firewallStatusBadge(applied) {
    if (applied === true) {
        return '<span style="color:var(--status-normal); font-weight:600;">Real rule active</span>';
    } else if (applied === false) {
        return '<span style="color:var(--text-muted);">Simulated only</span>';
    }
    return '<span style="color:var(--text-muted);">—</span>';
}

async function loadRateLimits() {
    try {
        const res = await fetch('/api/response-log?limit=100');
        const data = await res.json();
        const tbody = document.getElementById('rate-limit-table-body');

        const rateLimitRows = (data.actions || []).filter(
            a => a.action_type === 'RATE_LIMIT'
        );

        if (rateLimitRows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:24px;">No rate limits applied yet.</td></tr>';
        } else {
            tbody.innerHTML = rateLimitRows.map(a => `
                <tr>
                    <td>${a.meter_id}</td>
                    <td>${a.risk_score !== null && a.risk_score !== undefined ? a.risk_score.toFixed(2) + '%' : '—'}</td>
                    <td style="font-family:'Source Code Pro',monospace;">${a.rate_limit_ip || '—'}</td>
                    <td>${firewallStatusBadge(a.rate_limit_applied)}</td>
                    <td style="font-family:'Source Code Pro',monospace; font-size:0.75rem; color:var(--text-muted);">
                        ${a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Error loading rate limits:', e);
    }
}

function refreshAll() {
    loadResponseLog();
    loadTierCounts();
    loadSystemMetrics();
    loadDeliveryLog();
    loadRateLimits();
}

document.getElementById('refresh-log-btn')?.addEventListener('click', refreshAll);
document.getElementById('log-count-select')?.addEventListener('change', refreshAll);

refreshAll();
setInterval(refreshAll, 5000);  // auto-refresh every 5s
// Live WebSocket push — new responses appear instantly instead of
// waiting for the next poll
const socket = io();

socket.on("connect", () => {
    console.log("[WebSocket] Connected to live response feed");
});

socket.on("new_response", (data) => {
    console.log("[WebSocket] New response received:", data);
    refreshAll();  // simplest safe approach: just re-fetch everything
});

socket.on("disconnect", () => {
    console.log("[WebSocket] Disconnected — falling back to polling only");
});
