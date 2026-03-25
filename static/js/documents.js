/*
  documents.js provides a simple UI for listing uploaded documents and deleting them.
*/

(function () {
  const documentsEndpoint = '/api/documents/';
  const standardsEndpoint = '/api/standards/';

  let currentPage = 1;
  let pageSize = 20;
  let totalPages = 1;
  let selectedStandard = '';
  let searchTerm = '';
  let selectedIds = new Set();

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const dt = new Date(dateString);
      return dt.toLocaleString();
    } catch (e) {
      return dateString;
    }
  };

  const showStatus = (message, type = 'info') => {
    const el = document.getElementById('documents-status');
    if (!el) return;
    
    let typeClass = 'bg-blue-50 text-blue-800 border-blue-200';
    if (type === 'success') typeClass = 'bg-green-50 text-green-800 border-green-200';
    if (type === 'danger') typeClass = 'bg-red-50 text-red-800 border-red-200';
    if (type === 'warning') typeClass = 'bg-yellow-50 text-yellow-800 border-yellow-200';
    
    el.innerHTML = `<div class="text-sm px-4 py-2 rounded border ${typeClass}">${message}</div>`;
  };

  const updateDeleteSelectedButton = () => {
    const btn = document.getElementById('delete-selected');
    if (!btn) return;
    btn.disabled = selectedIds.size === 0;
  };

  const updateSelectAllCheckbox = () => {
    const selectAll = document.getElementById('select-all-documents');
    if (!selectAll) return;
    const checkboxes = Array.from(document.querySelectorAll('.document-checkbox'));
    if (!checkboxes.length) {
      selectAll.checked = false;
      selectAll.indeterminate = false;
      return;
    }

    const checked = checkboxes.filter((cb) => cb.checked).length;
    selectAll.checked = checked === checkboxes.length;
    selectAll.indeterminate = checked > 0 && checked < checkboxes.length;
  };

  const buildRow = (doc) => {
    const tr = document.createElement('tr');
    tr.className = 'border-b border-gray-200 hover:bg-gray-50';

    const fileName = doc.file_name || doc.file || 'Unknown';
    const standard = doc.standard_name || doc.standard || '—';

    tr.innerHTML = `
      <td class="px-6 py-4">
        <input type="checkbox" class="document-checkbox w-4 h-4 rounded border-gray-300 cursor-pointer" data-doc-id="${doc.id}" />
      </td>
      <td class="px-6 py-4 text-sm text-gray-500">${doc.id}</td>
      <td class="px-6 py-4 text-sm text-gray-900 font-medium">${fileName}</td>
      <td class="px-6 py-4 text-sm text-gray-600">${standard}</td>
      <td class="px-6 py-4 text-sm text-gray-600">${formatDate(doc.uploaded_at)}</td>
      <td class="px-6 py-4 text-sm text-right flex justify-end gap-2">
        <button class="px-3 py-1.5 bg-sky-50 text-sky-600 rounded text-sm font-medium hover:bg-sky-100 transition-colors" data-doc-id="${doc.id}" data-action="view-analysis" title="${i18n.t('documents.analyze')}">
          <i class="fa-solid fa-chart-bar me-1"></i><span data-i18n="documents.analyze">Analyze</span>
        </button>
        <button class="px-3 py-1.5 bg-red-50 text-red-600 rounded text-sm font-medium hover:bg-red-100 transition-colors" data-doc-id="${doc.id}" data-action="delete">
          <i class="fa-solid fa-trash me-1"></i><span data-i18n="common.delete">Delete</span>
        </button>
      </td>
    `;

    const checkbox = tr.querySelector('.document-checkbox');
    if (checkbox) {
      checkbox.checked = selectedIds.has(String(doc.id));
      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          selectedIds.add(String(doc.id));
        } else {
          selectedIds.delete(String(doc.id));
        }
        updateDeleteSelectedButton();
        updateSelectAllCheckbox();
      });
    }

    const buttons = tr.querySelectorAll('button');
    buttons.forEach(button => {
      if (button.dataset.action === 'delete') {
        button.addEventListener('click', () => deleteDocument(doc.id, tr));
      } else if (button.dataset.action === 'view-analysis') {
        button.addEventListener('click', () => viewAnalysis(doc.id, fileName));
      }
    });

    return tr;
  };

  const deleteDocument = async (id, row) => {
    if (!confirm('Delete this document? This action cannot be undone.')) {
      return;
    }

    showStatus('Deleting...', 'info');

    const headers = typeof addCsrfHeader === 'function' ? addCsrfHeader({}) : {};

    const resp = await fetch(`${documentsEndpoint}${id}/`, {
      method: 'DELETE',
      headers,
      credentials: 'same-origin',
    });

    if (!resp.ok) {
      let detail = '';
      try {
        const json = await resp.json();
        if (json && json.detail) {
          detail = `: ${json.detail}`;
        }
        console.error('Delete document error response:', json);
      } catch (e) {
        // ignore parse errors
      }
      showStatus(`Failed to delete document (status ${resp.status})${detail}`, 'danger');
      return;
    }

    selectedIds.delete(String(id));
    updateDeleteSelectedButton();
    if (row && row.remove) row.remove();
    showStatus('Document deleted.', 'success');
  };

  const deleteSelectedDocuments = async () => {
    if (!selectedIds.size) return;

    if (!confirm('Delete all selected documents? This action cannot be undone.')) {
      return;
    }

    showStatus('Deleting...', 'info');

    const headers = typeof addCsrfHeader === 'function' ? addCsrfHeader({}) : {};

    const ids = Array.from(selectedIds);
    for (const id of ids) {
      const resp = await fetch(`${documentsEndpoint}${id}/`, {
        method: 'DELETE',
        headers,
        credentials: 'same-origin',
      });

      if (resp.ok) {
        selectedIds.delete(id);
      } else {
        let detail = '';
        try {
          const json = await resp.json();
          if (json && json.detail) {
            detail = `: ${json.detail}`;
          }
        } catch (e) {
          // ignore parse errors
        }
        showStatus(`Failed to delete document ${id} (status ${resp.status})${detail}`, 'danger');
      }
    }

    updateDeleteSelectedButton();
    loadDocuments();
    showStatus('Selected documents deleted.', 'success');
  };

  const buildPagination = () => {
    const container = document.getElementById('documents-pagination');
    if (!container) return;

    container.innerHTML = '';

    if (totalPages <= 1) {
      return;
    }

    const createButton = (label, page, disabled = false) => {
      const btn = document.createElement('button');
      btn.className = `px-3 py-2 rounded text-sm font-medium border ${disabled ? 'border-gray-200 text-gray-400 cursor-not-allowed bg-gray-50' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`;
      btn.type = 'button';
      btn.textContent = label;
      btn.disabled = disabled;
      if (!disabled) {
        btn.addEventListener('click', () => {
          currentPage = page;
          loadDocuments();
        });
      }
      return btn;
    };

    container.appendChild(createButton('«', 1, currentPage === 1));
    container.appendChild(createButton('‹', Math.max(1, currentPage - 1), currentPage === 1));

    const pageInfo = document.createElement('span');
    pageInfo.className = 'mx-2 text-gray-600 text-sm';
    pageInfo.textContent = `Page ${currentPage} / ${totalPages}`;
    container.appendChild(pageInfo);

    container.appendChild(createButton('›', Math.min(totalPages, currentPage + 1), currentPage === totalPages));
    container.appendChild(createButton('»', totalPages, currentPage === totalPages));
  };

  const loadDocuments = async () => {
    const tbody = document.querySelector('#documents-tbody');
    if (!tbody) return;

    // Reset selection on new load
    selectedIds.clear();
    updateDeleteSelectedButton();

    tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500"><i class="fa-solid fa-spinner fa-spin me-2"></i>Loading...</td></tr>';

    const params = new URLSearchParams();
    if (selectedStandard) params.set('standard', selectedStandard);
    if (searchTerm) params.set('search', searchTerm);
    params.set('page', currentPage);
    params.set('page_size', pageSize);

    let data;
    try {
      const resp = await fetch(`${documentsEndpoint}?${params.toString()}`, {
        credentials: 'same-origin',
      });

      if (!resp.ok) {
      tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-red-600">Failed to load documents.</td></tr>';
        return;
      }

      data = await resp.json();
    } catch (err) {
      console.error('Failed to load documents:', err);
      tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-red-600">Error loading documents.</td></tr>';
      return;
    }

    const docs = Array.isArray(data) ? data : data.results || [];
    totalPages = (data && (data.total_pages || data.totalPages)) || 1;

    if (!docs.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No documents found.</td></tr>';
      buildPagination();
      return;
    }

    tbody.innerHTML = '';
    docs.forEach((doc) => {
      const row = buildRow(doc);
      tbody.appendChild(row);
    });

    buildPagination();
    updateSelectAllCheckbox();
    updateDeleteSelectedButton();
    showStatus(`Showing ${docs.length} document(s).`, 'success');
  };

  const loadStandards = async () => {
    const select = document.getElementById('filter-standard');
    if (!select) return;

    // Ensure default option is always present
    select.innerHTML = `<option value="">${i18n.t('documents.all_standards')}</option>`;

    try {
      const resp = await fetch(standardsEndpoint, { credentials: 'same-origin' });
      if (!resp.ok) {
        throw new Error(`Status ${resp.status}`);
      }

      const standards = await resp.json();
      if (!Array.isArray(standards) || !standards.length) return;

      standards.forEach((standard) => {
        const opt = document.createElement('option');
        opt.value = standard.id;
        opt.textContent = standard.name;
        select.appendChild(opt);
      });
    } catch (err) {
      console.error('Failed to load standards:', err);
      const errorOpt = document.createElement('option');
      errorOpt.value = '';
      errorOpt.textContent = 'Failed to load standards';
      errorOpt.disabled = true;
      select.appendChild(errorOpt);
      showStatus('Unable to load standards list.', 'warning');
    }
  };

  const applyFilters = () => {
    const select = document.getElementById('filter-standard');
    const searchInput = document.getElementById('filter-search');

    selectedStandard = select ? select.value : '';
    searchTerm = searchInput ? searchInput.value.trim() : '';
    currentPage = 1;

    loadDocuments();
  };

  function initDocuments() {
    const applyBtn = document.getElementById('filter-apply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyFilters);
    }

    const searchInput = document.getElementById('filter-search');
    if (searchInput) {
      searchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
          applyFilters();
        }
      });
    }

    const deleteSelectedBtn = document.getElementById('delete-selected');
    if (deleteSelectedBtn) {
      deleteSelectedBtn.addEventListener('click', deleteSelectedDocuments);
    }

    const selectAllCheckbox = document.getElementById('select-all-documents');
    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', () => {
        const checkboxes = document.querySelectorAll('.document-checkbox');
        checkboxes.forEach((cb) => {
          cb.checked = selectAllCheckbox.checked;
          const id = cb.getAttribute('data-doc-id');
          if (selectAllCheckbox.checked) {
            selectedIds.add(String(id));
          } else {
            selectedIds.delete(String(id));
          }
        });
        updateDeleteSelectedButton();
        updateSelectAllCheckbox();
      });
    }

    // Modal closing
    const modal = document.getElementById('analysis-modal');
    if (modal) {
      const closeBtn = modal.querySelector('button[type="button"]');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => {
          modal.style.display = 'none';
        });
      }
      
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.style.display = 'none';
        }
      });
    }

    loadStandards();
    loadDocuments();
  }

  const viewAnalysis = async (docId, docName) => {
    const modal = document.getElementById('analysis-modal');
    if (!modal) {
      console.error('Analysis modal not found');
      return;
    }

    // Show modal
    modal.style.display = 'flex';

    // Set document name
    const docNameElement = document.getElementById('analysis-doc-name');
    if (docNameElement) {
      docNameElement.textContent = `Document: ${docName}`;
    }

    // Set loading state
    const content = document.getElementById('analysis-content');
    if (content) {
      content.innerHTML = '<div class="text-center text-gray-500"><i class="fa-solid fa-spinner fa-spin me-2"></i>Loading analysis...</div>';
    }

    try {
      const resp = await fetch(`/api/compliance/results/?document_id=${docId}`, {
        credentials: 'same-origin',
      });

      if (!resp.ok) {
        if (content) {
          content.innerHTML = '<div class="p-4 bg-red-50 text-red-800 rounded-lg">Failed to load analysis.</div>';
        }
        return;
      }

      const data = await resp.json();
      const results = Array.isArray(data) ? data : data.results || [];

      if (!results.length) {
        if (content) {
          content.innerHTML = '<div class="p-4 bg-blue-50 text-blue-800 rounded-lg">No analysis available for this document. Execute an audit to generate analysis.</div>';
        }
        return;
      }

      // Display first result (most recent)
      const result = results[0];
      const analysisHtml = formatAnalysisResult(result);
      if (content) {
        content.innerHTML = analysisHtml;
      }
    } catch (err) {
      console.error('Failed to load analysis:', err);
      if (content) {
        content.innerHTML = '<div class="p-4 bg-red-50 text-red-800 rounded-lg">Error loading analysis.</div>';
      }
    }
  };

  const formatAnalysisResult = (result) => {
    const score = result.score || 0;
    const status = result.status || 'unknown';
    const violations = result.violations || {};
    const risks = result.risks || [];
    const recommendations = result.recommendations || [];
    const missing_controls = result.missing_controls || [];

    let statusBadgeClass = 'bg-gray-100 text-gray-800';
    let statusText = 'Unknown';
    let statusColor = 'gray';
    
    if (status === 'compliant') {
      statusBadgeClass = 'bg-green-100 text-green-800';
      statusText = 'Compliant';
      statusColor = 'green';
    } else if (status === 'partially_compliant') {
      statusBadgeClass = 'bg-yellow-100 text-yellow-800';
      statusText = 'Partially Compliant';
      statusColor = 'yellow';
    } else if (status === 'non_compliant') {
      statusBadgeClass = 'bg-red-100 text-red-800';
      statusText = 'Non-Compliant';
      statusColor = 'red';
    }

    let html = `
      <div class="space-y-6">
        <!-- Summary Section -->
        <div class="border-b border-gray-200 pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Summary</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-600 mb-1">Score</p>
              <p class="text-3xl font-bold text-gray-900">${score}<span class="text-lg">/100</span></p>
              <p class="text-xs text-gray-500 mt-1">Compliance Score</p>
            </div>
            <div>
              <p class="text-sm text-gray-600 mb-1">Status</p>
              <span class="inline-block px-3 py-1 rounded-lg text-sm font-medium ${statusBadgeClass}">${statusText}</span>
            </div>
          </div>
        </div>
    `;

    // Violations
    if (violations && Object.keys(violations).length > 0) {
      html += `
        <div class="border-b border-gray-200 pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Detected Violations</h4>
          <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <p class="text-sm mb-2"><strong class="text-red-900">Total Violations:</strong> <span class="text-red-700 font-semibold">${violations.violation_count || 0}</span></p>
            <p class="text-sm text-red-700"><strong>Critical Violations:</strong> <span class="font-semibold">${violations.critical_violation_count || 0}</span></p>
      `;
      
      if (violations.violation_patterns && Array.isArray(violations.violation_patterns)) {
        html += '<div class="mt-3 space-y-2">';
        violations.violation_patterns.forEach(v => {
          html += `<div class="text-sm"><strong class="text-red-700">${v.type}:</strong> <span class="text-red-600">${v.description}</span></div>`;
        });
        html += '</div>';
      }
      
      html += '</div></div>';
    }

    // Missing Controls
    if (missing_controls && Array.isArray(missing_controls) && missing_controls.length > 0) {
      html += `
        <div class="border-b border-gray-200 pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Missing Controls</h4>
          <div class="space-y-2">
      `;
      missing_controls.forEach(control => {
        html += `<div class="px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-900"><i class="fa-solid fa-exclamation-circle me-2 text-yellow-600"></i>${control}</div>`;
      });
      html += '</div></div>';
    }

    // Risks
    if (risks && Array.isArray(risks) && risks.length > 0) {
      html += `
        <div class="border-b border-gray-200 pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Identified Risks</h4>
          <div class="space-y-3">
      `;
      risks.forEach(risk => {
        const riskLevel = risk.level || risk.severity || 'medium';
        let riskClass = 'bg-blue-50 border-blue-200 text-blue-900';
        let riskIcon = 'fa-info-circle text-blue-600';
        
        if (riskLevel === 'critical') {
          riskClass = 'bg-red-50 border-red-200 text-red-900';
          riskIcon = 'fa-exclamation-triangle text-red-600';
        } else if (riskLevel === 'high') {
          riskClass = 'bg-orange-50 border-orange-200 text-orange-900';
          riskIcon = 'fa-warning text-orange-600';
        }
        
        html += `
          <div class="p-4 border ${riskClass} rounded-lg">
            <div class="flex items-start gap-3">
              <i class="fa-solid ${riskIcon} mt-1"></i>
              <div class="flex-1">
                <h5 class="font-semibold">${risk.title || risk.name || 'Risk'}</h5>
                <p class="text-sm mt-1 opacity-90">${risk.description || ''}</p>
              </div>
            </div>
          </div>
        `;
      });
      html += '</div></div>';
    }

    // Recommendations
    if (recommendations && Array.isArray(recommendations) && recommendations.length > 0) {
      html += `
        <div>
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Recommendations</h4>
          <div class="space-y-3">
      `;
      recommendations.forEach(rec => {
        html += `
          <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h5 class="font-semibold text-green-900">${rec.title || rec.action || 'Recommendation'}</h5>
            <p class="text-sm text-green-800 mt-1">${rec.description || ''}</p>
            ${rec.priority ? `<p class="text-xs text-green-600 mt-2"><strong>Priority:</strong> ${rec.priority}</p>` : ''}
          </div>
        `;
      });
      html += '</div></div>';
    }

    html += '</div>';

    return html || '<div class="p-4 bg-blue-50 text-blue-800 rounded-lg">No analysis data available.</div>';
  };

  window.initDocuments = initDocuments;
  window.viewAnalysis = viewAnalysis;
})();
