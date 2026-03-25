/*
  analytics.js fetches analytics dashboard data and renders charts.
*/

const analyticsEndpoint = '/api/analytics/dashboard/';

function initAnalytics() {
  const docsEl = document.getElementById('analytics-documents');
  const scoreEl = document.getElementById('analytics-score');
  const violationsEl = document.getElementById('analytics-violations');
  const risksEl = document.getElementById('analytics-risks');

  const violationsChartEl = document.getElementById('analytics-violations-chart');
  const risksChartEl = document.getElementById('analytics-risks-chart');
  const timeSeriesChartEl = document.getElementById('analytics-time-chart');
  const topViolationsChartEl = document.getElementById('analytics-top-violations-chart');

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

  const load = async () => {
    const resp = await fetch(analyticsEndpoint);
    if (!resp.ok) return;

    const data = await resp.json();

    if (docsEl) docsEl.innerText = data.total_documents || 0;
    if (scoreEl) scoreEl.innerText = Math.round(data.average_score || 0);
    if (violationsEl) violationsEl.innerText = data.violations_per_standard ? Object.values(data.violations_per_standard).reduce((a, b) => a + b, 0) : 0;
    if (risksEl) risksEl.innerText = data.risk_distribution ? Object.values(data.risk_distribution).reduce((a, b) => a + b, 0) : 0;
    const atcViolationsEl = document.getElementById('analytics-atc-violations');
    if (atcViolationsEl) atcViolationsEl.innerText = data.atc_violations || 0;

    const standardNames = data.violations_per_standard ? Object.keys(data.violations_per_standard) : [];
    const standardViolations = data.violations_per_standard ? Object.values(data.violations_per_standard) : [];

    const riskNames = data.risk_distribution ? Object.keys(data.risk_distribution) : [];
    const riskValues = data.risk_distribution ? Object.values(data.risk_distribution) : [];

    renderChart(violationsChartEl, standardNames, standardViolations, 'Violations', 'rgba(99, 102, 241, 0.75)');
    renderDoughnut(risksChartEl, riskNames, riskValues, ['rgba(34, 197, 94, 0.85)', 'rgba(245, 158, 11, 0.85)', 'rgba(239, 68, 68, 0.85)', 'rgba(6, 182, 212, 0.85)']);

    if (timeSeriesChartEl && Array.isArray(data.documents_over_time)) {
      const labels = data.documents_over_time.map((row) => row.date);
      const counts = data.documents_over_time.map((row) => row.count);
      const avgScores = data.documents_over_time.map((row) => row.average_score);

      new Chart(timeSeriesChartEl, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Documents',
              data: counts,
              borderColor: 'rgba(56, 189, 248, 0.85)',
              backgroundColor: 'rgba(56, 189, 248, 0.25)',
              tension: 0.35,
              yAxisID: 'y',
            },
            {
              label: 'Avg. Score',
              data: avgScores,
              borderColor: 'rgba(34, 197, 94, 0.85)',
              backgroundColor: 'rgba(34, 197, 94, 0.25)',
              tension: 0.35,
              yAxisID: 'y1',
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' },
          },
          scales: {
            y: {
              position: 'left',
              grid: { color: 'rgba(148, 163, 184, 0.2)' },
            },
            y1: {
              position: 'right',
              grid: { display: false },
              suggestedMin: 0,
              suggestedMax: 100,
            },
          },
        },
      });
    }

    if (topViolationsChartEl && Array.isArray(data.top_violations)) {
      const labels = data.top_violations.map((item) => item.standard);
      const values = data.top_violations.map((item) => item.count);

      renderChart(topViolationsChartEl, labels, values, 'Top Violations', 'rgba(248, 113, 113, 0.8)');
    }
  };

  load();
}

window.initAnalytics = initAnalytics;
