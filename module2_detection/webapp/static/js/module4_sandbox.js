
function updateSandboxStatusPill(activeCount) {
    const statusText = document.getElementById('sandbox-status-text');
    const statusDot = document.getElementById('sandbox-dot');
    if (statusText) {
        statusText.textContent = `${activeCount} Active Isolation${activeCount === 1 ? '' : 's'}`;
    }
    if (statusDot) {
        statusDot.style.background = activeCount > 0 ? 'var(--accent-red)' : 'var(--status-normal)';
    }
}

// Module 4: Sandbox Environment Dashboard

let selectedMeterForRelease = null;

function loadQuarantinedMeters() {
  fetch('/api/module4/quarantined-meters')
    .then(r => r.json())
    .then(meters => {
      const tbody = document.getElementById('quarantine-table-body');
      if (meters.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">No quarantined meters</td></tr>';
        return;
      }
      
      tbody.innerHTML = meters.map(m => `
        <tr>
          <td><code>${m.meter_id}</code></td>
          <td>${m.ip_address}</td>
          <td><span style="background:var(--accent-red); color:white; padding:4px 8px; border-radius:4px; font-size:0.75rem;">${m.state}</span></td>
          <td><span style="background:var(--bg-secondary); padding:2px 6px; border-radius:3px; font-size:0.75rem;">Active</span></td>
          <td><span style="background:var(--bg-secondary); padding:2px 6px; border-radius:3px; font-size:0.75rem;">Capturing</span></td>
          <td>
            <button class="btn btn-primary" style="padding:4px 8px; font-size:0.75rem;" onclick="openReleaseModal('${m.meter_id}')">Release</button>
          </td>
        </tr>
      `).join('');
    })
    .catch(e => console.error('Failed to load meters:', e));
}

function loadStats() {
  fetch('/api/module4/stats')
    .then(r => r.json())
    .then(data => {
      document.getElementById('stat-isolation-count').textContent = data.isolation_count;
      document.getElementById('stat-dnat-count').textContent = data.dnat_count;
      document.getElementById('stat-pcap-count').textContent = data.pcap_count;
      document.getElementById('stat-released-count').textContent = data.released_count;
      updateSandboxStatusPill(data.isolation_count);
    })
    .catch(e => console.error('Failed to load stats:', e));
}

function openReleaseModal(meterId) {
  selectedMeterForRelease = meterId;
  document.getElementById('release-modal-meter').textContent = `Meter: ${meterId}`;
  document.getElementById('release-notes').value = '';
  document.getElementById('release-modal').style.display = 'flex';
}

function closeReleaseModal() {
  document.getElementById('release-modal').style.display = 'none';
  selectedMeterForRelease = null;
}

function confirmRelease() {
  if (!selectedMeterForRelease) return;
  
  const notes = document.getElementById('release-notes').value;
  
  fetch(`/api/module4/release/${selectedMeterForRelease}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes })
  })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'released') {
        alert(`✅ Meter ${selectedMeterForRelease} released successfully`);
        closeReleaseModal();
        loadQuarantinedMeters();
        loadStats();
      } else {
        alert('❌ Release failed: ' + (data.error || 'Unknown error'));
      }
    })
    .catch(e => {
      alert('❌ Error: ' + e.message);
      console.error(e);
    });
}

// Load on page load
document.addEventListener('DOMContentLoaded', () => {
  loadQuarantinedMeters();
  loadStats();

  document.getElementById('refresh-sandbox-btn')?.addEventListener('click', () => {
    loadQuarantinedMeters();
    loadStats();
  });

  // Refresh every 10 seconds
  setInterval(loadQuarantinedMeters, 10000);
  setInterval(loadStats, 10000);
});
