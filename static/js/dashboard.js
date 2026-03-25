/*
  dashboard.js powers the dashboard landing page by rendering KPI cards and charts.
*/

const dashboardEndpoint = '/api/analytics/dashboard/';

function initDashboard() {
  const docCountEl = document.getElementById('stat-documents');
  const scoreEl = document.getElementById('stat-score');
  const violationsEl = document.getElementById('stat-noncompliant');
  const riskEl = document.getElementById('stat-risk');

  const scoreChartEl = document.getElementById('chart-score');
  const violationsChartEl = document.getElementById('chart-violations');

  const renderChart = (context, labels, values, label, color) => {
    if (!context) return null;
    return new Chart(context, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label,
            data: values,
            backgroundColor: color,
            borderRadius: 10,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            grid: { color: 'rgba(148, 163, 184, 0.2)' },
            beginAtZero: true,
          },
        },
      },
    });
  };

  const renderDoughnut = (context, labels, values, colors) => {
    if (!context) return null;
    return new Chart(context, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: colors,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
      },
    });
  };

  const messageEl = document.getElementById('dashboard-message');

  const recentAuditsTbody = document.getElementById('recent-audits-tbody');

  const renderRecentAudits = (audits = []) => {
    if (!recentAuditsTbody) return;

    if (!audits.length) {
      recentAuditsTbody.innerHTML =
        '<tr><td colspan="5" class="px-6 py-8 text-center text-gray-500">No recent audits found.</td></tr>';
      return;
    }

    recentAuditsTbody.innerHTML = '';

    audits.slice(0, 6).forEach((audit) => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-50 cursor-pointer';

      const name = (audit.document_name || 'Unknown').split('/').pop();
      const score = audit.score || 0;
      const status = score >= 80 ? 'Compliant' : score >= 50 ? 'Partial' : 'Non-compliant';

      tr.innerHTML = `
        <td class="px-6 py-4">${name}</td>
        <td class="px-6 py-4">${audit.standard_name || '-'}</td>
        <td class="px-6 py-4 font-semibold">${score}%</td>
        <td class="px-6 py-4"><span class="badge ${
          status === 'Compliant'
            ? 'badge--success'
            : status === 'Partial'
            ? 'badge--warning'
            : 'badge--danger'
        }">${status}</span></td>
        <td class="px-6 py-4">${
          audit.created_at ? new Date(audit.created_at).toLocaleDateString() : '-'
        }</td>
      `;

      recentAuditsTbody.appendChild(tr);
    });
  };

  const load = async () => {
    if (!window.Chart) {
      if (messageEl) {
        messageEl.textContent = 'Chart.js is not loaded; dashboard charts cannot be rendered.';
        messageEl.classList.remove('text-muted');
        messageEl.classList.add('text-danger');
      }
      return;
    }

    if (messageEl) {
      messageEl.textContent = 'Loading dashboard data…';
      messageEl.classList.remove('text-danger');
      messageEl.classList.add('text-muted');
    }

    const resp = await fetch(dashboardEndpoint);
    if (!resp.ok) {
      if (messageEl) {
        messageEl.textContent = 'Failed to load dashboard data.';
        messageEl.classList.add('text-danger');
      }
      return;
    }

    const data = await resp.json();

    const violationsPerStandard = data.violations_per_standard || {};
    const riskDistribution = data.risk_distribution || {};

    const standardsCount = Object.keys(violationsPerStandard).filter((k) => k).length;
    const riskCount = Object.values(riskDistribution).reduce((sum, c) => sum + (c || 0), 0);

    if (docCountEl) docCountEl.innerText = data.total_documents ?? 0;
    if (scoreEl) scoreEl.innerText = `${Math.round(data.average_score ?? 0)}%`;
    if (violationsEl) violationsEl.innerText = data.total_violations ?? 0;

    const riskLevel = data.risk_level || (riskCount > 0 ? 'Medium' : 'Low');
    if (riskEl) riskEl.innerText = riskLevel;

    if (scoreChartEl) {
      renderDoughnut(scoreChartEl, ['Average Score', 'Remaining'], [data.average_score ?? 0, 100 - (data.average_score ?? 0)], ['#38bdf8', 'rgba(148, 163, 184, 0.25)']);
    }

    if (violationsChartEl) {
      renderChart(
        violationsChartEl,
        Object.keys(violationsPerStandard).length ? Object.keys(violationsPerStandard) : ['No data'],
        Object.values(violationsPerStandard).length ? Object.values(violationsPerStandard) : [0],
        'Violations',
        'rgba(248, 113, 113, 0.8)'
      );
    }

    // Render recent audits list if available
    const recentAudits = data.recent_audits || data.audits || [];
    renderRecentAudits(recentAudits);

    if (messageEl) {
      messageEl.textContent = '';
    }
  };

  load();
}

window.initDashboard = initDashboard;
